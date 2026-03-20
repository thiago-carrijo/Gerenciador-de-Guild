import streamlit as st
from database import (
    verificar_login,
    buscar,
    adicionar_membro, editar_membro, excluir_membro,
    adicionar_conta, renomear_conta, excluir_conta,
)

# ─────────────────────────────────────────────
#  CONFIGURAÇÃO
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Guild MucaBrasil",
    page_icon="⚔️",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&family=Share+Tech+Mono&display=swap');

html, body, [class*="css"], .stApp {
    background-color: #0f1117 !important;
    color: #e8eaf0 !important;
}

h1, h2, h3 {
    font-family: 'Cinzel', serif !important;
    color: #f0a500 !important;
}

.stTextInput > label, .stTextArea > label {
    color: #7a7f99 !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.stTextInput > div > input {
    background-color: #22263a !important;
    color: #e8eaf0 !important;
    border: 1px solid #2d3150 !important;
    border-radius: 4px !important;
}

.stTextInput > div > input:focus {
    border-color: #f0a500 !important;
    box-shadow: 0 0 0 1px #f0a500 !important;
}

div[data-testid="stExpander"] {
    background-color: #1a1d27 !important;
    border: 1px solid #2d3150 !important;
    border-radius: 2px !important;
    margin-bottom: 2px;
}

div[data-testid="stExpander"] summary {
    font-family: 'Share Tech Mono', monospace !important;
    color: #e8eaf0 !important;
}

.stButton > button {
    font-family: 'Cinzel', serif !important;
    font-size: 0.8rem !important;
    border-radius: 4px !important;
    border: none !important;
    transition: opacity 0.2s;
}

.stButton > button:hover {
    opacity: 0.85;
}

.card-conta {
    background-color: #22263a;
    border: 1px solid #2d3150;
    border-radius: 6px;
    padding: 10px 14px;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-family: 'Share Tech Mono', monospace;
}

.badge {
    background-color: #2d3150;
    color: #7a7f99;
    border-radius: 12px;
    padding: 2px 10px;
    font-size: 0.75rem;
    font-family: 'Share Tech Mono', monospace;
}

.info-label {
    color: #7a7f99;
    font-size: 0.75rem;
    font-family: 'Share Tech Mono', monospace;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 2px;
}

.info-value {
    color: #e8eaf0;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.95rem;
    margin-bottom: 10px;
}

hr {
    border-color: #2d3150 !important;
}

.login-box {
    max-width: 400px;
    margin: 80px auto;
    background-color: #1a1d27;
    border: 1px solid #2d3150;
    border-radius: 12px;
    padding: 40px;
}

