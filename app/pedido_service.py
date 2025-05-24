from datetime import datetime
from typing import List
import sqlite3
from pydantic import BaseModel, condecimal

# Importando seus modelos (exemplo)
from models import PedidoCreate, PedidoDB, ItemPedidoCreate, ItemPedidoDB, ProdutoDB

from database import get_connection


def listar_produtos() -> List[ProdutoDB]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, preco, unidade FROM produtos")
    rows = cursor.fetchall()
    conn.close()

    return [ProdutoDB(id=row[0], nome=row[1], preco=row[2], unidade=row[3]) for row in rows]


def criar_pedido(pedido_create: PedidoCreate) -> PedidoDB:
    conn = get_connection()
    cursor = conn.cursor()

    # Calcular total do pedido somando quantidade * preco dos produtos
    total = 0
    for item in pedido_create.itens:
        cursor.execute("SELECT preco FROM produtos WHERE id = ?", (item.produto_id,))
        preco = cursor.fetchone()
        if preco is None:
            raise ValueError(f"Produto ID {item.produto_id} não existe.")
        total += preco[0] * float(item.quantidade)

    # Inserir pedido
    data_str = pedido_create.data.strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO pedidos (data, status, total) VALUES (?, ?, ?)",
        (data_str, pedido_create.status, float(total)),
    )
    pedido_id = cursor.lastrowid

    # Inserir itens do pedido
    for item in pedido_create.itens:
        cursor.execute(
            "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade) VALUES (?, ?, ?)",
            (pedido_id, item.produto_id, float(item.quantidade)),
        )

    conn.commit()
    conn.close()

    # Montar resposta com dados do pedido criado
    itens_db = [
        ItemPedidoDB(id=0, pedido_id=pedido_id, produto_id=item.produto_id, quantidade=item.quantidade)
        for item in pedido_create.itens
    ]

    return PedidoDB(id=pedido_id, data=pedido_create.data, status=pedido_create.status, total=total, itens=itens_db)


def buscar_pedido(pedido_id: int) -> PedidoDB:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, data, status, total FROM pedidos WHERE id = ?", (pedido_id,))
    pedido_row = cursor.fetchone()
    if not pedido_row:
        conn.close()
        raise ValueError(f"Pedido {pedido_id} não encontrado")

    cursor.execute(
        "SELECT id, produto_id, quantidade FROM itens_pedido WHERE pedido_id = ?", (pedido_id,)
    )
    itens_rows = cursor.fetchall()
    conn.close()

    itens = [
        ItemPedidoDB(id=row[0], pedido_id=pedido_id, produto_id=row[1], quantidade=row[2])
        for row in itens_rows
    ]

    data = datetime.strptime(pedido_row[1], "%Y-%m-%d %H:%M:%S")
    pedido = PedidoDB(id=pedido_row[0], data=data, status=pedido_row[2], total=pedido_row[3], itens=itens)
    return pedido


def atualizar_status_pedido(pedido_id: int, novo_status: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    conn.commit()
    conn.close()
