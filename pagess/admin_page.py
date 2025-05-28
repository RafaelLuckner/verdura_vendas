from narwhals import col
import streamlit as st
import pandas as pd
from datetime import datetime, date
import plotly.express as px
from app.crud import adicionar_produto, listar_produtos, atualizar_produto, excluir_produto, criar_pedido, listar_pedidos, atualizar_status_pedido, excluir_pedido, listar_usuarios
from app.crud import get_user_by_id, get_produto_by_id
from app.auth import atualizar_username_usuario
from app.models import ProdutoCreate, PedidoCreate, ItemPedidoCreate
from typing import List
import time

def att_data(pedidos= False, produtos= False, users=False):
    if pedidos:
        st.session_state.pedidos = listar_pedidos()
    if produtos:
        st.session_state.produtos = listar_produtos()
    if users:
        st.session_state.users = listar_usuarios(email= False, nome= True)

def render():
    """Renderiza a página do administrador baseada na opção do menu"""
    # st.title("🔧 Painel Administrativo")
    # Listar pedidos
    if 'pedidos' not in st.session_state:
        st.session_state.pedidos = listar_pedidos()

    # Listar users
    if 'users' not in st.session_state:
        st.session_state.users = listar_usuarios()

    # Listar produtos
    if 'produtos' not in st.session_state:
        st.session_state.produtos = listar_produtos()
    
    with st.sidebar:
        st.button("Atualizar Dados", on_click=att_data, args=(True, True, True), use_container_width=True)

    pg = st.navigation([
        st.Page(render_produtos, title="Produtos", icon="🥬",),
        st.Page(render_pedidos, title="Pedidos", icon="📦"),
        st.Page(pagina_configuracoes, title="Configurações", icon="⚙️")
    ])
    pg.run()
