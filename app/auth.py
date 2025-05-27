import bcrypt
from app.database import get_connection
import streamlit as st

def cadastrar_usuario(email: str, senha: str) -> bool:
    """Cadastra um novo usuário com email e senha"""
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

def autenticar_usuario(email: str, senha: str = '', check_admin=False, is_google=False):
    """Autentica usuário via senha normal ou Google"""
    conn = get_connection()
    cursor = conn.cursor()

    if is_google:
        # Para usuários Google, apenas verifica se existe e retorna status admin
        cursor.execute("SELECT is_admin, username FROM usuarios WHERE email = %s", (email,))
        resultado = cursor.fetchone()
        conn.close()
        if resultado:
            return bool(resultado[0]) if check_admin else True
        return False
    else:
        # Autenticação tradicional com senha
        cursor.execute("SELECT senha_hash, is_admin FROM usuarios WHERE email = %s", (email,))
        resultado = cursor.fetchone()
        conn.close()

        if resultado:
            senha_hash, is_admin = resultado
            if bcrypt.checkpw(senha.encode(), bytes(senha_hash)):
                if check_admin:
                    return bool(is_admin)
                return True

    return False

def cadastro_via_google(email: str) -> dict:
    """Cadastra ou retorna informações de usuário Google"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verifica se usuário já existe
    cursor.execute("SELECT email, username, is_admin FROM usuarios WHERE email = %s", (email,))
    resultado = cursor.fetchone()
    
    if resultado:
        # Usuário existe, retorna suas informações
        conn.close()
        return {
            'email': resultado[0],
            'username': resultado[1],
            'is_admin': bool(resultado[2]),
            'exists': True
        }
    
    # Usuário não existe, cria novo registro
    try:
        senha = email + 'google_auth_token'  # Senha placeholder para usuários Google
        senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt())
        cursor.execute(
            "INSERT INTO usuarios (email, senha_hash, username) VALUES (%s, %s, %s)", 
            (email, senha_hash, None)  # username como NULL inicialmente
        )
        conn.commit()
        conn.close()
        return {
            'email': email,
            'username': None,
            'is_admin': False,
            'exists': False
        }
    except Exception as e:
        print(f"Erro no cadastro via Google: {e}")
        conn.rollback()
        conn.close()
        return None

def atualizar_username_usuario(email: str, username: str) -> bool:
    """Atualiza o username de um usuário"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Verifica se o username já está em uso
        cursor.execute("SELECT id FROM usuarios WHERE username = %s AND email != %s", (username, email))
        if cursor.fetchone():
            conn.close()
            return False  # Username já em uso
        
        # Atualiza o username
        cursor.execute("UPDATE usuarios SET username = %s WHERE email = %s", (username, email))
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            return True
        else:
            conn.close()
            return False
            
    except Exception as e:
        print(f"Erro ao atualizar username: {e}")
        conn.rollback()
        conn.close()
        return False

def verificar_username_disponivel(username: str) -> bool:
    """Verifica se um username está disponível"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM usuarios WHERE username = %s", (username,))
        resultado = cursor.fetchone()
        conn.close()
        return resultado is None  # True se não encontrou (disponível)
    except Exception as e:
        print(f"Erro ao verificar username: {e}")
        conn.close()
        return False

def get_usuario_por_email(email: str) -> dict:
    """Retorna informações completas de um usuário pelo email"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT id, email, username, is_admin, created_at FROM usuarios WHERE email = %s", 
            (email,)
        )
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado:
            return {
                'id': resultado[0],
                'email': resultado[1],
                'username': resultado[2],
                'is_admin': bool(resultado[3]),
                'created_at': resultado[4]
            }
        return None
        
    except Exception as e:
        print(f"Erro ao buscar usuário: {e}")
        conn.close()
        return None