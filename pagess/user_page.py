from narwhals import col
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from app.crud import listar_produtos, criar_pedido, listar_pedidos, excluir_pedido, get_user_by_email, get_pedidos_by_user
from app.models import PedidoCreate, ItemPedidoCreate
import time
from itertools import zip_longest
from streamlit_elements import elements, mui, html

from app.auth import atualizar_username_usuario

def validar_username(username):
    """Valida se o username é válido"""
    if not username or len(username) < 3:
        st.error("Nome de usuário deve ter pelo menos 3 caracteres.")
        return False
    if len(username) > 20:
        st.error("Nome de usuário deve ter no máximo 20 caracteres.")
        return False

    return True
def att_data( produtos=False, pedidos_by_user=False):
    """Atualiza os dados na sessão"""

    if produtos:
        st.session_state.produtos = listar_produtos()

    if pedidos_by_user:
        st.session_state.pedidos_by_user = get_pedidos_by_user(st.session_state.user_id)
    st.rerun()

def render():
    if 'user_id' not in st.session_state:
        st.session_state.user_id = get_user_by_email(st.session_state.email)
    user_id = st.session_state.user_id

    
    if 'produtos' not in st.session_state:
        st.session_state.produtos = listar_produtos()
    if 'pedidos_by_user' not in st.session_state:
        st.session_state.pedidos_by_user = get_pedidos_by_user(st.session_state.user_id)
    
    pg = st.navigation([
        st.Page(render_pedidos, title="Pedidos", icon="🛠️"),
        st.Page(pagina_configuracoes, title="Configurações", icon="⚙️")
    ])
    pg.run()

def render_pedidos():
    # Abas principais
    tab1, tab2 = st.tabs(["🆕 Novo Pedido", "📋 Meus Pedidos"])
    
    with tab1:
        render_novo_pedido()
    
    with tab2:
        render_meus_pedidos()

