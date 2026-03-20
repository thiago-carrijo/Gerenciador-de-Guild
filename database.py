import sqlite3

DB_FILE = "guild_mucabrasil.db"

# ─────────────────────────────────────────────
#  INICIALIZAÇÃO
# ─────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS membros (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            nome       TEXT NOT NULL UNIQUE,
            recrutador TEXT,
            telefone   TEXT
        )
    """)
    # Migração: adiciona colunas caso o banco já exista sem elas
    for col, tipo in [("recrutador", "TEXT"), ("telefone", "TEXT")]:
        try:
            c.execute(f"ALTER TABLE membros ADD COLUMN {col} {tipo}")
        except sqlite3.OperationalError:
            pass  # coluna já existe
    c.execute("""
        CREATE TABLE IF NOT EXISTS contas (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            membro_id INTEGER NOT NULL,
            nome      TEXT NOT NULL,
            FOREIGN KEY (membro_id) REFERENCES membros(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# ─────────────────────────────────────────────
#  OPERAÇÕES DE MEMBROS
# ─────────────────────────────────────────────
def adicionar_membro(nome, recrutador="", telefone=""):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO membros (nome, recrutador, telefone) VALUES (?, ?, ?)",
            (nome.strip(), recrutador.strip(), telefone.strip())
        )

def editar_membro(membro_id, novo_nome, recrutador="", telefone=""):
    with get_conn() as conn:
        conn.execute(
            "UPDATE membros SET nome=?, recrutador=?, telefone=? WHERE id=?",
            (novo_nome.strip(), recrutador.strip(), telefone.strip(), membro_id)
        )

def excluir_membro(membro_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM membros WHERE id=?", (membro_id,))

# ─────────────────────────────────────────────
#  OPERAÇÕES DE CONTAS
# ─────────────────────────────────────────────
def adicionar_conta(membro_id, nome_conta):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO contas (membro_id, nome) VALUES (?,?)",
            (membro_id, nome_conta.strip())
        )

def renomear_conta(conta_id, novo_nome):
    with get_conn() as conn:
        conn.execute(
            "UPDATE contas SET nome=? WHERE id=?",
            (novo_nome.strip(), conta_id)
        )

def excluir_conta(conta_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM contas WHERE id=?", (conta_id,))

# ─────────────────────────────────────────────
#  BUSCA
# ─────────────────────────────────────────────
def buscar(termo=""):
    termo = f"%{termo.strip()}%"
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT m.id, m.nome, m.recrutador, m.telefone, c.id, c.nome
            FROM membros m
            LEFT JOIN contas c ON c.membro_id = m.id
            WHERE m.nome LIKE ? OR c.nome LIKE ?
            ORDER BY m.nome, c.nome
        """, (termo, termo)).fetchall()

    membros = {}
    for mid, mnome, recrutador, telefone, cid, cnome in rows:
        if mid not in membros:
            membros[mid] = {
                "nome":       mnome,
                "recrutador": recrutador or "",
                "telefone":   telefone or "",
                "contas":     []
            }
        if cid:
            membros[mid]["contas"].append({"id": cid, "nome": cnome})
    return membros
