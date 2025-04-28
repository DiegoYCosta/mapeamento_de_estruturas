import os
import json
import pyperclip
from tkinter import (
    Tk, filedialog, Checkbutton, Button, IntVar,
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
    """Retorna True se 'path' deve ser ignorado, comparando substrings e wildcard '*' no final."""
    for pattern in IGNORED_PATTERNS:
        if pattern.startswith("*"):
            if path.endswith(pattern[1:]):
                return True
        elif pattern in path:
            return True
    return False

def get_directory_structure(path):
    """Retorna dict aninhado com arquivos (None) e pastas (outro dict)."""
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

def show_selection_gui(window, base_path):
    window.title("Seleção de Arquivos")
    window.geometry("600x700")

    state     = load_state()
    abs_base  = os.path.abspath(base_path)
    saved     = set(state.get(abs_base, []))
    # Inicializa save_var com base em se já existe histórico para este caminho
    save_var  = IntVar(master=window, value=1 if abs_base in state else 0)
    vars_dict = {}

    def toggle_visibility(button, frame):
        """Expandir/recolher bloco de itens."""
        if frame.winfo_viewable():
            frame.pack_forget()
            button.config(text="+")
        else:
            frame.pack(fill="x")
            button.config(text="-")

    def update_folder_selection(var, folder_dict):
        """Altera recursivamente seleção de todos os filhos."""
        def toggle(status, d):
            for p, v in d.items():
                if isinstance(v, dict):
                    toggle(status, v)
                else:
                    vars_dict[p].set(status)
        toggle(var.get(), folder_dict)

    def add_items(parent_frame, parent_dict):
        """Adiciona recursivamente checkboxes de arquivos e pastas."""
        files   = [(p, s) for p, s in parent_dict.items() if s is None]
        folders = [(p, s) for p, s in parent_dict.items() if isinstance(s, dict)]

        # Primeiro arquivos
        for path, _ in sorted(files, key=lambda kv: os.path.basename(kv[0]).lower()):
            name = os.path.basename(path)
            var  = IntVar(master=window, value=1 if path in saved else 0)
            vars_dict[path] = var
            Checkbutton(parent_frame, text=name, variable=var).pack(anchor="w", padx=20)

        # Depois pastas
        for path, subtree in sorted(folders, key=lambda kv: os.path.basename(kv[0]).lower()):
            name = os.path.basename(path)
            var  = IntVar(master=window, value=1 if any(p.startswith(path) for p in saved) else 0)
            vars_dict[path] = var

            folder_frame = Frame(parent_frame, bg="#f0f0f0", bd=1, relief="solid")
            folder_frame.pack(fill="x", padx=5, pady=2)

            Checkbutton(
                folder_frame, text=name, variable=var,
                command=lambda v=var, d=subtree: update_folder_selection(v, d),
                bg="#f0f0f0"
            ).pack(side=LEFT, padx=5)

            toggle_btn  = Button(folder_frame, text="-", width=2)
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
        """Gera output.txt, copia ao clipboard e atualiza o histórico conforme save_var."""
        selected = [p for p, v in vars_dict.items() if v.get()]
        out_file = "output.txt"
        try:
            with open(out_file, "w", encoding="utf-8") as out:
                for fp in selected:
                    out.write(f"=== {fp} ===\n")
                    try:
                        with open(fp, "r", encoding="utf-8") as f:
                            out.write(f.read() + "\n\n")
                    except Exception as e:
                        out.write(f"Erro ao ler {fp}: {e}\n\n")
            with open(out_file, "r", encoding="utf-8") as out:
                pyperclip.copy(out.read())

            # Se marcado, salva; caso contrário, remove histórico deste caminho
            if save_var.get():
                state[abs_base] = selected
            else:
                state.pop(abs_base, None)
            save_state(state)

            messagebox.showinfo("Sucesso", "Arquivos copiados para o clipboard!")
        except Exception as e:
            messagebox.showerror("Erro", str(e))
        finally:
            window.destroy()

    # Montagem da UI: Canvas + Scrollbar + itens + botões
    canvas    = Canvas(window)
    scrollbar = Scrollbar(window, orient=VERTICAL, command=canvas.yview)
    scroll_f  = Frame(canvas)
    scroll_f.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scroll_f, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
    canvas.bind_all("<Button-4>",   lambda e: canvas.yview_scroll(-1, "units"))
    canvas.bind_all("<Button-5>",   lambda e: canvas.yview_scroll(1, "units"))

    add_items(scroll_f, get_directory_structure(base_path))

    bottom = Frame(window)
    bottom.pack(fill="x", pady=5)
    Button(bottom, text="Selecionar Tudo", command=select_all).pack(side=LEFT, padx=5)
    Checkbutton(bottom, text="Salvar Seleção", variable=save_var).pack(side=LEFT, padx=5)
    Button(bottom, text="OK", command=map_selected_files).pack(side=RIGHT, padx=5)
    Button(bottom, text="Cancelar", command=window.destroy).pack(side=RIGHT, padx=5)

    canvas.pack(side=LEFT, fill=BOTH, expand=True)
    scrollbar.pack(side=RIGHT, fill=Y)


if __name__ == "__main__":
    root = Tk()
    root.withdraw()  # Oculta enquanto escolhe pasta
    user_path = filedialog.askdirectory(title="Selecione a pasta que deseja mapear")

    if not user_path:
        print("Nenhuma pasta foi selecionada.")
    else:
        root.deiconify()               # Reexibe a janela principal
        show_selection_gui(root, user_path)
        root.mainloop()
