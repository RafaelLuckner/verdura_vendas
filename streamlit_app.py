import streamlit as st
import json
import time
from app.database import init_db
from app.auth import autenticar_usuario, cadastrar_usuario, cadastro_via_google, atualizar_username_usuario
from app import models

from pagess.admin_page import render as admin_page
from pagess.user_page import render as user_page

def validar_username(username):
    """Valida se o username é válido"""
    if not username or len(username) < 3:
        st.error("Nome de usuário deve ter pelo menos 3 caracteres.")
        return False
    if len(username) > 20:
        st.error("Nome de usuário deve ter no máximo 20 caracteres.")
        return False

    return True

def inicializar_sessao():
    """Inicializa as variáveis de sessão necessárias"""
    if "email" not in st.session_state:
        st.session_state.email = None
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False
    if "google_user" not in st.session_state:
        st.session_state.google_user = None
    if "needs_username" not in st.session_state:
        st.session_state.needs_username = False
    if "username" not in st.session_state:
        st.session_state.username = None

def fazer_logout():
    """Limpa dados da sessão no logout"""
    st.session_state.email = None
    st.session_state.is_admin = False
    st.session_state.google_user = None
    st.session_state.needs_username = False
    st.session_state.username = None
    
    # Logout do Google
    st.logout()

def processar_login_google():
    """Processa o login via Google e verifica se precisa definir username"""
    print('Processando login via Google...')
    
    if st.user.is_logged_in:
        user_info = st.user
        email = user_info.get('email')
        nome = user_info.get('name')
        
        # Atualiza o email na sessão
        st.session_state.email = email
        
        # Verifica se é um novo usuário ou se já tem username definido
        usuario_existente = cadastro_via_google(email)
        
        if not usuario_existente or not usuario_existente.get('username'):
            # Novo usuário ou usuário sem username - precisa definir
            st.session_state.needs_username = True
            st.session_state.google_user = {
                'email': email,
                'name': nome,
                'picture': user_info.get('picture')
            }
        else:
            # Usuário existente com username - login completo
            finalizar_login(email, nome, usuario_existente.get('username'))

def finalizar_login(email, nome, username):
    """Finaliza o processo de login após ter username definido"""
    # Verifica se é admin
    st.session_state.is_admin = autenticar_usuario(
        email, 
        senha='', 
        check_admin=True, 
        is_google=True
    )
    
    # Define dados do usuário
    st.session_state.google_user = {
        'email': email,
        'name': nome,
        'username': username
    }
    st.session_state.username = username
    st.session_state.needs_username = False
    

def main():
    # Inicializa o banco
    if "db" not in st.session_state:
        st.session_state.db = None
        init_db()   
    st.set_page_config(
        page_title="Login - Sistema de Vendas",
        page_icon="🥬",
    )
    inicializar_sessao()

    # Verifica se o usuário está logado via Google
    if st.user.is_logged_in and not st.session_state.email:
        processar_login_google()

    # Interface principal
    if not st.user.is_logged_in:
        mostrar_tela_login()
    elif st.session_state.needs_username:
        mostrar_tela_username()
    else:
        mostrar_area_logada()

def mostrar_tela_login():
    """Exibe a tela de login apenas com Google"""
    st.title("🥬 Vendas Verduras")
    st.subheader("Faça login com sua conta Google")
    
    # Informações sobre o sistema
    st.info("🔹 Acesso seguro através da sua conta Google")
    st.info("🔹 Primeiro acesso? Você poderá escolher seu nome de usuário")
    
    # Login com Google
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔑 Entrar com Google", type="primary", use_container_width=True):
                st.login("google")

def mostrar_tela_username():
    """Exibe a tela para definir username no primeiro acesso"""
    st.title("👋 Bem-vindo ao Sistema!")
    st.subheader("Defina seu nome de usuário")
    
    # Informações do usuário do Google
    if st.session_state.google_user:

        st.write(f"**Email:** {st.session_state.google_user['email']}")
        st.write(f"**Nome:** {st.session_state.google_user['name']}")
    
    st.divider()
    
    # Formulário para definir username
    st.write("**Escolha seu nome de usuário para podermos te identificar:**")
    st.caption("Este será o nome exibido no sistema. Você pode alterá-lo depois nas configurações.")
    
    username = st.text_input(
        "Nome de usuário",
        placeholder="Digite seu nome de usuário (3-20 caracteres)",
        help="Apenas letras, números, _ e - são permitidos"
    )
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("✅ Confirmar", type="primary", use_container_width=True):
            if validar_username(username):
                # Tenta atualizar o username no banco
                if atualizar_username_usuario(st.session_state.google_user['email'], username):
                    finalizar_login(
                        st.session_state.google_user['email'],
                        st.session_state.google_user['name'],
                        username
                    )
                    st.rerun()
                else:
                    st.error("Nome de usuário já está em uso. Tente outro.")
    
    with col2:
        if st.button("Usar nome do Google", use_container_width=True):
            nome_google = st.session_state.google_user.get('name', '')
            if validar_username(nome_google):
                if atualizar_username_usuario(st.session_state.google_user['email'], nome_google):
                    finalizar_login(
                        st.session_state.google_user['email'],
                        st.session_state.google_user['name'],
                        nome_google
                    )
                    st.rerun()
                else:
                    st.error("Nome baseado no Google já está em uso. Digite um nome personalizado.")

def mostrar_area_logada():
    """Exibe a área principal do sistema após login completo"""
    # Header com informações do usuário

    st.sidebar.write(f"Nome: {st.session_state['username']}")
    st.sidebar.write(f"Email: {st.session_state['email']}")
    st.sidebar.write(f"---")
    st.sidebar.button("🔓 Sair", on_click=fazer_logout, use_container_width=True)


    
    # Sidebar para administradores
    if st.session_state.is_admin:
        with st.sidebar:
            st.success("Acesso Administrativo")
        admin_page()
    else:
        user_page()

if __name__ == "__main__":
    main()