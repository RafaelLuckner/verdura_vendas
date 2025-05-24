import sqlite3
from pathlib import Path

DB_PATH = Path("vendas.db")

def tornar_admin(email: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("UPDATE usuarios SET is_admin = 1 WHERE email = ?", (email,))
    conn.commit()
    conn.close()
    print(f"Usuário '{email}' agora é admin.")

def apagar_usuario(email: str) -> bool:
    """
    Apaga um usuário da tabela 'usuarios' com base no e-mail fornecido.
    Retorna True se o usuário foi apagado com sucesso, False se o usuário não foi encontrado.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Verifica se o usuário existe
        cursor.execute("SELECT email FROM usuarios WHERE email = ?", (email,))
        resultado = cursor.fetchone()

        if not resultado:
            print(f"Usuário '{email}' não encontrado no banco de dados.")
            return False

        # Apaga o usuário
        cursor.execute("DELETE FROM usuarios WHERE email = ?", (email,))
        conn.commit()
        print(f"Usuário '{email}' apagado com sucesso.")
        return True
    except sqlite3.Error as e:
        print(f"Erro ao apagar usuário '{email}': {e}")
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    # tornar_admin("rafaelluckner3@gmail.com")
    apagar_usuario("rafaelluckner1@gmail.com")