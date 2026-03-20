import streamlit as st
from supabase import create_client, Client
import hashlib


# ─────────────────────────────────────────────
#  CONEXÃO
# ─────────────────────────────────────────────
@st.cache_resource
def get_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def db() -> Client:
    return get_client()


# ─────────────────────────────────────────────
#  AUTENTICAÇÃO
# ─────────────────────────────────────────────
def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()


def verificar_login(login: str, senha: str) -> bool:
    res = db().table("usuarios") \
        .select("id") \
        .eq("login", login.strip()) \
        .eq("senha", hash_senha(senha)) \
        .execute()
    return len(res.data) > 0


# ─────────────────────────────────────────────
#  MEMBROS
# ─────────────────────────────────────────────
def buscar(termo: str = "") -> list:
    if termo.strip():
        membros_res = db().table("membros") \
            .select("*").ilike("nome", f"%{termo}%").order("nome").execute().data

        contas_res = db().table("contas") \
            .select("membro_id").ilike("nome", f"%{termo}%").execute().data
        ids_por_conta = [c["membro_id"] for c in contas_res]

        if ids_por_conta:
            membros_extra = db().table("membros") \
                .select("*").in_("id", ids_por_conta).order("nome").execute().data
            ids_ja = {m["id"] for m in membros_res}
            for m in membros_extra:
                if m["id"] not in ids_ja:
                    membros_res.append(m)
            membros_res.sort(key=lambda m: m["nome"])
    else:
        membros_res = db().table("membros") \
            .select("*").order("nome").execute().data

    ids = [m["id"] for m in membros_res]
    contas_por_membro = {m["id"]: [] for m in membros_res}
    if ids:
        todas = db().table("contas") \
            .select("*").in_("membro_id", ids).order("nome").execute().data
        for c in todas:
            contas_por_membro[c["membro_id"]].append(c)

    for m in membros_res:
        m["contas"] = contas_por_membro[m["id"]]

    return membros_res


def adicionar_membro(nome: str, recrutador: str = "", telefone: str = ""):
    db().table("membros").insert({
        "nome":       nome.strip(),
        "recrutador": recrutador.strip(),
        "telefone":   telefone.strip(),
    }).execute()


def editar_membro(membro_id: int, nome: str, recrutador: str = "", telefone: str = ""):
    db().table("membros").update({
        "nome":       nome.strip(),
        "recrutador": recrutador.strip(),
        "telefone":   telefone.strip(),
    }).eq("id", membro_id).execute()


def excluir_membro(membro_id: int):
    db().table("membros").delete().eq("id", membro_id).execute()


# ─────────────────────────────────────────────
#  CONTAS
# ─────────────────────────────────────────────
def adicionar_conta(membro_id: int, nome_conta: str):
    db().table("contas").insert({
        "membro_id": membro_id,
        "nome":      nome_conta.strip(),
    }).execute()


def renomear_conta(conta_id: int, novo_nome: str):
    db().table("contas").update({
        "nome": novo_nome.strip()
    }).eq("id", conta_id).execute()


def excluir_conta(conta_id: int):
    db().table("contas").delete().eq("id", conta_id).execute()
