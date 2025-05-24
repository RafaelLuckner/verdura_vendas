import streamlit as st
import json
from app.database import init_db
from app.auth import autenticar_usuario, cadastrar_usuario, cadastro_via_google
from app import models
from streamlit_google_auth import Authenticate

from pagess.admin_page import render as admin_page
from pagess.user_page import render as user_page


def validar_info(email, senha):
    try:
        models.UsuarioBase(email=email)
    except:
        st.error("Formato de e-mail inválido.")
        st.stop()
    try:
        models.UsuarioCreate(email=email, senha=senha)
    except:
        st.error("Formato de senha inválido. (mínimo 6 caracteres)")
        st.stop()

def inicializar_sessao():
    """Inicializa as variáveis de sessão necessárias"""
    if "email" not in st.session_state:
        st.session_state.email = None
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False
    if "google_user" not in st.session_state:
        st.session_state.google_user = None
    if "login_rerun_done" not in st.session_state:
        st.session_state.login_rerun_done = False
    credentials_dict = {
        "client_id": st.secrets["google_auth"]["client_id"],
        "client_secret": st.secrets["google_auth"]["client_secret"],
        "project_id": st.secrets["google_auth"]["project_id"],
        "auth_uri": st.secrets["google_auth"]["auth_uri"],
        "token_uri": st.secrets["google_auth"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["google_auth"]["auth_provider_x509_cert_url"],
        "redirect_uris": [st.secrets["google_auth"]["redirect_uri"]]
    }

    # Salva como JSON temporário
    with open("google_credentials.json", "w") as f:
        json.dump({"web": credentials_dict}, f)

    # Usa no seu autenticador
    if 'connected' not in st.session_state:
        authenticator = Authenticate(
            secret_credentials_path='google_credentials.json',
            cookie_name='my_cookie_name',
            cookie_key='this_is_secret',
            redirect_uri=st.secrets["google_auth"]["redirect_uri"],
        )
        st.session_state["authenticator"] = authenticator
        
def fazer_logout(authenticator):
    """Limpa dados da sessão no logout"""
    st.session_state.email = None
    st.session_state.is_admin = False
    st.session_state.google_user = None
    st.session_state.login_rerun_done = False
    
    # Logout do Google se autenticado
    if 'user_info' in st.session_state:
        st.session_state.user_info = None
        authenticator.logout()
    st.session_state.clear()
    st.rerun()

def processar_login_google():
    print('---')
    print("Processando login via Google...")
    if 'user_info' in st.session_state and st.session_state.connected == True:
        email = st.session_state['user_info'].get('email')
        nome = st.session_state['user_info'].get('name')
        print("pass0")
        
        # Cadastra o usuário via Google se não existir
        cadastro_via_google(email)
        
        # Verifica se é admin
        st.session_state.is_admin = autenticar_usuario(
            email, 
            senha='', 
            check_admin=True, 
            is_google=True
        )
        
        # Define como conectado
        st.session_state.email = email
        st.session_state.google_user = {
            'email': email,
            'name': nome,
            'picture': st.session_state['user_info'].get('picture')
        }
        
        st.success(f"Login realizado com sucesso! Bem-vindo(a), {email}")
        
        # Rerun total na primeira autenticação
        if not st.session_state.get("login_rerun_done", False):
            st.session_state["login_rerun_done"] = True
            st.rerun()

def main():
    # Configurações iniciais
    init_db()
    st.set_page_config(
        page_title="Login - Sistema de Vendas",
        page_icon="🔐",
        # layout="wide",
        
    )
    inicializar_sessao()

    # Interface principal
    if not st.session_state.connected:
        mostrar_tela_login()
    else:
        mostrar_area_logada()

def mostrar_tela_login():
    """Exibe a tela de login/cadastro"""
    st.title("🔐 Sistema de Vendas")
    
    aba = st.radio("Acesso ao sistema", ["Login", "Cadastro"], horizontal=True)
    
    if aba == "Login":
        st.subheader("Fazer Login")
        
        # Login tradicional
        with st.container():
            st.write("**Login com email e senha:**")
            email = st.text_input("Email", key="login_email")
            senha = st.text_input("Senha", type="password", key="login_senha")
            
            if st.button("Entrar", type="primary", use_container_width=True):
                if email and senha:
                    validar_info(email, senha)
                    if autenticar_usuario(email, senha):
                        st.session_state.is_admin = autenticar_usuario(
                            email, senha, check_admin=True
                        )
                        st.session_state.connected = True
                        st.session_state.email = email
                        st.success("Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Credenciais inválidas.")
                else:
                    st.warning("Preencha todos os campos.")
        
        st.divider()
        
        # Login com Google
        with st.container():
            st.write("**Ou faça login com Google:**")
            # Catch the login event
            st.session_state["authenticator"].check_authentification()

            # Create the login button
            st.session_state["authenticator"].login()
            processar_login_google()
        
    else:  # Cadastro
        st.subheader("Criar Conta")
        
        email = st.text_input("Email para cadastro", key="cadastro_email")
        senha = st.text_input("Senha", type="password", key="cadastro_senha")
        
        if st.button("Cadastrar", type="primary", use_container_width=True):
            if email and senha:
                validar_info(email, senha)
                if cadastrar_usuario(email, senha):
                    st.success("Cadastro realizado com sucesso! Faça login.")
                else:
                    st.error("Erro: e-mail já cadastrado.")
            else:
                st.warning("Preencha todos os campos.")

def mostrar_area_logada():

    if 'user_info' in st.session_state and st.session_state.email == None:
        processar_login_google()
        
    # Header com informações do usuário
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.session_state.google_user and st.session_state.google_user.get('name'):
            st.write(f"**Olá, {st.session_state.google_user.get('email')}!**")

        else:
            st.write(f"**Olá, {st.session_state.email}!**")
    
    with col2:
        if st.button("🔓 Sair", use_container_width=True):
            fazer_logout(st.session_state.authenticator)
    
    # Sidebar para administradores
    if st.session_state.is_admin:
        menu_option = st.sidebar.radio(
            "Menu",
            ["Produtos", "Pedidos", "Usuários"]
        )

        admin_page(menu_option)

    else:
        user_page()


if __name__ == "__main__":
    main()
    # st.session_state