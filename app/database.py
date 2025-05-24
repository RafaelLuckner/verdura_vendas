import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import os
import streamlit as st

load_dotenv()

USER = st.secrets["postgres"]["user"]
PASSWORD = st.secrets["postgres"]["password"]
HOST = st.secrets["postgres"]["host"]
PORT = st.secrets["postgres"]["port"]
DBNAME = st.secrets["postgres"]["dbname"]

def get_connection():
    return psycopg2.connect(
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        dbname=DBNAME
    )

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Criar tabela usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE
        );
    ''')

    # Criar tabela produtos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            preco NUMERIC NOT NULL,
            unidade TEXT NOT NULL,
            ativo BOOLEAN DEFAULT TRUE
        );
    ''')

    # Criar tabela pedidos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id SERIAL PRIMARY KEY,
            data TIMESTAMP NOT NULL,
            status TEXT NOT NULL DEFAULT 'pendente',
            total NUMERIC NOT NULL,
            usuario_id INTEGER NOT NULL,
            CONSTRAINT fk_usuario
                FOREIGN KEY(usuario_id)
                REFERENCES usuarios(id)
                ON DELETE CASCADE
        );
    ''')

    # Criar tabela itens_pedido
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS itens_pedido (
            id SERIAL PRIMARY KEY,
            pedido_id INTEGER NOT NULL,
            produto_id INTEGER NOT NULL,
            quantidade NUMERIC NOT NULL,
            preco_unitario NUMERIC NOT NULL,
            subtotal NUMERIC NOT NULL,
            CONSTRAINT fk_pedido
                FOREIGN KEY(pedido_id)
                REFERENCES pedidos(id)
                ON DELETE CASCADE,
            CONSTRAINT fk_produto
                FOREIGN KEY(produto_id)
                REFERENCES produtos(id)
                ON DELETE CASCADE
        );
    ''')

    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    init_db()

