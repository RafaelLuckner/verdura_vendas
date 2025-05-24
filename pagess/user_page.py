import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from app.crud import listar_produtos, criar_pedido, listar_pedidos, excluir_pedido, get_user_by_email, get_pedidos_by_user
from app.models import PedidoCreate, ItemPedidoCreate
import time
from itertools import zip_longest


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
    """Renderiza a página do usuário"""
    st.title(f"🛒 {st.session_state.email.split('@')[0]}")
    
    # Inicializar dados na sessão
    if 'pedidos' not in st.session_state:
        st.session_state.pedidos = listar_pedidos()
    if 'produtos' not in st.session_state:
        st.session_state.produtos = listar_produtos()
    if 'pedidos_by_user' not in st.session_state:
        st.session_state.pedidos_by_user = get_pedidos_by_user(st.session_state.user_id)
    
    # Botão de atualizar no topo
    if st.button("🔄 Atualizar"):
        att_data(produtos=True, pedidos_by_user=True)
    
    # Abas principais
    tab1, tab2 = st.tabs(["🆕 Novo Pedido", "📋 Meus Pedidos"])
    
    with tab1:
        render_novo_pedido(user_id)
    
    with tab2:
        render_meus_pedidos(user_id)

def render_novo_pedido(user_id):
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
    # Faça uma cópia local
    carrinho_temp = st.session_state.carrinho.copy()

    st.subheader("✨ Escolha seus produtos")

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

    from streamlit_elements import elements, mui, html
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
                        value=st.session_state.carrinho.get(produto.id, 0),
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

        st.markdown(f"### Total a pagar: **R$ {total:.2f}**")
        
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


        if st.button("✅ Finalizar Pedido", type="primary", use_container_width=True):
            try:
                pedido = PedidoCreate(
                    data=dia_entrega,
                    status="Pendente",
                    total=total,
                    usuario_id=user_id,
                    itens=itens_pedido
                )

                criar_pedido(pedido)
                st.success(f"Pedido criado com sucesso!")
                st.session_state.carrinho = {}
                time.sleep(4)
                att_data(pedidos_by_user=True)

            except Exception as e:
                st.error(f"⚠️ Ocorreu um erro ao criar o pedido: {str(e)}")
    else:
        st.info("👆 Para começar, selecione a quantidade de um ou mais produtos acima, ou visualize seus pedidos na aba Meus Pedidos")



def render_meus_pedidos(user_id):
    """Renderiza a aba dos pedidos do usuário"""
    st.header("Meus Pedidos")
    
    # Filtrar pedidos do usuário
    meus_pedidos = st.session_state.pedidos_by_user
    if not meus_pedidos:
        st.info("Você ainda não fez nenhum pedido.")
        return
    
    # Estatísticas rápidas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total", len(meus_pedidos))
    with col2:
        pendentes = len([p for p in meus_pedidos if p.status == "Pendente"])
        st.metric("Pendentes", pendentes)
    with col3:
        total_gasto = sum(float(p.total) for p in meus_pedidos)
        st.metric("Gasto", f"R$ {total_gasto:.0f}")
    
    # Lista de pedidos (mais recentes primeiro)
    meus_pedidos_ordenados = sorted(meus_pedidos, key=lambda x: x.data, reverse=True)
    
    for pedido in meus_pedidos_ordenados:
        # Status emoji
        status_emoji = {
            "Pendente": "⏳",
            "Aprovado": "✅", 
            "Cancelado": "❌"
        }.get(pedido.status, "❓")
        
        with st.expander(
            f"{status_emoji} Pedido #{pedido.id} - {pedido.data.strftime('%d/%m')} - R$ {pedido.total:.2f}"
        ):
            # Informações do pedido
            st.write(f"**Data:** {pedido.data.strftime('%d/%m/%Y')}")
            st.write(f"**Status:** {pedido.status}")
            
            # Itens do pedido
            if pedido.itens:
                st.write("**Itens:**")
                produtos = st.session_state.produtos
                
                for item in pedido.itens:
                    produto = next((p for p in produtos if p.id == item.produto_id), None)
                    if produto:
                        subtotal = item.quantidade * item.preco_unitario
                        st.write(f"• {produto.nome} - {item.quantidade}x = R$ {subtotal:.2f}")
            
            st.write(f"**Total: R$ {pedido.total:.2f}**")
            
            # Ação de cancelar (apenas para pedidos pendentes)
            if pedido.status == "Pendente":
                if st.button(f"🗑️ Cancelar Pedido", key=f"cancel_{pedido.id}"):
                    if excluir_pedido(pedido.id):
                        st.success("Pedido cancelado!")
                        time.sleep(1)
                        att_data(pedidos_by_user=True)
                    else:
                        st.error("Erro ao cancelar pedido.")


