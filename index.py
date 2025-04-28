import os
import json
import pyperclip
from tkinter import (
    Tk, filedialog, Toplevel, Checkbutton, Button, IntVar,
    Scrollbar, Canvas, Frame, VERTICAL, BOTH, RIGHT, LEFT, Y, messagebox
)

# Padrões de arquivos/pastas a ignorar
IGNORED_PATTERNS = [
 ".git", "node_modules", "__pycache__", ".DS_Store", ".vscode", "*.pyc", "*.pyo", "*.exe",
    "*.dll", "*.so", "*.dylib", "*.log", "*.tmp", "*.swp", "*.swo", "*.bak", ".idea", "*.class",
    "*.jar", "*.war", "*.zip", "*.tar", "*.gz", "*.7z", "*.rar", "dist", "build", "*.egg-info",
    "env", ".env", "venv", ".coverage", ".pytest_cache", ".mypy_cache", "coverage.xml", ".gradle", ".next",
    ".nuxt", ".yarn", "yarn.lock", "package-lock.json", "*.lock", "Thumbs.db", ".sass-cache", ".cache"
]

# Arquivo para salvar e carregar seleções
STATE_FILE = "selection_state.json"


def load_state():
    """Carrega seleções salvas de STATE_FILE."""
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state):
    """Salva dict de seleções em STATE_FILE."""
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Erro ao salvar estado: {e}")


def should_ignore(path):
    """
    Retorna True se 'path' deve ser ignorado,
    comparando substrings e wildcard '*' no final.
    """
    for pattern in IGNORED_PATTERNS:
        if pattern.startswith("*"):
            if path.endswith(pattern[1:]):
                return True
        elif pattern in path:
            return True
    return False


def get_directory_structure(path):
    """
    Retorna um dict aninhado onde cada chave é um caminho absoluto
    e o valor é None (arquivo) ou outro dict (pasta).
    """
    structure = {}
    try:
        for name in sorted(os.listdir(path), key=str.lower):
            full = os.path.join(path, name)
            if should_ignore(full):
                continue
            if os.path.isdir(full):
                structure[full] = get_directory_structure(full)
            else:
                structure[full] = None
    except PermissionError:
        pass
    return structure