def render_produtos():
    """Tela de gerenciamento de produtos"""
    st.header("📦 Gerenciamento de Produtos")
    produtos = st.session_state.produtos
    users = st.session_state.users
    pedidos = st.session_state.pedidos
    
    tab1, tab2, tab3 = st.tabs(["Lista de Produtos", "Adicionar Produto", "Relatórios"])
    
    with tab1:
        st.subheader("Produtos Cadastrados")


        df_produtos = pd.DataFrame([{
            "id": p.id,
            "nome": p.nome,
            "preco": float(p.preco),
            "unidade": p.unidade,
            "ativo": "Ativo" if p.ativo else "Inativo"
        } for p in st.session_state.produtos])
        
        if df_produtos.empty:
            st.warning("Nenhum produto cadastrado.")
        else:
            # Filtros
            col1, col2, col3 = st.columns(3)
            with col1:
                filtro_unidade = st.selectbox("Filtrar por Unidade", 
                                            ["Todas"] + list(df_produtos['unidade'].unique()))
            with col2:
                filtro_status = st.selectbox("Filtrar por Status", 
                                        ["Todos", "Ativo", "Inativo"])
            with col3:
                buscar_nome = st.text_input("Buscar por nome")
            
            # Aplicar filtros
            df_filtrado = df_produtos.copy()
            if filtro_unidade != "Todas":
                df_filtrado = df_filtrado[df_filtrado['unidade'] == filtro_unidade]
            if filtro_status != "Todos":
                df_filtrado = df_filtrado[df_filtrado['ativo'] == filtro_status]
            if buscar_nome:
                df_filtrado = df_filtrado[df_filtrado['nome'].str.contains(buscar_nome, case=False)]
            
            # Exibir tabela editável
            edited_df = st.data_editor(
                df_filtrado,
                key="produtos_editor",
                num_rows="fixed",
                use_container_width=True,
                column_config={
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "nome": st.column_config.TextColumn("Nome"),
                    "preco": st.column_config.NumberColumn("Preço (R$)", format="%.2f"),
                    "unidade": st.column_config.SelectboxColumn("Unidade", options=["Unidade", "Caixa"]),
                    "ativo": st.column_config.SelectboxColumn("Status", options=["Ativo", "Inativo"])
                }
            )

            # 
            
            # Salvar edições
            if st.button("💾 Salvar Alterações"):
                for idx, row in edited_df.iterrows():
                    produto = ProdutoCreate(
                        nome=row['nome'],
                        preco=row['preco'],
                        unidade=row['unidade'],
                        ativo=row['ativo'] == "Ativo"
                    )
                    if atualizar_produto(int(row['id']), produto):
                        st.success(f"Produto {row['nome']} atualizado com sucesso!")

            # Ações em lote
            st.write('---')
            st.subheader("Exluir Produto")
            col1, col2, col3 = st.columns(3)
            with col1:
                produto_id = st.number_input("ID do Produto para Excluir", min_value=1, step=1)
                if st.button("🗑️ Excluir Produto"):
                    if excluir_produto(produto_id):
                        st.success(f"Produto ID {produto_id} excluído com sucesso!")
                        st.rerun()
                    else:
                        st.error(f"Produto ID {produto_id} não encontrado.")

    
    with tab2:
        st.subheader("Adicionar Novo Produto")
        
        with st.form("novo_produto"):
            col1, col2 = st.columns(2)
            
            with col1:
                nome = st.text_input("Nome do Produto*")
                preco = st.number_input("Preço (R$)*", min_value=0.01, format="%.2f")
            
            with col2:
                unidade = st.selectbox('Unidade ou Caixa', ["Caixa","Unidade"])
                ativo = st.selectbox("Status", ["Ativo", "Inativo"])
            
            submitted = st.form_submit_button("Adicionar Produto")
            
            if submitted:
                if nome and preco > 0 and unidade:
                    produto = ProdutoCreate(
                        nome=nome,
                        preco=preco,
                        unidade=unidade,
                        ativo= ativo == "Ativo"
                    )
                    produto_id = adicionar_produto(produto)
                    st.success(f"Produto '{nome}' adicionado com ID {produto_id}!")
                    time.sleep(3)
                    att_data(produtos=True)
                else:
                    st.error("Preencha todos os campos obrigatórios.")
    
    with tab3:
        st.subheader("Relatórios de Produtos")
        if df_produtos.empty:
            st.warning("Nenhum produto cadastrado.")
        else:
        
            df_produtos = pd.DataFrame([{
                "id": p.id,
                "nome": p.nome,
                "preco": float(p.preco),
                "unidade": p.unidade,
                "ativo": p.ativo
            } for p in produtos])
            
            # Métricas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Produtos", len(df_produtos))
            with col2:
                produtos_ativos = len(df_produtos[df_produtos['ativo'] == True])
                st.metric("Produtos Ativos", produtos_ativos)
            with col3:
                valor_total = df_produtos['preco'].sum()
                st.metric("Valor Total", f"R$ {valor_total:,.2f}")
            
            # Gráficos
            col1, col2 = st.columns(2)
            
            with col1:
                fig_unidade = px.pie(df_produtos, 
                                names='unidade', 
                                title='Produtos por Unidade')
                st.plotly_chart(fig_unidade, use_container_width=True)
            
            with col2:
                baixo_preco = df_produtos[df_produtos['preco'] < 100]
                fig_preco = px.bar(baixo_preco, 
                                x='nome', 
                                y='preco',
                                title='Produtos com Preço < R$100')
                st.plotly_chart(fig_preco, use_container_width=True)

