# import sqlite3
# import pandas as pd
# from sqlalchemy import create_engine
# from urllib.parse import quote_plus
# from dotenv import load_dotenv
# import os

# # Load env variables
# load_dotenv()

# # PostgreSQL URL (encode senha)
# senha = quote_plus(os.getenv("password"))
# usuario = os.getenv("user")
# host = os.getenv("host")
# port = os.getenv("port")
# dbname = os.getenv("dbname")

# pg_url = f"postgresql://{usuario}:{senha}@{host}:{port}/{dbname}"
# pg_engine = create_engine(pg_url)

# # Conexão com SQLite local
# sqlite_conn = sqlite3.connect("vendas.db")

# # Migração na ordem correta (respeitando dependências)
# tabelas = ['usuarios', 'produtos', 'pedidos', 'itens_pedido']

# for tabela in tabelas:
#     print(f"Migrando tabela {tabela}...")
#     df = pd.read_sql_query(f"SELECT * FROM {tabela}", sqlite_conn)

#     # Conversões específicas
#     if 'is_admin' in df.columns:
#         df['is_admin'] = df['is_admin'].astype(bool)
#     if 'ativo' in df.columns:
#         df['ativo'] = df['ativo'].astype(bool)
#     if 'data' in df.columns:
#         df['data'] = pd.to_datetime(df['data'])  # converte para datetime

#     df.to_sql(tabela, pg_engine, index=False, if_exists="append")

# print("Migração concluída com sucesso.")
# sqlite_conn.close()