def show_selection_gui(base_path):
    # Cria janela antes de IntVar para evitar erros de "nenhum root"
    window = Toplevel()
    window.title("Seleção de Arquivos")
    window.geometry("600x700")

    # Carrega estado prévio e selecionados para esta pasta
    state = load_state()
    abs_base = os.path.abspath(base_path)
    saved = set(state.get(abs_base, []))

    # Variável para salvar seleção
    save_var = IntVar(master=window, value=1)

    # Funções auxiliares
    def toggle_visibility(button, frame):
        """Expandir/recolher bloco de itens (não usado ativamente)."""
        if frame.winfo_viewable():
            frame.pack_forget()
            button.config(text="+")
        else:
            frame.pack(fill="x")
            button.config(text="-")

    def update_folder_selection(var, folder_dict):
        """
        Quando a checkbox de uma pasta for alternada,
        ajusta todos os arquivos-filho para o mesmo estado.
        """
        def toggle(status, d):
            for p, v in d.items():
                if isinstance(v, dict):
                    toggle(status, v)
                else:
                    vars_dict[p].set(status)
        toggle(var.get(), folder_dict)

    def add_items(parent_frame, parent_dict):
        """
        Adiciona recursivamente checkboxes de arquivos e pastas
        em parent_frame, mostrando primeiro arquivos (prioridade no topo),
        depois pastas.
        """
        # lista de (path, subtree)
        files   = [(p, s) for p, s in parent_dict.items() if s is None]
        folders = [(p, s) for p, s in parent_dict.items() if isinstance(s, dict)]

        # Primeiro, os arquivos
        for path, _ in sorted(files, key=lambda kv: os.path.basename(kv[0]).lower()):
            name = os.path.basename(path)
            file_var = IntVar(master=window, value=1 if path in saved else 0)
            vars_dict[path] = file_var
            file_cb = Checkbutton(parent_frame, text=name, variable=file_var)
            file_cb.pack(anchor="w", padx=20)

        # Depois, as pastas
        for path, subtree in sorted(folders, key=lambda kv: os.path.basename(kv[0]).lower()):
            name = os.path.basename(path)
            folder_var = IntVar(master=window, value=1 if any(p.startswith(path) for p in saved) else 0)
            vars_dict[path] = folder_var

            folder_frame = Frame(parent_frame, bg="#f0f0f0", bd=1, relief="solid")
            folder_frame.pack(fill="x", padx=5, pady=2)

            folder_cb = Checkbutton(
                folder_frame, text=name, variable=folder_var,
                command=lambda v=folder_var, d=subtree: update_folder_selection(v, d),
                bg="#f0f0f0"
            )
            folder_cb.pack(side=LEFT, padx=5)

            toggle_btn = Button(folder_frame, text="-", width=2)
            child_frame = Frame(parent_frame)
            child_frame.pack(fill="x", padx=10)
            toggle_btn.config(command=lambda b=toggle_btn, f=child_frame: toggle_visibility(b, f))
            toggle_btn.pack(side=RIGHT, padx=5)

            add_items(child_frame, subtree)

    def select_all():
        """Marca todos os arquivos/pastas."""
        for var in vars_dict.values():
            var.set(1)

    def map_selected_files():
        """Gera output.txt, copia ao clipboard e salva estado se solicitado."""
        selected_files = [p for p, v in vars_dict.items() if v.get()]

        output_file = "output.txt"
        try:
            with open(output_file, "w", encoding="utf-8") as out:
                for fp in selected_files:
                    out.write(f"=== {fp} ===\n")
                    try:
                        with open(fp, "r", encoding="utf-8") as f:
                            out.write(f.read() + "\n\n")
                    except Exception as e:
                        out.write(f"Erro ao ler {fp}: {e}\n\n")
            # Copia ao clipboard
            with open(output_file, "r", encoding="utf-8") as out:
                pyperclip.copy(out.read())
            # Salva estado se marcado
            if save_var.get():
                state[abs_base] = selected_files
                save_state(state)
            messagebox.showinfo("Sucesso", "Arquivos copiados para o clipboard!")
        except Exception as e:
            messagebox.showerror("Erro", str(e))
        finally:
            window.destroy()

    # Canvas + Scrollbar
    canvas = Canvas(window)
    scrollbar = Scrollbar(window, orient=VERTICAL, command=canvas.yview)
    scrollable_frame = Frame(canvas)
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Rolar com a roda do mouse
    canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
    canvas.bind_all("<Button-4>",   lambda e: canvas.yview_scroll(-1, "units"))
    canvas.bind_all("<Button-5>",   lambda e: canvas.yview_scroll(1, "units"))

    # Monta árvore de seleção
    structure = get_directory_structure(base_path)
    vars_dict = {}
    add_items(scrollable_frame, structure)

    # Botões inferiores
    bottom = Frame(window)
    bottom.pack(fill="x", pady=5)
    Button(bottom, text="Selecionar Tudo", command=select_all).pack(side=LEFT, padx=5)
    Checkbutton(bottom, text="Salvar Seleção", variable=save_var).pack(side=LEFT, padx=5)
    Button(bottom, text="OK",      command=map_selected_files).pack(side=RIGHT, padx=5)
    Button(bottom, text="Cancelar",command=window.destroy).pack(side=RIGHT, padx=5)

    # Exibe tudo
    canvas.pack(side=LEFT, fill=BOTH, expand=True)
    scrollbar.pack(side=RIGHT, fill=Y)
    window.mainloop()


if __name__ == "__main__":
    root = Tk()
    root.withdraw()
    user_path = filedialog.askdirectory(title="Selecione a pasta que deseja mapear")
    if user_path:
        show_selection_gui(user_path)
    else:
        print("Nenhuma pasta foi selecionada.")
