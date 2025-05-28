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
        st.session_state.users = listar_usuarios()
    st.rerun()

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
    
    pg = st.navigation([
        st.Page(render_produtos, title="Produtos", icon="👤"),
        st.Page(render_pedidos, title="Pedidos", icon="🛠️"),
        st.Page(pagina_configuracoes, title="Configurações", icon="⚙️")
    ])
    pg.run()
def render_produtos():
    """Tela de gerenciamento de produtos"""
    st.header("📦 Gerenciamento de Produtos")
    produtos = st.session_state.produtos
    users = st.session_state.users
    pedidos = st.session_state.pedidos

    if st.button("Atualizar", key = 'asfweaf', ):
        att_data(pedidos=True, produtos=True, users=True)

    
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

    if st.button("Atualizar", type="primary", key="atualizar_pedidos"):
        att_data(pedidos=True, produtos=True, users=True)
    
    tab1, tab2, tab3 = st.tabs(["Lista de Pedidos", "Criar Pedido", "Relatórios"])
    
    with tab1:
        st.subheader("Pedidos Recentes")
    
        df_pedidos = pd.DataFrame([{
            "id": p.id,
            "usuario_id": p.usuario_id,
            "email": [u[1] for u in users if u[0] == p.usuario_id],
            "data": p.data.strftime('%Y-%m-%d %H:%M'),
            "status": p.status,
            "valor": float(p.total),
            "itens": len(p.itens)
        } for p in pedidos])

        if df_pedidos.empty:
            st.warning("Nenhum pedido encontrado.")
        else:
            # Filtros
            col1, col2, col3 = st.columns(3)
            with col1:
                filtro_status = st.selectbox("Status", ["Todos", "Pendente", "Aprovado", "Cancelado"])
            with col2:
                data_inicio = st.date_input("Data Início", date(2024, 5, 1))
            with col3:
                data_fim = st.date_input("Data Fim", date.today())
            
            # Aplicar filtros
            df_filtrado = df_pedidos.copy()
            if filtro_status != "Todos":
                df_filtrado = df_filtrado[df_filtrado['status'] == filtro_status]
            df_filtrado['data'] = pd.to_datetime(df_filtrado['data'])
            df_filtrado = df_filtrado[
                (df_filtrado['data'].dt.date >= data_inicio) & 
                (df_filtrado['data'].dt.date <= data_fim)
            ]
            
            # Colorir status

            
            st.dataframe(df_filtrado, use_container_width=True, column_config={
                "id": "ID",
                "email": "Email do Usuário",
                "data": "Data",
                "status": "Status",
                "valor": st.column_config.NumberColumn("Valor (R$)", format="%.2f"),
                "itens": "Nº de Itens"
            })
            
            # Visualizar detalhes do pedido
            st.subheader("Detalhes do Pedido")
            pedido_id = st.selectbox("Selecione um pedido", df_filtrado["id"])
            if st.button("🔍 Visualizar Itens"):
                pedido = next((p for p in pedidos if p.id == pedido_id), None)
                if pedido:
                    st.write(f"**Detalhes do Pedido ID {pedido_id}**")
                    st.write(f"**Usuário:** {[u[1] for u in users if u[0] == pedido.usuario_id]}")
                    st.write(f"**Data:** {pedido.data.strftime('%Y-%m-%d %H:%M')}")
                    st.write(f"**Status:** {pedido.status}")
                    st.write(f"**Total:** R${pedido.total:.2f}")
                    
                    # Exibir itens
                    if pedido.itens:
                        df_itens = pd.DataFrame([{
                            "Produto": [p.nome for p in produtos if p.id == item.produto_id],
                            "Quantidade": item.quantidade,
                            "Preço Unitário": float(item.preco_unitario),
                            "Subtotal": float(item.quantidade * item.preco_unitario)
                        } for item in pedido.itens])
                        st.dataframe(df_itens, use_container_width=True, column_config={
                            "Produto": "Produto",
                            "Quantidade": "Quantidade",
                            "Preço Unitário": st.column_config.NumberColumn("Preço Unitário (R$)", format="%.2f"),
                            "Subtotal": st.column_config.NumberColumn("Subtotal (R$)", format="%.2f")
                        })
                    else:
                        st.warning("Nenhum item encontrado para este pedido.")
                else:
                    st.error(f"Pedido ID {pedido_id} não encontrado.")
            st.write("---")
            # Ações rápidas
            st.subheader("Ações Rápidas")
            col1, col2, col3 = st.columns(3)
            with col1:
                pedido_id_excluir = st.number_input("ID do Pedido para Excluir", min_value=1, step=1)
                if st.button("🗑️ Excluir Pedido"):
                    if excluir_pedido(pedido_id_excluir):
                        time.sleep(2)
                        st.success(f"Pedido ID {pedido_id_excluir} excluído com sucesso!")
                        att_data(pedidos=True)
                    else:
                        st.error(f"Pedido ID {pedido_id_excluir} não encontrado.")
    
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