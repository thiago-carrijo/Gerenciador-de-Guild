import tkinter as tk
from tkinter import messagebox, simpledialog
import sqlite3

from database import (
    init_db, buscar,
    adicionar_membro, editar_membro, excluir_membro,
    adicionar_conta, renomear_conta, excluir_conta
)

# ─────────────────────────────────────────────
#  TEMA
# ─────────────────────────────────────────────
CORES = {
    "bg":      "#0f1117",
    "panel":   "#1a1d27",
    "card":    "#22263a",
    "accent":  "#f0a500",
    "text":    "#e8eaf0",
    "muted":   "#7a7f99",
    "danger":  "#e05050",
    "success": "#3ecf8e",
    "border":  "#2d3150",
}

FONT_TITLE = ("Georgia", 18, "bold")
FONT_HEAD  = ("Georgia", 12, "bold")
FONT_BODY  = ("Courier New", 10)
FONT_SMALL = ("Courier New", 9)
FONT_BTN   = ("Georgia", 9, "bold")


# ─────────────────────────────────────────────
#  DIÁLOGO — NOVO MEMBRO
# ─────────────────────────────────────────────
class DialogoMembro(tk.Toplevel):
    """Janela modal para criar um novo membro."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Novo Membro")
        self.configure(bg=CORES["bg"])
        self.resizable(False, False)
        self.grab_set()
        self.resultado = None  # (nome, recrutador, telefone) ou None

        self._build(parent)

    def _build(self, parent):
        pad = {"padx": 20, "pady": 5}

        tk.Label(self, text="NOVO MEMBRO", font=FONT_HEAD,
                 bg=CORES["bg"], fg=CORES["accent"]).pack(pady=(16, 8))

        campos = [
            ("Nome do membro *", "nome"),
        ]
        self._vars = {}
        for label, key in campos:
            tk.Label(self, text=label, font=FONT_SMALL,
                     bg=CORES["bg"], fg=CORES["muted"]).pack(anchor="w", **pad)
            v = tk.StringVar()
            e = tk.Entry(self, textvariable=v, font=FONT_BODY, width=32,
                         bg=CORES["card"], fg=CORES["text"],
                         insertbackground=CORES["accent"], relief="flat", bd=4)
            e.pack(**pad)
            self._vars[key] = v
            if key == "nome":
                e.focus_set()

        # Separador
        tk.Frame(self, bg=CORES["border"], height=1).pack(fill="x", padx=20, pady=8)

        # Botões
        btn_frame = tk.Frame(self, bg=CORES["bg"])
        btn_frame.pack(pady=(0, 16))

        tk.Button(btn_frame, text="✔ Salvar", command=self._salvar,
                  bg=CORES["accent"], fg="#000", font=FONT_BTN,
                  relief="flat", bd=0, padx=14, pady=5, cursor="hand2"
                  ).pack(side="left", padx=6)
        tk.Button(btn_frame, text="✖ Cancelar", command=self.destroy,
                  bg=CORES["card"], fg=CORES["text"], font=FONT_BTN,
                  relief="flat", bd=0, padx=14, pady=5, cursor="hand2"
                  ).pack(side="left", padx=6)

        self.bind("<Return>", lambda _: self._salvar())
        self.bind("<Escape>", lambda _: self.destroy())
        self._centralizar(parent)

    def _centralizar(self, parent):
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _salvar(self):
        nome = self._vars["nome"].get().strip()
        if not nome:
            messagebox.showwarning("Campo obrigatório",
                                   "O nome do membro é obrigatório.", parent=self)
            return
        self.resultado = nome
        self.destroy()


# ─────────────────────────────────────────────
#  APLICAÇÃO PRINCIPAL
# ─────────────────────────────────────────────
class GuildApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("⚔Gerenciador de Guild⚔")
        self.geometry("940x660")
        self.minsize(720, 500)
        self.configure(bg=CORES["bg"])
        self.resizable(True, True)

        init_db()
        self._build_ui()
        self.atualizar()

    # ── Layout principal ──────────────────────
    def _build_ui(self):
        # Cabeçalho
        hdr = tk.Frame(self, bg=CORES["panel"], pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="⚔SENSE⚔", font=FONT_TITLE,
                 bg=CORES["panel"], fg=CORES["accent"]).pack(side="left", padx=20)
        tk.Label(hdr, text="Gerenciador de Membros & Contas", font=FONT_SMALL,
                 bg=CORES["panel"], fg=CORES["muted"]).pack(side="left", padx=4)

        # Barra de pesquisa
        bar = tk.Frame(self, bg=CORES["bg"], pady=8)
        bar.pack(fill="x", padx=16)
        tk.Label(bar, text="🔍", bg=CORES["bg"], fg=CORES["accent"],
                 font=("Arial", 12)).pack(side="left")
        self.var_busca = tk.StringVar()
        self.var_busca.trace_add("write", lambda *_: self.atualizar())
        tk.Entry(bar, textvariable=self.var_busca, font=FONT_BODY,
                 bg=CORES["card"], fg=CORES["text"],
                 insertbackground=CORES["accent"], relief="flat", bd=0
                 ).pack(side="left", fill="x", expand=True, ipady=6, padx=8)
        self._btn(bar, "+ Novo Membro", self.dlg_add_membro,
                  bg=CORES["accent"], fg="#000").pack(side="right", padx=4)

        # Separador
        tk.Frame(self, bg=CORES["border"], height=1).pack(fill="x", padx=16)

        # Corpo
        body = tk.Frame(self, bg=CORES["bg"])
        body.pack(fill="both", expand=True, padx=16, pady=8)

        # Lista de membros (esquerda)
        left = tk.Frame(body, bg=CORES["panel"], width=360)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)
        tk.Label(left, text="MEMBROS", font=FONT_SMALL,
                 bg=CORES["panel"], fg=CORES["muted"]).pack(pady=(10, 4), padx=10, anchor="w")
        lista_frame = tk.Frame(left, bg=CORES["panel"])
        lista_frame.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        sb = tk.Scrollbar(lista_frame, orient="vertical")
        self.listbox = tk.Listbox(
            lista_frame, yscrollcommand=sb.set,
            font=FONT_BODY, bg=CORES["card"], fg=CORES["text"],
            selectbackground=CORES["accent"], selectforeground="#000",
            relief="flat", bd=0, activestyle="none",
            highlightthickness=0, cursor="hand2"
        )
        sb.config(command=self.listbox.yview)
        sb.pack(side="right", fill="y")
        self.listbox.pack(side="left", fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        # Painel de detalhe (direita)
        self.right = tk.Frame(body, bg=CORES["bg"])
        self.right.pack(side="left", fill="both", expand=True)
        self._mostrar_placeholder()

    # ── Widgets auxiliares ────────────────────
    def _btn(self, parent, texto, cmd, bg=None, fg=None, small=False):
        bg  = bg or CORES["card"]
        fg  = fg or CORES["text"]
        fnt = ("Georgia", 8, "bold") if small else FONT_BTN
        return tk.Button(
            parent, text=texto, command=cmd,
            bg=bg, fg=fg,
            activebackground=CORES["accent"], activeforeground="#000",
            font=fnt, relief="flat", bd=0, padx=10, pady=4, cursor="hand2"
        )

    def _label_field(self, parent, label, valor):
        """Linha de rótulo + valor somente leitura com botão editar."""
        row = tk.Frame(parent, bg=CORES["bg"])
        row.pack(fill="x", pady=2)
        tk.Label(row, text=label, font=FONT_SMALL, width=12, anchor="w",
                 bg=CORES["bg"], fg=CORES["muted"]).pack(side="left")
        tk.Label(row, text=valor if valor else "—", font=FONT_BODY,
                 bg=CORES["bg"], fg=CORES["text"] if valor else CORES["muted"]).pack(side="left", padx=4)
        return row

    def _card(self, parent, **kw):
        return tk.Frame(parent, bg=CORES["card"],
                        highlightbackground=CORES["border"],
                        highlightthickness=1, **kw)

    # ── Placeholder ───────────────────────────
    def _mostrar_placeholder(self):
        for w in self.right.winfo_children():
            w.destroy()
        tk.Label(
            self.right,
            text="← Selecione um membro\npara ver detalhes",
            font=FONT_BODY, bg=CORES["bg"], fg=CORES["muted"], justify="center"
        ).place(relx=.5, rely=.5, anchor="center")

    # ── Atualizar lista ───────────────────────
    def atualizar(self):
        self.membros_data = buscar(self.var_busca.get())
        self.listbox.delete(0, "end")
        self._ids_listbox = []
        for mid, info in self.membros_data.items():
            n = len(info["contas"])
            self.listbox.insert("end",
                f"  {info['nome']}  ({n} conta{'s' if n != 1 else ''})")
            self._ids_listbox.append(mid)
        self._mostrar_placeholder()

    # ── Seleção na lista ──────────────────────
    def _on_select(self, _=None):
        sel = self.listbox.curselection()
        if not sel:
            return
        self._mostrar_detalhe(self._ids_listbox[sel[0]])

    # ── Painel de detalhe ─────────────────────
    def _mostrar_detalhe(self, membro_id):
        for w in self.right.winfo_children():
            w.destroy()

        info = self.membros_data.get(membro_id)
        if not info:
            return

        # ── Cabeçalho do membro ──
        top = tk.Frame(self.right, bg=CORES["bg"])
        top.pack(fill="x", pady=(0, 6))
        tk.Label(top, text=f"👤  {info['nome']}", font=FONT_HEAD,
                 bg=CORES["bg"], fg=CORES["accent"]).pack(side="left")
        self._btn(top, "🗑 Excluir Membro",
                  lambda: self.conf_excluir_membro(membro_id, info["nome"]),
                  bg=CORES["danger"], fg="#fff").pack(side="right", padx=4)

        # ── Contas ──
        tk.Label(self.right, text="CONTAS", font=FONT_SMALL,
                 bg=CORES["bg"], fg=CORES["muted"]).pack(anchor="w", pady=(4, 2))

        contas_frame = tk.Frame(self.right, bg=CORES["bg"])
        contas_frame.pack(fill="x")

        canvas = tk.Canvas(contas_frame, bg=CORES["bg"], highlightthickness=0, height=180)
        sb = tk.Scrollbar(contas_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=CORES["bg"])
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        for conta in info["contas"]:
            row = self._card(inner, pady=5, padx=10)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"🎮  {conta['nome']}", font=FONT_BODY,
                     bg=CORES["card"], fg=CORES["text"]).pack(side="left")
            self._btn(row, "✏",
                      lambda cid=conta["id"], cn=conta["nome"]:
                          self.dlg_renomear_conta(cid, cn, membro_id),
                      bg=CORES["panel"], small=True).pack(side="right", padx=2)
            self._btn(row, "🗑",
                      lambda cid=conta["id"]:
                          self.conf_excluir_conta(cid, membro_id),
                      bg=CORES["danger"], fg="#fff", small=True).pack(side="right", padx=2)

        # Botão adicionar conta
        add_conta_row = tk.Frame(self.right, bg=CORES["bg"])
        add_conta_row.pack(fill="x", pady=(4, 10))
        self._btn(add_conta_row, "+ Adicionar Conta",
                  lambda: self.dlg_add_conta(membro_id),
                  bg=CORES["success"], fg="#000").pack(side="left")

        # ── Separador ──
        tk.Frame(self.right, bg=CORES["border"], height=1).pack(fill="x", pady=(0, 10))

        # ── Recrutador e Telefone (campos editáveis inline) ──
        info_frame = tk.Frame(self.right, bg=CORES["bg"])
        info_frame.pack(fill="x")

        # Recrutador
        tk.Label(info_frame, text="RECRUTADOR", font=FONT_SMALL,
                 bg=CORES["bg"], fg=CORES["muted"]).pack(anchor="w", pady=(0, 2))
        rec_row = tk.Frame(info_frame, bg=CORES["bg"])
        rec_row.pack(fill="x", pady=(0, 8))
        var_rec = tk.StringVar(value=info["recrutador"])
        tk.Entry(rec_row, textvariable=var_rec, font=FONT_BODY,
                 bg=CORES["card"], fg=CORES["text"],
                 insertbackground=CORES["accent"], relief="flat", bd=4
                 ).pack(side="left", fill="x", expand=True, ipady=4)

        # Telefone
        tk.Label(info_frame, text="TELEFONE", font=FONT_SMALL,
                 bg=CORES["bg"], fg=CORES["muted"]).pack(anchor="w", pady=(0, 2))
        tel_row = tk.Frame(info_frame, bg=CORES["bg"])
        tel_row.pack(fill="x", pady=(0, 10))
        var_tel = tk.StringVar(value=info["telefone"])
        tk.Entry(tel_row, textvariable=var_tel, font=FONT_BODY,
                 bg=CORES["card"], fg=CORES["text"],
                 insertbackground=CORES["accent"], relief="flat", bd=4
                 ).pack(side="left", fill="x", expand=True, ipady=4)

        # Botões Salvar / Renomear membro
        acoes_row = tk.Frame(self.right, bg=CORES["bg"])
        acoes_row.pack(fill="x", pady=(0, 6))

        def salvar_info():
            novo_nome = info["nome"]  # nome não muda por aqui
            try:
                editar_membro(membro_id, novo_nome,
                              var_rec.get(), var_tel.get())
                self.atualizar()
                # Re-selecionar o membro
                if membro_id in self.membros_data:
                    idx = list(self.membros_data.keys()).index(membro_id)
                    self.listbox.selection_set(idx)
                    self._mostrar_detalhe(membro_id)
            except Exception as e:
                messagebox.showerror("Erro", str(e))

        self._btn(acoes_row, "💾 Salvar Informações", salvar_info,
                  bg=CORES["accent"], fg="#000").pack(side="left", padx=(0, 8))
        self._btn(acoes_row, "✏ Renomear Membro",
                  lambda: self.dlg_renomear_membro(membro_id, info["nome"]),
                  bg=CORES["card"]).pack(side="left")

    # ── Diálogos ──────────────────────────────
    def dlg_add_membro(self):
        dlg = DialogoMembro(self)
        self.wait_window(dlg)
        if dlg.resultado:
            try:
                adicionar_membro(dlg.resultado)
                self.atualizar()
            except sqlite3.IntegrityError:
                messagebox.showerror("Erro",
                    f"Já existe um membro com o nome '{dlg.resultado}'.")

    def dlg_renomear_membro(self, mid, nome_atual):
        novo = simpledialog.askstring("Renomear Membro", "Novo nome:",
                                      initialvalue=nome_atual, parent=self)
        if not novo or not novo.strip() or novo.strip() == nome_atual:
            return
        try:
            # Preserva recrutador e telefone ao renomear
            info = self.membros_data.get(mid, {})
            editar_membro(mid, novo, info.get("recrutador", ""), info.get("telefone", ""))
            self.atualizar()
            if mid in self.membros_data:
                idx = list(self.membros_data.keys()).index(mid)
                self.listbox.selection_set(idx)
                self._mostrar_detalhe(mid)
        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", f"Já existe um membro com o nome '{novo}'.")

    def conf_excluir_membro(self, mid, nome):
        ok = messagebox.askyesno(
            "Excluir Membro",
            f"Excluir '{nome}' e todas as suas contas?\nEssa ação não pode ser desfeita."
        )
        if ok:
            excluir_membro(mid)
            self.atualizar()

    def dlg_add_conta(self, mid):
        nome = simpledialog.askstring("Nova Conta", "Nome da conta:", parent=self)
        if not nome or not nome.strip():
            return
        adicionar_conta(mid, nome)
        self.atualizar()
        self._mostrar_detalhe(mid)

    def dlg_renomear_conta(self, cid, nome_atual, mid):
        novo = simpledialog.askstring("Renomear Conta", "Novo nome:",
                                      initialvalue=nome_atual, parent=self)
        if not novo or not novo.strip() or novo.strip() == nome_atual:
            return
        renomear_conta(cid, novo)
        self.atualizar()
        self._mostrar_detalhe(mid)

    def conf_excluir_conta(self, cid, mid):
        ok = messagebox.askyesno("Excluir Conta", "Excluir esta conta?")
        if ok:
            excluir_conta(cid)
            self.atualizar()
            self._mostrar_detalhe(mid)


# ─────────────────────────────────────────────
#  Diálogo de novo membro (apenas nome)
# ─────────────────────────────────────────────
class DialogoMembro(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Novo Membro")
        self.configure(bg=CORES["bg"])
        self.resizable(False, False)
        self.grab_set()
        self.resultado = None

        pad = {"padx": 20, "pady": 6}
        tk.Label(self, text="NOVO MEMBRO", font=FONT_HEAD,
                 bg=CORES["bg"], fg=CORES["accent"]).pack(pady=(16, 8))
        tk.Label(self, text="Nome do membro *", font=FONT_SMALL,
                 bg=CORES["bg"], fg=CORES["muted"]).pack(anchor="w", **pad)
        self.var_nome = tk.StringVar()
        e = tk.Entry(self, textvariable=self.var_nome, font=FONT_BODY, width=32,
                     bg=CORES["card"], fg=CORES["text"],
                     insertbackground=CORES["accent"], relief="flat", bd=4)
        e.pack(**pad)
        e.focus_set()

        tk.Frame(self, bg=CORES["border"], height=1).pack(fill="x", padx=20, pady=8)

        btn_frame = tk.Frame(self, bg=CORES["bg"])
        btn_frame.pack(pady=(0, 16))
        tk.Button(btn_frame, text="✔ Salvar", command=self._salvar,
                  bg=CORES["accent"], fg="#000", font=FONT_BTN,
                  relief="flat", bd=0, padx=14, pady=5, cursor="hand2"
                  ).pack(side="left", padx=6)
        tk.Button(btn_frame, text="✖ Cancelar", command=self.destroy,
                  bg=CORES["card"], fg=CORES["text"], font=FONT_BTN,
                  relief="flat", bd=0, padx=14, pady=5, cursor="hand2"
                  ).pack(side="left", padx=6)

        self.bind("<Return>", lambda _: self._salvar())
        self.bind("<Escape>", lambda _: self.destroy())
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _salvar(self):
        nome = self.var_nome.get().strip()
        if not nome:
            messagebox.showwarning("Campo obrigatório",
                                   "O nome do membro é obrigatório.", parent=self)
            return
        self.resultado = nome
        self.destroy()