.stAlert {
    border-radius: 6px !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  ESTADO DE SESSÃO
# ─────────────────────────────────────────────
if "logado" not in st.session_state:
    st.session_state.logado = False
if "membro_selecionado" not in st.session_state:
    st.session_state.membro_selecionado = None
if "modo_edicao" not in st.session_state:
    st.session_state.modo_edicao = None


# ─────────────────────────────────────────────
#  TELA DE LOGIN
# ─────────────────────────────────────────────
def tela_login():
    st.markdown("<div class='login-box'>", unsafe_allow_html=True)
    st.markdown("## ⚔ SENSE")
    st.markdown("<p style='color:#7a7f99;font-family:monospace'>Gerenciador de Guild</p>",
                unsafe_allow_html=True)
    st.markdown("---")

    login = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar", use_container_width=True, type="primary"):
        if verificar_login(login, senha):
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")

    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  TELA PRINCIPAL
# ─────────────────────────────────────────────
def tela_principal():
    # ── Cabeçalho ──
    col_title, col_logout = st.columns([6, 1])
    with col_title:
        st.markdown("## ⚔ Gerenciador de Guild")
    with col_logout:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Sair", use_container_width=True):
            st.session_state.logado = False
            st.session_state.membro_selecionado = None
            st.rerun()

    st.markdown("---")

    # ── Barra de busca + botão novo membro ──
    col_busca, col_btn = st.columns([4, 1])
    with col_busca:
        termo = st.text_input("🔍 Pesquisar por nome do membro ou conta",
                              placeholder="Digite para filtrar...")
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Novo Membro", use_container_width=True, type="primary"):
            st.session_state.modo_edicao = "novo_membro"
            st.session_state.membro_selecionado = None

    st.markdown("---")

    # ── Carrega dados ──
    membros = buscar(termo)

    # ── Layout: lista (esq) | detalhe (dir) ──
    col_lista, col_detalhe = st.columns([1, 2], gap="large")

    # ── Coluna esquerda: lista de membros ──
    with col_lista:
        st.markdown(f"<p class='info-label'>Membros ({len(membros)})</p>",
                    unsafe_allow_html=True)

        if not membros:
            st.markdown("<p style='color:#7a7f99;font-family:monospace'>Nenhum membro encontrado.</p>",
                        unsafe_allow_html=True)
        for m in membros:
            n = len(m["contas"])
            label = f"👤 {m['nome']}  —  {n} conta{'s' if n != 1 else ''}"
            selecionado = st.session_state.membro_selecionado == m["id"]
            if st.button(label, key=f"sel_{m['id']}",
                         use_container_width=True,
                         type="primary" if selecionado else "secondary"):
                st.session_state.membro_selecionado = m["id"]
                st.session_state.modo_edicao = "ver"
                st.rerun()

    # ── Coluna direita: detalhe / formulários ──
    with col_detalhe:

        # ── Formulário: novo membro ──
        if st.session_state.modo_edicao == "novo_membro":
            st.markdown("### Novo Membro")
            with st.form("form_novo_membro"):
                nome       = st.text_input("Nome do membro *")
                recrutador = st.text_input("Recrutador")
                telefone   = st.text_input("Telefone")
                col_s, col_c = st.columns(2)
                salvar    = col_s.form_submit_button("💾 Salvar", type="primary", use_container_width=True)
                cancelar  = col_c.form_submit_button("✖ Cancelar", use_container_width=True)

            if salvar:
                if not nome.strip():
                    st.error("O nome do membro é obrigatório.")
                else:
                    try:
                        adicionar_membro(nome, recrutador, telefone)
                        st.success(f"Membro '{nome}' adicionado!")
                        st.session_state.modo_edicao = None
                        st.rerun()
                    except Exception:
                        st.error(f"Já existe um membro com o nome '{nome}'.")
            if cancelar:
                st.session_state.modo_edicao = None
                st.rerun()

        # ── Detalhe do membro selecionado ──
        elif st.session_state.membro_selecionado and st.session_state.modo_edicao in ("ver", None):
            mid = st.session_state.membro_selecionado
            info = next((m for m in membros if m["id"] == mid), None)

            if not info:
                st.info("Selecione um membro na lista.")
            else:
                # Cabeçalho
                col_h, col_excluir = st.columns([3, 1])
                with col_h:
                    st.markdown(f"### 👤 {info['nome']}")
                with col_excluir:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🗑 Excluir Membro", use_container_width=True):
                        st.session_state.modo_edicao = "confirmar_excluir"
                        st.rerun()

                # Confirmação de exclusão
                if st.session_state.modo_edicao == "confirmar_excluir":
                    st.warning(f"Tem certeza que deseja excluir **{info['nome']}** e todas as suas contas?")
                    col_sim, col_nao = st.columns(2)
                    if col_sim.button("✔ Sim, excluir", type="primary", use_container_width=True):
                        excluir_membro(mid)
                        st.session_state.membro_selecionado = None
                        st.session_state.modo_edicao = None
                        st.rerun()
                    if col_nao.button("✖ Cancelar", use_container_width=True):
                        st.session_state.modo_edicao = "ver"
                        st.rerun()
                    st.stop()

                # ── Contas ──
                st.markdown("---")
                st.markdown("<p class='info-label'>Contas</p>", unsafe_allow_html=True)

                if not info["contas"]:
                    st.markdown("<p style='color:#7a7f99;font-family:monospace'>Nenhuma conta cadastrada.</p>",
                                unsafe_allow_html=True)

                for conta in info["contas"]:
                    with st.expander(f"🎮  {conta['nome']}"):
                        col_e, col_d = st.columns(2)
                        novo_nome_conta = col_e.text_input(
                            "Novo nome", value=conta["nome"],
                            key=f"rename_input_{conta['id']}"
                        )
                        col_e2, col_d2 = st.columns(2)
                        if col_e2.button("✏ Salvar", key=f"rename_{conta['id']}",
                                         use_container_width=True, type="primary"):
                            if novo_nome_conta.strip():
                                renomear_conta(conta["id"], novo_nome_conta)
                                st.rerun()
                        if col_d2.button("🗑 Excluir", key=f"del_conta_{conta['id']}",
                                          use_container_width=True):
                            excluir_conta(conta["id"])
                            st.rerun()

                # Adicionar conta
                with st.expander("➕ Adicionar nova conta"):
                    nova_conta = st.text_input("Nome da conta", key="nova_conta_input")
                    if st.button("Adicionar", type="primary", key="btn_add_conta"):
                        if nova_conta.strip():
                            adicionar_conta(mid, nova_conta)
                            st.rerun()
                        else:
                            st.error("Digite um nome para a conta.")

                # ── Recrutador e Telefone ──
                st.markdown("---")
                st.markdown("<p class='info-label'>Informações do Membro</p>",
                            unsafe_allow_html=True)

                with st.form(f"form_editar_{mid}"):
                    novo_nome  = st.text_input("Nome do membro *", value=info["nome"])
                    recrutador = st.text_input("Recrutador", value=info.get("recrutador", ""))
                    telefone   = st.text_input("Telefone",   value=info.get("telefone",   ""))
                    if st.form_submit_button("💾 Salvar Informações", type="primary",
                                             use_container_width=True):
                        if not novo_nome.strip():
                            st.error("O nome do membro é obrigatório.")
                        else:
                            try:
                                editar_membro(mid, novo_nome, recrutador, telefone)
                                st.success("Informações salvas!")
                                st.rerun()
                            except Exception:
                                st.error(f"Já existe um membro com o nome '{novo_nome}'.")

        else:
            st.markdown("<p style='color:#7a7f99;font-family:monospace;margin-top:40px'>"
                        "← Selecione um membro para ver os detalhes.</p>",
                        unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  ROTEAMENTO
# ─────────────────────────────────────────────
if st.session_state.logado:
    tela_principal()
else:
    tela_login()
