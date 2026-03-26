import streamlit as st
from supabase import create_client, Client
import hashlib
from datetime import datetime


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
#  LOG DE AUDITORIA
# ─────────────────────────────────────────────
def registrar_log(usuario: str, acao: str, detalhe: str):
    """Registra uma ação no histórico. Nunca lança exceção para não bloquear o fluxo."""
    try:
        db().table("historico").insert({
            "usuario": usuario,
            "acao":    acao,
            "detalhe": detalhe,
        }).execute()
    except Exception:
        pass


def buscar_historico() -> list:
    res = db().table("historico") \
        .select("*") \
        .order("criado_em", desc=True) \
        .limit(500) \
        .execute()
    return res.data


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


def adicionar_membro(nome: str, recrutador: str = "", telefone: str = "", usuario: str = ""):
    db().table("membros").insert({
        "nome":       nome.strip(),
        "recrutador": recrutador.strip(),
        "telefone":   telefone.strip(),
    }).execute()
    registrar_log(usuario, "Adicionou membro", f"Membro: {nome.strip()}")


def editar_membro(membro_id: int, nome_antigo: str, nome: str,
                  recrutador: str = "", telefone: str = "", usuario: str = ""):
    db().table("membros").update({
        "nome":       nome.strip(),
        "recrutador": recrutador.strip(),
        "telefone":   telefone.strip(),
    }).eq("id", membro_id).execute()

    if nome.strip() != nome_antigo.strip():
        detalhe = f"Membro renomeado: {nome_antigo} → {nome.strip()}"
    else:
        detalhe = f"Informações editadas do membro: {nome.strip()}"
    registrar_log(usuario, "Editou membro", detalhe)


def excluir_membro(membro_id: int, nome: str = "", usuario: str = ""):
    # Primeiro, deletar todas as contas associadas ao membro
    db().table("contas").delete().eq("membro_id", membro_id).execute()
    # Depois, deletar o membro
    db().table("membros").delete().eq("id", membro_id).execute()
    registrar_log(usuario, "Excluiu membro", f"Membro: {nome}")


# ─────────────────────────────────────────────
#  CONTAS
# ─────────────────────────────────────────────
def adicionar_conta(membro_id: int, nome_conta: str,
                    nome_membro: str = "", usuario: str = ""):
    db().table("contas").insert({
        "membro_id": membro_id,
        "nome":      nome_conta.strip(),
    }).execute()
    registrar_log(usuario, "Adicionou conta",
                  f"Conta: {nome_conta.strip()} → Membro: {nome_membro}")


def renomear_conta(conta_id: int, nome_antigo: str, novo_nome: str,
                   nome_membro: str = "", usuario: str = ""):
    db().table("contas").update({
        "nome": novo_nome.strip()
    }).eq("id", conta_id).execute()
    registrar_log(usuario, "Renomeou conta",
                  f"{nome_antigo} → {novo_nome.strip()} (Membro: {nome_membro})")


def excluir_conta(conta_id: int, nome_conta: str = "",
                  nome_membro: str = "", usuario: str = ""):
    db().table("contas").delete().eq("id", conta_id).execute()
    registrar_log(usuario, "Excluiu conta",
                  f"Conta: {nome_conta} (Membro: {nome_membro})")
