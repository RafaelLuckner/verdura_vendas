from .database import get_connection
from .models import ProdutoCreate, ProdutoDB, ItemPedidoCreate, PedidoCreate, PedidoDB, ItemPedidoDB
from datetime import datetime
import psycopg2
import streamlit as st

def adicionar_produto(produto: ProdutoCreate) -> int:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                'INSERT INTO produtos (nome, preco, unidade, ativo) VALUES (%s, %s, %s, %s) RETURNING id',
                (produto.nome, float(produto.preco), produto.unidade, produto.ativo)
            )
            produto_id = cursor.fetchone()[0]
        conn.commit()
    return produto_id

def listar_produtos():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, preco, unidade, ativo FROM produtos")
    rows = cursor.fetchall()
    conn.close()
    return [
        ProdutoDB(id=row[0], nome=row[1], preco=row[2], unidade=row[3], ativo=row[4])
        for row in rows
    ]
def listar_usuarios():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT id, email FROM usuarios')
            rows = cursor.fetchall()
    return rows

def atualizar_produto(produto_id: int, produto: ProdutoCreate) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT nome, preco, unidade, ativo FROM produtos WHERE id = %s', (produto_id,))
            resultado = cursor.fetchone()

            if not resultado:
                return False  # Produto não encontrado

            nome_atual, preco_atual, unidade_atual, ativo_atual = resultado

            if (
                nome_atual == produto.nome and
                float(preco_atual) == float(produto.preco) and
                unidade_atual == produto.unidade and
                ativo_atual == produto.ativo
            ):
                return False  # Nenhuma alteração

            cursor.execute(
                'UPDATE produtos SET nome = %s, preco = %s, unidade = %s, ativo = %s WHERE id = %s',
                (produto.nome, float(produto.preco), produto.unidade, produto.ativo, produto_id)
            )
        conn.commit()
    return True

def excluir_produto(produto_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('DELETE FROM produtos WHERE id = %s', (produto_id,))
            affected = cursor.rowcount > 0
        conn.commit()
    return affected

def criar_pedido(pedido: PedidoCreate) -> int:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            total = 0
            itens_db = []
            for item in pedido.itens:
                cursor.execute('SELECT preco FROM produtos WHERE id = %s', (item.produto_id,))
                result = cursor.fetchone()
                if not result:
                    raise ValueError(f"Produto ID {item.produto_id} não encontrado")
                preco = result[0]
                subtotal = preco * float(item.quantidade)
                total += subtotal
                itens_db.append({
                    'produto_id': item.produto_id,
                    'quantidade': item.quantidade,
                    'preco_unitario': preco,
                    'subtotal': subtotal
                })

            data_str = pedido.data.strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(
                'INSERT INTO pedidos (data, status, total, usuario_id) VALUES (%s, %s, %s, %s) RETURNING id',
                (data_str, pedido.status, float(total), pedido.usuario_id)
            )
            pedido_id = cursor.fetchone()[0]

            for item in itens_db:
                cursor.execute(
                    '''INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario, subtotal)
                       VALUES (%s, %s, %s, %s, %s)''',
                    (pedido_id, item['produto_id'], float(item['quantidade']), item['preco_unitario'], item['subtotal'])
                )
        conn.commit()
    return pedido_id

def listar_pedidos() -> list[PedidoDB]:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT id, data, status, total, usuario_id FROM pedidos')
            pedidos_rows = cursor.fetchall()

            pedidos = []
            for row in pedidos_rows:
                cursor.execute(
                    'SELECT id, produto_id, quantidade, preco_unitario, subtotal FROM itens_pedido WHERE pedido_id = %s',
                    (row[0],)
                )
                itens_rows = cursor.fetchall()
                itens = [
                    ItemPedidoDB(
                        id=item[0],
                        pedido_id=row[0],
                        produto_id=item[1],
                        quantidade=item[2],
                        preco_unitario=item[3],
                        subtotal=item[4]
                    ) for item in itens_rows
                ]
                pedidos.append(PedidoDB(
                    id=row[0],
                    data=row[1],  # já vem como datetime do Postgres
                    status=row[2],
                    total=row[3],
                    usuario_id=row[4],
                    itens=itens
                ))
    return pedidos

def get_pedidos_by_user(user_id: int) -> list[PedidoDB]:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT id, data, status, total FROM pedidos WHERE usuario_id = %s', (user_id,))
            rows = cursor.fetchall()
            pedidos = []
            for row in rows:
                cursor.execute('SELECT id, produto_id, quantidade, preco_unitario, subtotal FROM itens_pedido WHERE pedido_id = %s', (row[0],))
                itens_rows = cursor.fetchall()
                itens = [
                    ItemPedidoDB(
                        id=item[0],
                        pedido_id=row[0],
                        produto_id=item[1],
                        quantidade=item[2],
                        preco_unitario=item[3],
                        subtotal=item[4]
                    ) for item in itens_rows
                ]
                pedidos.append(PedidoDB(
                    id=row[0],
                    data=row[1],  # já vem como datetime do Postgres
                    status=row[2],
                    total=row[3],
                    usuario_id=user_id,
                    itens=itens
                ))
    return pedidos

def atualizar_status_pedido(pedido_id: int, status: str) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('UPDATE pedidos SET status = %s WHERE id = %s', (status, pedido_id))
            affected = cursor.rowcount > 0
        conn.commit()
    return affected

def excluir_pedido(pedido_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('DELETE FROM itens_pedido WHERE pedido_id = %s', (pedido_id,))
            cursor.execute('DELETE FROM pedidos WHERE id = %s', (pedido_id,))
            affected = cursor.rowcount > 0
        conn.commit()
    return affected

def get_user_by_id(user_id: int) -> tuple | None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT id, email FROM usuarios WHERE id = %s', (user_id,))
            user = cursor.fetchone()
    return user
def get_user_by_email(email: str) -> tuple | None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT id, email FROM usuarios WHERE email = %s', (email,))
            user = cursor.fetchone()
    return user[0]

def get_produto_by_id(produto_id: int) -> ProdutoDB | None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT id, nome, preco, unidade, ativo FROM produtos WHERE id = %s', (produto_id,))
            row = cursor.fetchone()
    if row:
        return ProdutoDB(id=row[0], nome=row[1], preco=row[2], unidade=row[3], ativo=row[4])
    return None
