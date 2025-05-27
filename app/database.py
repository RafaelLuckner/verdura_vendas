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
    """Estabelece conexão com o banco PostgreSQL"""
    return psycopg2.connect(
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        dbname=DBNAME
    )


def init_db():
    """Inicializa o banco de dados com todas as tabelas necessárias"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Tabela de controle de inicialização
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')


        # Criar/atualizar tabela usuarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                senha_hash TEXT NOT NULL,
                username TEXT UNIQUE,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')


        # Criar tabela produtos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS produtos (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                preco NUMERIC(10,2) NOT NULL,
                unidade TEXT NOT NULL,
                ativo BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        # Criar tabela pedidos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pedidos (
                id SERIAL PRIMARY KEY,
                data TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL DEFAULT 'pendente',
                total NUMERIC(10,2) NOT NULL,
                usuario_id INTEGER NOT NULL,
                observacoes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
                quantidade NUMERIC(10,3) NOT NULL,
                preco_unitario NUMERIC(10,2) NOT NULL,
                subtotal NUMERIC(10,2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
        print("✅ Banco de dados inicializado com sucesso!")

    except Exception as e:
        print(f"❌ Erro ao inicializar banco de dados: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def verificar_status_db():
    """Verifica o status e versão do banco de dados"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Verificar versão
        cursor.execute("SELECT value FROM metadata WHERE key = 'db_version'")
        version = cursor.fetchone()
        
        # Contar registros principais
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        total_usuarios = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM produtos WHERE ativo = true")
        total_produtos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM pedidos")
        total_pedidos = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return {
            'version': version[0] if version else 'Desconhecida',
            'usuarios': total_usuarios,
            'produtos': total_produtos,
            'pedidos': total_pedidos,
            'status': 'OK'
        }
        
    except Exception as e:
        return {
            'version': 'Erro',
            'usuarios': 0,
            'produtos': 0,
            'pedidos': 0,
            'status': f'Erro: {e}'
        }

def reset_database():
    """CUIDADO: Remove todos os dados do banco (apenas para desenvolvimento)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Remover todas as tabelas
        tabelas = ['itens_pedido', 'pedidos', 'produtos', 'usuarios', 'metadata']
        
        for tabela in tabelas:
            cursor.execute(f"DROP TABLE IF EXISTS {tabela} CASCADE")
        
        # Remover função
        cursor.execute("DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE")
        
        conn.commit()
        print("⚠️ Banco de dados resetado com sucesso!")
        
        # Reinicializar
        cursor.close()
        conn.close()
        init_db()
        
    except Exception as e:
        print(f"❌ Erro ao resetar banco: {e}")
        conn.rollback()
    finally:
        if not cursor.closed:
            cursor.close()
        if not conn.closed:
            conn.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "reset":
            confirma = input("⚠️ ATENÇÃO: Isso irá apagar TODOS os dados! Digite 'CONFIRMO' para continuar: ")
            if confirma == "CONFIRMO":
                reset_database()
            else:
                print("Operação cancelada.")
        elif sys.argv[1] == "status":
            status = verificar_status_db()
            print(f"""
📊 Status do Banco de Dados:
- Versão: {status['version']}
- Usuários: {status['usuarios']}
- Produtos: {status['produtos']}
- Pedidos: {status['pedidos']}
- Status: {status['status']}
            """)
    else:
        init_db()