import bcrypt
from app.database import get_connection
import streamlit as st

def cadastrar_usuario(email: str, senha: str) -> bool:
    senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt())
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (email, senha_hash) VALUES (%s, %s)", (email, senha_hash))
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro ao cadastrar usuário: {e}")
        return False
    finally:
        conn.close()

def autenticar_usuario(email: str, senha : str, check_admin=False, is_google = False):
    conn = get_connection()
    cursor = conn.cursor()

    if is_google:
        cursor.execute("SELECT is_admin FROM usuarios WHERE email = %s", (email,))
        resultado = cursor.fetchone()
        conn.close()
        if resultado:
            return bool(resultado[0])
        return False

    else:
        cursor.execute("SELECT senha_hash, is_admin FROM usuarios WHERE email = %s", (email,))
        resultado = cursor.fetchone()
        conn.close()

    if resultado:
        senha_hash, is_admin = resultado
        if bcrypt.checkpw(senha.encode(), bytes(senha_hash)):
            if check_admin:
                return bool(is_admin)
            return True

    return None

def cadastro_via_google(email: str) -> bool:
    # avaliar se o email ja existe
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM usuarios WHERE email = %s", (email,))
    resultado = cursor.fetchone()
    conn.close()

    if resultado:
        return False

    conn = get_connection()
    try:
        senha= email + 'pppp'
        senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt())
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (email, senha_hash) VALUES (%s, %s)", (email, senha_hash))
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro no cadastro via Google: {e}")
        return False
    finally:
        conn.close()