def render_novo_pedido():
    """Renderiza a aba de criar novo pedido"""
    st.header("🛒 Novo Pedido")

    produtos = st.session_state.produtos
    produtos_ativos = [p for p in produtos if p.ativo]

    if not produtos_ativos:
        st.warning("Nenhum produto disponível no momento. Volte mais tarde!")
        return

    # Inicializar carrinho se ainda não existir
    if 'carrinho' not in st.session_state:
        st.session_state.carrinho = {}
    
    # Inicializar estado de confirmação
    if 'mostrar_confirmacao' not in st.session_state:
        st.session_state.mostrar_confirmacao = False

    # Campo de pesquisa
    termo_pesquisa = st.text_input("🔍 Pesquisar produto", placeholder="Digite o nome do produto...").strip().lower()

    # Filtrar produtos pelo termo de pesquisa
    produtos_filtrados = [
        p for p in produtos_ativos
        if termo_pesquisa in p.nome.lower()
    ] if termo_pesquisa else produtos_ativos

    if not produtos_filtrados:
        st.info("Nenhum produto encontrado com esse nome.")
        st.stop()

    st.markdown("Ajuste a quantidade desejada e veja o valor atualizado em tempo real.")

    # Agrupar produtos de dois em dois
    for prod1, prod2 in zip_longest(*[iter(produtos_filtrados)]*2):
        col1, col2 = st.columns(2)

        for produto, col in zip([prod1, prod2], [col1, col2]):
            if produto is None:
                continue

            with col:
                with st.container(border=True, height=270, key=f"produto_{produto.id}"):
                    name_img = f"{produto.nome.replace(' ', '_').lower()}"
                    with elements(f"produto_{produto.id}"):
                        mui.Box(
                            sx={
                                "display": "flex",
                                "flexDirection": "row",
                                "alignItems": "center",
                                "justifyContent": "space-between",
                                "gap": 2,
                                "flexWrap": "nowrap",
                            }
                        )(
                            # Informações do produto
                            mui.Box(
                                sx={"flex": 1}
                            )(
                                mui.Typography(f"{produto.nome}", variant="h6"),
                                mui.Typography(f"R$ {produto.preco:.2f} por {produto.unidade}", variant="body2"),
                            ),
                                # Imagem do produto
                                mui.Box(
                                    sx={"flex": "0 0 auto"}
                                )(
                                    html.img(
                                        src=f"https://raw.githubusercontent.com/RafaelLuckner/verdura_vendas/main/imgs/{name_img}.png",
                                        style={"maxWidth": "100px", "height": "100px"}
                                    )
                                )
  
                        )
                    
                    # Campo de quantidade
                    qtd = st.number_input(
                        "Quantidade",
                        min_value=0,
                        step=1,
                        key=f"qtd_{produto.id}_{produto.nome}",
                        label_visibility="collapsed"
                    )
                    
                    # Atualiza o carrinho
                    if qtd > 0:
                        st.session_state.carrinho[produto.id] = qtd

                    elif produto.id in st.session_state.carrinho:
                        del st.session_state.carrinho[produto.id]

                    # Exibe o subtotal
                    if qtd > 0:
                        subtotal = qtd * float(produto.preco)
                        st.markdown(f"Subtotal: **R$ {subtotal:.2f}**")

                

    if st.session_state.carrinho:
        st.subheader("📦 Resumo do Pedido")
        total = 0
        itens_pedido = []

        for produto_id, quantidade in st.session_state.carrinho.items():
            produto = next(p for p in produtos_ativos if p.id == produto_id)
            subtotal = quantidade * float(produto.preco)
            total += subtotal

            st.markdown(f"- **{produto.nome}** – {quantidade}x = R$ {subtotal:.2f}")
            itens_pedido.append(ItemPedidoCreate(
                produto_id=produto.id,
                quantidade=quantidade,
                preco_unitario=produto.preco
            ))

        st.markdown(f"### Total: **R$ {total:.2f}**")
        
        st.write('---')
        st.subheader("📅 Escolha o dia da feira")
        hoje = datetime.today().date()
        datas_validas = [
            hoje + timedelta(days=i)
            for i in range(1, 15)
            if (hoje + timedelta(days=i)).weekday() in [1, 3, 5]
        ]

        dias_pt = {1: 'Terça-feira', 3: 'Quinta-feira', 5: 'Sábado'}
        opcoes_data = [f"{dias_pt[d.weekday()]} - {d.strftime('%d/%m')}" for d in datas_validas]

        data_selecionada = st.selectbox("Disponível para entrega em:", opcoes_data)
        dia_entrega = datas_validas[opcoes_data.index(data_selecionada)]

        if 'observacao' not in st.session_state:
            st.session_state.observacao = ""

        # Campo de observação
        st.subheader("📝 Observações (opcional)")
        observacao = st.text_area(
            "Deixe aqui alguma observação sobre seu pedido:",
            placeholder="Ex: Entregue no final da tarde no veiculo de placa XXXX.",
            height=80,
            key="observacao_pedido"
        )
        st.session_state.observacao = observacao

        # Botão para mostrar confirmação
        if st.button("🛒 Confirmar Pedido", type="primary", use_container_width=True):
            st.session_state.mostrar_confirmacao = True
            st.session_state.ja_pediu = False
            st.rerun()

        # Modal de confirmação
        if st.session_state.mostrar_confirmacao:
            st.write('---')
            st.subheader("✅ Confirmação do Pedido")
            
            with st.container(border=True):
                st.markdown("### 📋 **Detalhes do seu pedido:**")
                
                # Resumo dos itens
                for produto_id, quantidade in st.session_state.carrinho.items():
                    produto = next(p for p in produtos_ativos if p.id == produto_id)
                    subtotal = quantidade * float(produto.preco)
                    st.markdown(f"• **{produto.nome}** – {quantidade} {produto.unidade} × {produto.preco:.2f} = R$  {subtotal:.2f}")
                
                st.markdown(f"### 💰 **Total:** \n **R$ {total:.2f}**")
                st.markdown(f"### 📅 **Data de entrega:** \n {dias_pt[dia_entrega.weekday()]} - {dia_entrega.strftime('%d/%m/%Y')}")
                
                if observacao.strip():
                    st.markdown(f"### 📝 **Observações:** \n {observacao}")

                st.markdown("---")
                st.markdown("**Confirme os dados acima antes de finalizar seu pedido.**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("❌ Cancelar", use_container_width=True):
                        st.session_state.mostrar_confirmacao = False
                        st.rerun()
                
                with col2:
                    if st.button("✅ Confirmar Pedido", type="primary", use_container_width=True):
                        try:

                            pedido = PedidoCreate(
                                data=dia_entrega,
                                status="Pendente",
                                total=total,
                                usuario_id=st.session_state['user_id'],
                                itens=itens_pedido,
                                observacoes=st.session_state.observacao.strip() if observacao.strip() else None
                            )
                            criar_pedido(pedido)
                            st.session_state.ja_pediu = True
                            st.session_state.carrinho = {}
                            st.session_state.mostrar_confirmacao = False
                            att_data(pedidos_by_user=True)
                            st.rerun()

                        except Exception as e:
                            st.error(f"⚠️ Ocorreu um erro ao criar o pedido: {str(e)}")
                            print('erro ao criar pedido')

    if 'ja_pediu' in st.session_state and st.session_state.ja_pediu:
        st.success("✅ Pedido criado com sucesso!")
        st.info("📦 Seus pedidos podem ser visualizados na aba Meus Pedidos")

    elif not st.session_state.ja_pediu and not st.session_state.mostrar_confirmacao:
        st.info("👆 Para começar, selecione a quantidade de um ou mais produtos acima e clique em confirmar pedido, ou visualize seus pedidos na aba Meus Pedidos")

def render_meus_pedidos():
    """Renderiza a aba dos pedidos do usuário - Versão Mobile Otimizada"""


    # Filtrar pedidos do usuário
    meus_pedidos = st.session_state.pedidos_by_user
    if not meus_pedidos:
        st.empty()
        st.info("📦 Você ainda não fez nenhum pedido.")
        st.markdown("---")
        st.write("💡 **Dica:** Vá para a aba 'Fazer Pedido' para começar!")
        return

    # === ESTATÍSTICAS EM CARDS VERTICAIS (MELHOR PARA MOBILE) ===
    st.subheader("📊 Resumo")

    # Layout em 3 cards verticais
    total_pedidos = len(meus_pedidos)
    pendentes = len([p for p in meus_pedidos if p.status == "Pendente"])
    aprovados = len([p for p in meus_pedidos if p.status == "Aprovado"])
    cancelados = len([p for p in meus_pedidos if p.status == "Cancelado"])
    total_gasto = sum(float(p.total) for p in meus_pedidos)

    # Cards de estatísticas
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="📝 Total de Pedidos",
            value=total_pedidos,
            help="Total de pedidos realizados"
        )

    with col2:
        st.metric(
            label="⏳ Pendentes",
            value=pendentes,
            delta="Aguardando" if pendentes > 0 else "Em dia",
            help="Pedidos aguardando aprovação",delta_color="inverse"
        )

    with col3:
        st.metric(
            label="⏳ Aprovados",
            value=aprovados,
            delta="Confirmados" if aprovados > 0 else "Em dia",
            help="Pedidos Aprovados"
        )


    # === FILTROS RÁPIDOS ===
    st.markdown("---")
    st.subheader("🔍 Filtrar Pedidos")

    # Filtro por status em linha única
    status_filtro = st.selectbox(
        "Status dos pedidos",
        ["Todos", "Pendente", "Aprovado", "Cancelado"],
        help="Filtrar pedidos por status"
    )

    # Aplicar filtro
    if status_filtro == "Todos":
        pedidos_filtrados = meus_pedidos
    else:
        pedidos_filtrados = [p for p in meus_pedidos if p.status == status_filtro]

    # === LISTA DE PEDIDOS OTIMIZADA PARA MOBILE ===
    st.markdown("---")
    st.subheader(f"📋 Seus Pedidos ({len(pedidos_filtrados)})")

    if not pedidos_filtrados:
        st.warning(f"Nenhum pedido encontrado com status '{status_filtro}'")
    else:
        # Ordenar pedidos (mais recentes primeiro)
        pedidos_ordenados = sorted(pedidos_filtrados, key=lambda x: x.data, reverse=True)
        
        for i, pedido in enumerate(pedidos_ordenados):
            # Status emoji e cor
            status_config = {
                "Pendente": {"emoji": "⏳", "color": "#FFA500"},
                "Aprovado": {"emoji": "✅", "color": "#28A745"},
                "Cancelado": {"emoji": "❌", "color": "#DC3545"}
            }
            
            config = status_config.get(pedido.status, {"emoji": "❓", "color": "#0F1214"})
            
            # Card do pedido com design mobile-first
            with st.container():
                # Header do pedido
                col_header1, col_header2 = st.columns([3, 1])
                
                with col_header1:
                    st.markdown(f"""
                    <div style="background: linear-gradient(90deg, {config['color']}15 0%, transparent 100%); 
                            padding: 10px; border-left: 4px solid {config['color']}; border-radius: 0 8px 8px 0; margin: 5px 0;">
                        <h4 style="margin: 0; color: {config['color']};">
                            {config['emoji']} Pedido #{pedido.id}
                        </h4>
                        <p style="margin: 5px 0; font-size: 14px; color: #666;">
                            📅 {pedido.data.strftime('%d/%m/%Y')} • 💰 R$ {pedido.total:.2f}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_header2:
                    # Botão de expandir/recolher
                    expandir_key = f"expand_{pedido.id}"
                    if expandir_key not in st.session_state:
                        st.session_state[expandir_key] = False
                    
                    if st.button("Ver Mais" if not st.session_state[expandir_key] else "Ver Menos", 
                            key=f"toggle_{pedido.id}",
                            help="Ver detalhes"):
                        st.session_state[expandir_key] = not st.session_state[expandir_key]
                        st.rerun()
                
                # Detalhes expandíveis
                if st.session_state[expandir_key]:
                    with st.container():
                        # Informações detalhadas
                        st.markdown(f"""
                        <div style=" padding: 15px; border-radius: 8px; margin: 10px 0;">
                            <p><strong>📅 Data completa:</strong> {pedido.data.strftime('%d/%m/%Y às %H:%M')}</p>
                            <p><strong>📊 Status:</strong> {config['emoji']} {pedido.status}</p>
                            <p><strong>🛍️ Quantidade de itens:</strong> {len(pedido.itens)}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Lista de itens do pedido
                        if pedido.itens:
                            st.write("**🛒 Itens do Pedido:**")
                            produtos = st.session_state.produtos
                            
                            # Container para itens
                            for j, item in enumerate(pedido.itens):
                                produto = next((p for p in produtos if p.id == item.produto_id), None)
                                if produto:
                                    subtotal = item.quantidade * item.preco_unitario
                                    
                                    # Card para cada item
                                    st.markdown(f"""
                                    <div style=" padding: 10px; margin: 5px 0; 
                                            border-radius: 6px; border: 1px solid #e9ecef;">
                                        <div style="display: flex; justify-content: space-between; align-items: center;">
                                            <div>
                                                <strong>{produto.nome}</strong><br>
                                                <small style="color: #666;">
                                                    {item.quantidade:.0f}x R$ {item.preco_unitario:.2f}
                                                </small>
                                            </div>
                                            <div style="text-align: right;">
                                                <strong style="color: #28A745;">R$ {subtotal:.2f}</strong>
                                            </div>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                        
                        # Total destacado
                        st.markdown(f"""
                        <div style="background: linear-gradient(45deg, #28A745, #20C997); color: white; 
                                padding: 15px; border-radius: 8px; text-align: center; margin: 10px 0;">
                            <h3 style="margin: 0;">💰 Total: R$ {pedido.total:.2f}</h3>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Ações do pedido
                        if pedido.status == "Pendente":
                            st.markdown("---")
                            st.write("**⚡ Ações Disponíveis:**")
                            
                            # Confirmação de cancelamento
                            cancel_key = f"cancel_confirm_{pedido.id}"
                            if cancel_key not in st.session_state:
                                st.session_state[cancel_key] = False
                            
                            if not st.session_state[cancel_key]:
                                if st.button(f"🗑️ Cancelar Pedido #{pedido.id}", 
                                        key=f"cancel_btn_{pedido.id}",
                                        use_container_width=True,
                                        type="secondary"):
                                    st.session_state[cancel_key] = True
                                    st.rerun()
                            else:
                                st.warning("⚠️ **Confirmar cancelamento do pedido?**")
                                col_confirm1, col_confirm2 = st.columns(2)
                                
                                with col_confirm1:
                                    if st.button("✅ Sim, Cancelar", 
                                            key=f"confirm_yes_{pedido.id}",
                                            use_container_width=True,
                                            type="primary"):
                                        if excluir_pedido(pedido.id):
                                            st.success("✅ Pedido cancelado com sucesso!")
                                            time.sleep(1.5)
                                            att_data(pedidos_by_user=True)
                                            st.rerun()
                                        else:
                                            st.error("❌ Erro ao cancelar pedido.")
                                
                                with col_confirm2:
                                    if st.button("❌ Não, Manter", 
                                            key=f"confirm_no_{pedido.id}",
                                            use_container_width=True):
                                        st.session_state[cancel_key] = False
                                        st.rerun()
                        
                        elif pedido.status == "Aprovado":
                            st.success("✅ **Pedido aprovado!** Aguarde o preparo.")
                        elif pedido.status == "Cancelado":
                            st.info("ℹ️ **Pedido cancelado.** Você pode fazer um novo pedido a qualquer momento.")
                
                # Separador visual entre pedidos
                if i < len(pedidos_ordenados) - 1:
                    st.markdown("<hr style='margin: 20px 0; border: 1px solid #e9ecef;'>", unsafe_allow_html=True)

def pagina_configuracoes():
    st.header("⚙️ Configurações da Conta")

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Email:** {st.session_state.email}")
        st.write(f"**Nome:** {st.session_state.username}")

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