def render_pedidos():

    """Tela de gerenciamento de pedidos"""
    st.header("📋 Gerenciamento de Pedidos")
    produtos = st.session_state.produtos
    users = st.session_state.users
    pedidos = st.session_state.pedidos

    tab1, tab2, tab3 = st.tabs(["📋 Lista de Pedidos", "➕ Criar Pedido", "📊 Relatórios"])


    with tab1:
        st.header("🛍️ Gestão de Pedidos")
        
        # Função auxiliar para obter datas válidas (terça, quinta, sábado)
        def obter_datas_validas():
            """Retorna lista de datas dos últimos 30 dias que são terça, quinta ou sábado"""
            from datetime import datetime, timedelta
            
            datas_validas = []
            data_atual = datetime.now().date()
            
            for i in range(15):  # Últimos 30 dias
                data = data_atual + timedelta(days=i)
                dia_semana = data.weekday()  # 0=segunda, 1=terça, 2=quarta, 3=quinta, 4=sexta, 5=sábado, 6=domingo
                
                if dia_semana in [1, 3, 5]:  # terça=1, quinta=3, sábado=5
                    nome_dia = {1: "Terça", 3: "Quinta", 5: "Sábado"}[dia_semana]
                    datas_validas.append({
                        'data': data,
                        'label': f"{nome_dia}, {data.day:02d}/{data.month:02d}",
                        'dia_semana': nome_dia
                    })
            
            return sorted(datas_validas, key=lambda x: x['data'], reverse=False)

        # Preparar dados dos pedidos
        if pedidos:
            df_pedidos = pd.DataFrame([{
                "id": p.id,
                "usuario_id": p.usuario_id,
                "email": next((u[1] for u in users if u[0] == p.usuario_id), "N/A"),
                "data": p.data,
                "data_str": p.data.strftime('%d/%m/%Y'),
                "hora": p.data.strftime('%H:%M'),
                "status": p.status,
                "valor": float(p.total),
                "itens": len(p.itens)
            } for p in pedidos])
            
            # Adicionar coluna do dia da semana
            df_pedidos['dia_semana'] = df_pedidos['data'].dt.day_name().map({
                'Monday': 'Segunda', 'Tuesday': 'Terça', 'Wednesday': 'Quarta',
                'Thursday': 'Quinta', 'Friday': 'Sexta', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
            })
            
            # Filtrar apenas dias válidos (terça, quinta, sábado)
            df_pedidos = df_pedidos[df_pedidos['dia_semana'].isin(['Terça', 'Quinta', 'Sábado'])]
            
            if df_pedidos.empty:
                st.warning("📅 Nenhum pedido encontrado para os dias de funcionamento (Terças, Quintas e Sábados).")
            else:
                # === SEÇÃO DE FILTROS ===
                st.subheader("🔍 Filtros")
                
                col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
                
                with col1:
                    status_options = ["Todos"] + list(df_pedidos['status'].unique())
                    filtro_status = st.selectbox("📊 Status", status_options)

                with col2:
                    datas_validas = obter_datas_validas()
                    data_inicio_options = ["Todos"] + [d['label'] for d in datas_validas]
                    filtro_data_inicio = st.selectbox("Dia", data_inicio_options)
                
                # Aplicar filtros
                df_filtrado = df_pedidos.copy()
                
                if filtro_status != "Todos":
                    df_filtrado = df_filtrado[df_filtrado['status'] == filtro_status]
                
                if filtro_data_inicio != "Todos":
                    data_selecionada = next(d['data'] for d in datas_validas if d['label'] == filtro_data_inicio)
                    df_filtrado = df_filtrado[df_filtrado['data'].dt.date == data_selecionada]
                
                
                # === MÉTRICAS RÁPIDAS ===
                if not df_filtrado.empty:
       
                    with col3:
                        st.metric(
                            label="📝 Total de Pedidos",
                            value=len(df_filtrado),
                            delta=f"{len(df_filtrado) - len(df_pedidos)} vs. total" if len(df_filtrado) != len(df_pedidos) else None
                        )

                    
                    with col4:
                        pedidos_pendentes = len(df_filtrado[df_filtrado['status'] == 'Pendente'])
                        st.metric(
                            label="⏳ Pendentes",
                            value=pedidos_pendentes,
                        )
                
                st.divider()
                
                # === TABELA DE PEDIDOS ===
                st.subheader("📋 Lista de Pedidos")
                
                # Preparar dados para exibição
                df_display = df_filtrado.copy()
                df_display = df_display.sort_values('data', ascending=False)
                
                # Função para colorir status
                def colorir_status(status):
                    colors = {
                        'Pendente': '🟡',
                        'Aprovado': '🟢', 
                        'Cancelado': '🔴'
                    }
                    return f"{colors.get(status, '⚪')} {status}"
                
                df_display['status_icon'] = df_display['status'].apply(colorir_status)
                
                # Exibir tabela
                st.dataframe(
                    df_display[['id', 'dia_semana', 'data_str', 'email', 'status_icon', 'valor', 'itens']],
                    use_container_width=True,
                    column_config={
                        "id": st.column_config.NumberColumn("ID", width="small"),
                        "dia_semana": st.column_config.TextColumn("Dia", width="small"),
                        "data_str": st.column_config.TextColumn("Data", width="small"),
                        "hora": st.column_config.TextColumn("Hora", width="small"),
                        "email": st.column_config.TextColumn("Cliente", width="medium"),
                        "status_icon": st.column_config.TextColumn("Status", width="small"),
                        "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", width="medium"),
                        "itens": st.column_config.NumberColumn("Itens", width="small")
                    },
                    hide_index=True
                )
                
                # === DETALHES DO PEDIDO ===
                st.divider()
                st.subheader("🔍 Detalhes do Pedido")
                

                pedidos_ids = df_filtrado['id'].tolist()
                pedido_selecionado = st.selectbox(
                    "Selecione um pedido para visualizar detalhes",
                    pedidos_ids,
                    format_func=lambda x: f"Pedido #{x} - {df_filtrado[df_filtrado['id']==x]['email'].iloc[0]}"
                )

                if  pedido_selecionado:
                    pedido = next((p for p in pedidos if p.id == pedido_selecionado), None)
                    
                    if pedido:
                        # Card com informações do pedido
                        with st.container():
                            st.markdown(f"""
                            <div style="background-color:  padding: 20px; border-radius: 10px; margin: 10px 0;">
                                <h4>🛍️ Pedido #{pedido.id}</h4>
                                <p><strong>👤 Cliente:</strong> {next((u[1] for u in users if u[0] == pedido.usuario_id), 'N/A')}</p>
                                <p><strong>📅 Data:</strong> {pedido.data.strftime('%d/%m/%Y ')}</p>
                                <p><strong>📊 Status:</strong> {colorir_status(pedido.status)}</p>
                                <p><strong>💰 Total:</strong> R$ {pedido.total:.2f}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Itens do pedido
                        if pedido.itens:
                            st.write("**📦 Itens do Pedido:**")
                            
                            df_itens = pd.DataFrame([{
                                "Produto": next((p.nome for p in produtos if p.id == item.produto_id), f"Produto ID {item.produto_id}"),
                                "Quantidade": item.quantidade,
                                "Preço Unitário": float(item.preco_unitario),
                                "Subtotal": float(item.quantidade * item.preco_unitario)
                            } for item in pedido.itens])
                            
                            st.dataframe(
                                df_itens,
                                use_container_width=True,
                                column_config={
                                    "Produto": st.column_config.TextColumn("🛍️ Produto", width="small"),
                                    "Quantidade": st.column_config.NumberColumn("📊 Qtd", width="small"),
                                    "Preço Unitário": st.column_config.NumberColumn("💰 Preço Unit.", format="R$ %.2f"),
                                    "Subtotal": st.column_config.NumberColumn("💰 Subtotal", format="R$ %.2f")
                                },
                                hide_index=True
                            )
                        else:
                            st.warning("📦 Nenhum item encontrado para este pedido.")
                    else:
                        st.error(f"❌ Pedido #{pedido_selecionado} não encontrado.")
                
                # Botões em linha única para melhor visualização mobile
                col1, col2 = st.columns(2)

                if not 'editar_excluir_pedido' in st.session_state:
                    st.session_state.editar_excluir_pedido = None
                if st.session_state.editar_excluir_pedido == None:
                    
                    with col1:
                        if st.button("📝 Editar Status", use_container_width=True, type="primary"):
                            st.session_state.editar_excluir_pedido = 'Editar'
                            st.rerun()

                    with col2:
                        if st.button("🗑️ Excluir Pedido", use_container_width=True, type="secondary"):
                            st.session_state.editar_excluir_pedido = 'Excluir'
                            st.rerun()

                # === SEÇÃO DE EDIÇÃO DE STATUS ===
                if st.session_state.editar_excluir_pedido == 'Editar':
                    st.write("**📝 Alterar Status do Pedido**")
                    
                    # Botões de status em formato de grid 2x2 (melhor para mobile)
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("✅ Aprovar", 
                                    use_container_width=True, 
                                    type="primary",
                                    help="Marcar pedido como aprovado"):
                            atualizar_status_pedido(pedido_selecionado, "Aprovado")
                            st.session_state.editar_excluir_pedido = None
                            st.success("Status atualizado para Aprovado!")
                            time.sleep(1)
                            st.rerun()
                    
                    with col2:
                        if st.button("❌ Cancelar", 
                                    use_container_width=True, 
                                    type="secondary",
                                    help="Marcar pedido como cancelado"):
                            atualizar_status_pedido(pedido_selecionado, "Cancelado")
                            st.session_state.editar_excluir_pedido = None
                            st.success("Status atualizado para Cancelado!")
                            time.sleep(1)
                            st.rerun()
                    
                    # Segunda linha de botões
                    col3, col4 = st.columns(2)
                    
                    with col3:
                        if st.button("⏳ Pendente", 
                                    use_container_width=True,
                                    help="Marcar pedido como pendente"):
                            atualizar_status_pedido(pedido_selecionado, "Pendente")
                            st.session_state.editar_excluir_pedido = None
                            st.success("Status atualizado para Pendente!")
                            time.sleep(1)
                            st.rerun()
                    
                    with col4:
                        if st.button("↩️ Voltar", 
                                    use_container_width=True):
                            st.session_state.editar_excluir_pedido = None
                            st.rerun()

                # === SEÇÃO DE EXCLUSÃO ===
                elif st.session_state.editar_excluir_pedido == 'Excluir':
                    st.warning("⚠️ **Confirmar Exclusão do Pedido**")
                    st.write(f"Você tem certeza que deseja excluir o pedido #{pedido_selecionado}?")
                    st.write("⚠️ **Esta ação não pode ser desfeita!**")
                    
                    # Botões de confirmação em linha
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("🗑️ Confirmar Exclusão", 
                                    use_container_width=True, 
                                    type="primary"):
                            if excluir_pedido(pedido_selecionado):
                                st.success(f"✅ Pedido #{pedido_selecionado} excluído com sucesso!")
                                st.session_state.editar_excluir_pedido = None
                                time.sleep(2)
                                att_data(pedidos=True)
                                st.rerun()
                            else:
                                st.error(f"❌ Erro ao excluir pedido #{pedido_selecionado}")
                    
                    with col2:
                        if st.button("↩️ Cancelar", 
                                    use_container_width=True, 
                                    type="secondary"):
                            st.session_state.editar_excluir_pedido = None
                            st.rerun()

        
        else:
            st.info("📝 Nenhum pedido cadastrado ainda. Use a aba 'Criar Pedido' para adicionar o primeiro pedido.")
    
    with tab2:
        st.subheader("Criar Novo Pedido")
        df_usuarios = pd.DataFrame(st.session_state.users, columns=['id', 'email'])
        usuario_id = st.selectbox("Email do Usuário", options=[u for u in df_usuarios['email']])
        usuario_id = df_usuarios[df_usuarios['email'] == usuario_id]['id'].values[0]
        status = st.selectbox("Status Inicial", ["Pendente", "Aprovado"])

        produtos_options = {f"{p.nome} - R${p.preco:.2f}": p for p in produtos}

        # Usa session_state para controlar número de itens dinamicamente
        if "num_itens" not in st.session_state:
            st.session_state.num_itens = 1

        itens = []
        for i in range(st.session_state.num_itens):
            st.write("---")
            col1, col2, col3 = st.columns(3)
            with col1:
                produto_key = st.selectbox(
                    f"\n Produto {i+1}",
                    options=list(produtos_options.keys()),
                    key=f"produto_{i}"
                )
                produto = produtos_options[produto_key]

            with col2:
                quantidade = st.number_input(
                    f"Quantidade",
                    min_value=1,
                    step=1,
                    key=f"quantidade_{i}"
                )
            from datetime import datetime, timedelta
            with col3:
                pass

                

            itens.append(ItemPedidoCreate(produto_id=produto.id,
                                         quantidade=quantidade,
                                         preco_unitario=produto.preco))

        st.write("")
        st.write("")
        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Adicionar Item", use_container_width=True):
                    st.session_state.num_itens += 1
                    st.rerun()

            with col2:
                if st.button("Remover Item", use_container_width=True):
                    if st.session_state.num_itens > 1:
                        st.session_state.num_itens -= 1
                        st.rerun()
        

        total = sum(item.quantidade * item.preco_unitario for item in itens)
        col1, col2 = st.columns(2)
        with col1:
            dias_semana_pt = {
                1: 'Terça-feira',
                3: 'Quinta-feira',
                5: 'Sábado',
            }

            # Gera próximas 60 datas, apenas terça, quinta e sábado
            hoje = datetime.today().date()
            datas_validas = [
                hoje + timedelta(days=i)
                for i in range(30)
                if (hoje + timedelta(days=i)).weekday() in [1, 3, 5]
            ]

            # Lista formatada com o dia da semana
            datas_formatadas = [
                f"{dias_semana_pt[data.weekday()]} - {data.strftime('%d/%m/%Y')}"
                for data in datas_validas
            ]

            # Cria um dicionário para mapear texto formatado de volta para o objeto date
            data_map = dict(zip(datas_formatadas, datas_validas))

            # Selectbox com datas formatadas
            data_selecionada_str = st.selectbox(
                "Dia (Terça, Quinta ou Sábado):",
                datas_formatadas,
                key=f"data_entrega_{i}"
            )

                # Recupera a data real selecionada
            dia_entrega = data_map[data_selecionada_str]
            st.write(f"Data Selecionada: {dia_entrega}")
            st.subheader(f"**Total: R${total:.2f}**")
        st.write("---")

        # Botão para criar pedido
        if st.button("Criar Pedido"):
            if not usuario_id:
                st.error("Selecione um usuário.")
            elif not itens:
                st.error("Adicione pelo menos um item ao pedido.")
            else:
                pedido = PedidoCreate(
                    data=dia_entrega,
                    status=status,
                    total=total,  # Passa o total calculado para maior clareza
                    usuario_id=usuario_id,
                    itens=itens
                )
                try:
                    pedido_id = criar_pedido(pedido)
                    st.success(f"Pedido #{pedido_id} criado com sucesso!")
                    # Reseta o formulário
                    st.session_state.num_itens = 1
                except ValueError as e:
                    st.error(str(e))
    
    with tab3:
        st.subheader("Relatórios de Vendas")
        pedidos = st.session_state.pedidos
        df_pedidos = pd.DataFrame([{
            "id": p.id,
            "usuario_id": p.usuario_id,
            "data": p.data,
            "status": p.status,
            "valor": float(p.total)
        } for p in pedidos])
        if df_pedidos.empty:
            st.warning("Nenhum pedido encontrado.")
            return
        else:
            # Métricas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Pedidos", len(df_pedidos))
            with col2:
                receita_total = df_pedidos['valor'].sum()
                st.metric("Receita Total", f"R$ {receita_total:,.2f}")
            with col3:
                ticket_medio = df_pedidos['valor'].mean() if len(df_pedidos) > 0 else 0
                st.metric("Ticket Médio", f"R$ {ticket_medio:.2f}")
            
            # Gráficos
            col1, col2 = st.columns(2)
            
            with col1:
                status_count = df_pedidos['status'].value_counts()
                fig_status = px.pie(values=status_count.values, 
                                names=status_count.index,
                                title='Distribuição por Status')
                st.plotly_chart(fig_status, use_container_width=True)
            
            with col2:
                df_pedidos['data'] = pd.to_datetime(df_pedidos['data'])
                vendas_dia = df_pedidos.groupby(df_pedidos['data'].dt.date)['valor'].sum().reset_index()
                fig_vendas = px.bar(
                    vendas_dia,
                    x='data',
                    y='valor',
                    title='Vendas por Dia'
                )
                st.plotly_chart(fig_vendas, use_container_width=True)

def pagina_configuracoes():
    st.header("⚙️ Configurações da Conta")

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Email:** {st.session_state.email}")
        st.write(f"**Username:** {st.session_state.username}")

    with col2:
        if "mostrar_input_username" not in st.session_state:
            st.session_state.mostrar_input_username = False

        if st.button("Alterar Nome", key="alterar_username2"):
            st.session_state.mostrar_input_username = True

        if st.session_state.mostrar_input_username:
            novo_username = st.text_input(
                "Nome de usuário",
                key="novo_username_input",
                placeholder="Digite seu nome de usuário (3-20 caracteres)",
                help="Apenas letras, números, _ e - são permitidos"
            )

            if novo_username and novo_username != st.session_state.username:
                if st.button("✅ Confirmar", key="confirmar_username"):
                    if atualizar_username_usuario(st.session_state['email'], novo_username):
                        st.success("Username atualizado com sucesso!")
                        st.session_state.username = novo_username
                        st.session_state.mostrar_input_username = False
                    else:
                        st.error("Este nome já está em uso ou ocorreu um erro.")
            elif novo_username == st.session_state.username:
                st.info("O novo username é igual ao atual.")