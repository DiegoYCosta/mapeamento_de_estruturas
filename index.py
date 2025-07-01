import os
import json
import pyperclip
from datetime import datetime
import tkinter as tk
from tkinter import (
    Tk, filedialog, Checkbutton, Button, IntVar,
    Scrollbar, Canvas, Frame, VERTICAL, BOTH, RIGHT, LEFT, Y, messagebox, simpledialog
)

def show_toast(window, msg, duration=2000):
    toast = tk.Toplevel(window)
    toast.overrideredirect(True)
    toast.attributes("-topmost", True)
    # Calcula posição no centro inferior da janela principal
    window.update_idletasks()
    x = window.winfo_rootx() + (window.winfo_width() // 2) - 100
    y = window.winfo_rooty() + window.winfo_height() - 80
    toast.geometry(f"350x40+{x}+{y}")
    label = tk.Label(toast, text=msg, bg="#444", fg="white", font=("Segoe UI", 11), bd=2, relief="solid")
    label.pack(fill=BOTH, expand=True)
    toast.after(duration, toast.destroy)

IGNORED_FILE = "never_select.json"
IGNORED_PATTERNS = [
    ".git", "node_modules", "__pycache__", ".DS_Store", ".vscode", "*.pyc", "*.pyo", "*.exe",
    "*.dll", "*.so", "*.dylib", "*.log","*.db", "*.tmp", "*.swp", "*.swo", "*.bak", ".idea", "*.class",
    "*.jar", "*.war", "*.zip", "*.tar", "*.gz", "*.7z", "*.rar", "dist", "build", "*.egg-info",
    "env", ".env", "venv", ".coverage", ".pytest_cache", ".mypy_cache", "coverage.xml", ".gradle", ".next",
    ".nuxt", ".yarn", "yarn.lock", "package-lock.json", "*.lock", "Thumbs.db", ".sass-cache", ".cache"
]

HISTORY_FILE = "selection_state.json"
MAX_HISTORY = 30

def load_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("history", [])
    except Exception:
        return []

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump({"history": history[:MAX_HISTORY]}, f, indent=2, ensure_ascii=False)

def add_or_update_history(history, path, selected, name=None):
    # Remove duplicata pelo path
    for i, entry in enumerate(history):
        if os.path.normcase(entry['path']) == os.path.normcase(path):
            # Atualiza seleção e data se já existir
            entry['selected'] = selected
            entry['saved_at'] = datetime.now().isoformat()
            if name:
                entry['name'] = name
            # Move para o topo
            history.insert(0, history.pop(i))
            break
    else:
        # Adiciona novo no topo
        history.insert(0, {
            "path": path,
            "selected": selected,
            "saved_at": datetime.now().isoformat(),
            "name": name or os.path.basename(path) or "Histórico"
        })
    # Limita tamanho do histórico
    del history[MAX_HISTORY:]
    return history

class ToolTip(object):
    def __init__(self, widget, text=''):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.showtip)
        widget.bind("<Leave>", self.hidetip)

    def showtip(self, event=None):
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 1
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self, event=None):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

def rename_item(listbox, index, history):
    old_name = history[index]['name']
    new_name = simpledialog.askstring(
        "Renomear",
        "Informe novo nome (máx 30 caracteres):",
        initialvalue=old_name)
    if new_name:
        new_name = new_name.strip()[:30]
        history[index]['name'] = new_name
        save_history(history)
        listbox.delete(index)
        listbox.insert(index, new_name)

def create_history_listbox(parent, history):
    listbox = tk.Listbox(parent, font=("Segoe UI", 11), height=15)
    listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    for entry in history:
        display_name = entry.get("name") or os.path.basename(entry.get("path") or "") or "Nenhuma pasta"
        listbox.insert(tk.END, display_name)

    def on_motion(event):
        idx = listbox.nearest(event.y)
        if 0 <= idx < len(history):
            path = history[idx]['path']
            tip_text = path if path else "Nenhuma pasta associada"
            if not hasattr(listbox, 'tooltip') or listbox.tooltip.text != tip_text:
                if hasattr(listbox, 'tooltip') and listbox.tooltip:
                    listbox.tooltip.hidetip()
                listbox.tooltip = ToolTip(listbox, tip_text)
                listbox.tooltip.showtip()
    def on_leave(event):
        if hasattr(listbox, 'tooltip') and listbox.tooltip:
            listbox.tooltip.hidetip()

    listbox.bind("<Motion>", on_motion)
    listbox.bind("<Leave>", on_leave)
    def on_rename(event):
        idx = listbox.nearest(event.y)
        # Busca o histórico atualizado (sempre sincronizado)
        hist = load_history()
        if 0 <= idx < len(hist):
            rename_item(listbox, idx, hist)
            # Após renomear, atualiza o listbox inteiro para evitar mismatch
            listbox.delete(0, tk.END)
            for entry in hist:
                display_name = entry.get("name") or os.path.basename(entry.get("path") or "") or "Nenhuma pasta"
                listbox.insert(tk.END, display_name)
    listbox.bind("<Double-Button-1>", on_rename)

    return listbox

def load_ignored_patterns():
    try:
        with open(IGNORED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return IGNORED_PATTERNS  + [p for p in data if p not in IGNORED_PATTERNS ]
    except Exception:
        return IGNORED_PATTERNS 

def should_ignore(path):
    patterns = load_ignored_patterns()
    for pattern in patterns:
        if pattern.startswith("*") and path.endswith(pattern[1:]):
            return True
        elif pattern in path:
            return True
    return False
def get_directory_structure(path):
    structure = {}
    try:
        for name in sorted(os.listdir(path), key=str.lower):
            full = os.path.join(path, name)
            if should_ignore(full): continue
            if os.path.isdir(full):
                structure[full] = get_directory_structure(full)
            else:
                structure[full] = None
    except PermissionError:
        pass
    return structure

def show_selection_gui(window, base_path, saved_selection=None):
    window.title("Seleção de Arquivos")
    window.geometry("900x700")
    window.resizable(True, True)

    abs_base = os.path.abspath(base_path)

    left_frame = Frame(window)
    left_frame.pack(side=tk.LEFT, fill=BOTH, expand=True)

    right_frame = Frame(window, width=280, bg="#f8f8f8", bd=1, relief="solid")
    right_frame.pack(side=tk.RIGHT, fill=Y)

    history = load_history()
    hist_listbox = create_history_listbox(right_frame, history)
    current_path = abs_base
    current_saved = set(saved_selection or [])

    vars_dict = {}

    bottom = Frame(left_frame)
    bottom.pack(fill="x", pady=5)

    # save_checkbox = Checkbutton(bottom, text="Salvar Seleção (histórico é automático)")
    # save_checkbox.pack(side=LEFT, padx=5)
    # save_checkbox.config(state="disabled")

    def refresh_hist_listbox():
        nonlocal history
        hist_listbox.delete(0, tk.END)
        history = load_history()
        for entry in history:
            display_name = entry.get("name") or os.path.basename(entry.get("path") or "") or "Nenhuma pasta"
            hist_listbox.insert(tk.END, display_name)

    def load_selection(path, saved):
        nonlocal current_path, current_saved, vars_dict
        current_path = path
        current_saved = set(saved or [])
        for widget in left_frame.winfo_children():
            if widget != bottom: widget.destroy()
        vars_dict.clear()

        canvas = Canvas(left_frame)
        scrollbar = Scrollbar(left_frame, orient=VERTICAL, command=canvas.yview)
        scroll_f = Frame(canvas)
        scroll_f.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_f, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Suporte ao scroll do mouse (Windows, Linux, Mac)
        def _on_mousewheel(event):
            if event.num == 4 or event.delta > 0:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5 or event.delta < 0:
                canvas.yview_scroll(1, "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)      # Windows/Mac
        canvas.bind_all("<Button-4>", _on_mousewheel)        # Linux scroll up
        canvas.bind_all("<Button-5>", _on_mousewheel)        # Linux scroll down


        def toggle_visibility(button, frame):
            if frame.winfo_viewable():
                frame.pack_forget()
                button.config(text="+")
            else:
                frame.pack(fill="x")
                button.config(text="-")

        def update_folder_selection(var, folder_dict):
            def toggle(status, d):
                for p, v in d.items():
                    if isinstance(v, dict): toggle(status, v)
                    else: vars_dict[p].set(status)
            toggle(var.get(), folder_dict)

        def add_items(parent_frame, parent_dict, level=0):
            files = [(p, s) for p, s in parent_dict.items() if s is None]
            folders = [(p, s) for p, s in parent_dict.items() if isinstance(s, dict)]
            for path, _ in sorted(files, key=lambda kv: os.path.basename(kv[0]).lower()):
                name = os.path.basename(path)
                var = IntVar(master=window, value=1 if path in current_saved else 0)
                vars_dict[path] = var
                Checkbutton(
                    parent_frame,
                    text=name,
                    variable=var
                ).pack(anchor="w", padx=20)
            for path, subtree in sorted(folders, key=lambda kv: os.path.basename(kv[0]).lower()):
                name = os.path.basename(path)
                var = IntVar(master=window, value=1 if any(p.startswith(path) for p in current_saved) else 0)
                vars_dict[path] = var
                folder_frame = Frame(parent_frame, bg="#e0e3f1" if level % 2 == 0 else "#e6d7d7", bd=1, relief="solid")
                folder_frame.pack(padx=20 + (level * 20), pady=10, anchor="w")
                relative_path = os.path.relpath(path, current_path)
                Checkbutton(
                    folder_frame,
                     text=f"{name}  ({relative_path})",
                    variable=var,
                    command=lambda v=var, d=subtree: update_folder_selection(v, d),
                    bg=folder_frame["bg"],
                    font=("Segoe UI Semibold", 10)
                ).pack(side=LEFT, padx=5)
                toggle_btn = Button(folder_frame, text="-", width=2)
                child_frame = Frame(parent_frame)
                child_frame.pack(padx=20 + (level * 20), anchor="w")
                toggle_btn.config(command=lambda b=toggle_btn, f=child_frame: toggle_visibility(b, f))
                toggle_btn.pack(anchor="w", padx=5)
                add_items(child_frame, subtree, level=level + 1)


        dir_structure = get_directory_structure(path)
        add_items(scroll_f, dir_structure)

    def on_ok():
        selected = [p for p, v in vars_dict.items() if v.get()]
        out_file = "output.txt"
        try:
            with open(out_file, "w", encoding="utf-8") as out:
                for fp in selected:
                    try:
                        with open(fp, "r", encoding="utf-8") as f:
                            out.write(f"=== {fp} ===\n")
                            out.write(f.read() + "\n\n")
                    except Exception:
                        continue

            with open(out_file, "r", encoding="utf-8") as out:
                pyperclip.copy(out.read())

            history = load_history()
            history = add_or_update_history(history, current_path, selected)
            save_history(history)
            refresh_hist_listbox()
            show_toast(window, "Arquivos copiados para o clipboard!")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def on_hist_select(event=None):
        sel = hist_listbox.curselection()
        if sel:
            idx = sel[0]
            entry = load_history()[idx]
            load_selection(entry["path"], entry["selected"])

    hist_listbox.bind("<<ListboxSelect>>", on_hist_select)

    def open_new_folder():
        new_path = filedialog.askdirectory(title="Selecione a nova pasta")
        if new_path:
            history = load_history()
            history = add_or_update_history(history, new_path, [])
            save_history(history)
            refresh_hist_listbox()
            hist_listbox.selection_clear(0, tk.END)
            hist_listbox.selection_set(0)
            hist_listbox.activate(0)
            load_selection(new_path, [])

    def remove_selected_history():
        sel = hist_listbox.curselection()
        if sel:
            idx = sel[0]
            history = load_history()
            if 0 <= idx < len(history):
                removed = history.pop(idx)
                save_history(history)
                refresh_hist_listbox()
                show_toast(window, f'Removido: {removed.get("name") or os.path.basename(removed.get("path"))}')
                # Seleciona outro item, se existir
                if history:
                    hist_listbox.selection_set(0)
                    hist_listbox.activate(0)
                    load_selection(history[0]["path"], history[0].get("selected", []))
                else:
                    # Limpa seleção da esquerda se não houver mais histórico
                    for widget in left_frame.winfo_children():
                        if widget != bottom:
                            widget.destroy()

        # -- logo antes de criar os botões “Selecionar Tudo” etc. --
    def map_structure():
        structure = get_directory_structure(current_path)
        # monta linhas da árvore
        lines = [os.path.basename(current_path) + "/"]
        def build_tree(d, prefix=""):
            items = sorted(d.items(), key=lambda kv: os.path.basename(kv[0]).lower())
            for idx, (path, subtree) in enumerate(items):
                name = os.path.basename(path)
                last = (idx == len(items) - 1)
                connector = "└── " if last else "├── "
                lines.append(f"{prefix}{connector}{name}{'/' if isinstance(subtree, dict) else ''}")
                if isinstance(subtree, dict):
                    extension = "    " if last else "│   "
                    build_tree(subtree, prefix + extension)
        build_tree(structure)

        tree_text = "\n".join(lines)
        # copia pro clipboard
        pyperclip.copy(tree_text)
        # mostra em janela
        tree_win = tk.Toplevel(window)
        tree_win.title("Estrutura de Pastas (Copiada pro clipboard)")
        txt = tk.Text(tree_win, wrap="none")
        txt.insert("1.0", tree_text)
        txt.pack(fill="both", expand=True)
        # scrollbar horizontal
        hbar = tk.Scrollbar(tree_win, orient=tk.HORIZONTAL, command=txt.xview)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        txt.config(xscrollcommand=hbar.set)

        show_toast(window, "Árvore copiada para o clipboard!")

    # -- adiciona o botão junto dos outros em bottom --
    Button(bottom, text="Mapear & Copiar Estrutura", command=map_structure).pack(side=LEFT, padx=5)
    Button(right_frame, text="Abrir Nova Pasta", command=open_new_folder).pack(pady=10, padx=10)
    Button(right_frame, text="Remover do Histórico", command=remove_selected_history).pack(pady=2, padx=10)
    Button(bottom, text="Selecionar Tudo", command=lambda: [var.set(1) for var in vars_dict.values()]).pack(side=LEFT, padx=5)
    Button(bottom, text="Deselecionar Tudo", command=lambda: [var.set(0) for var in vars_dict.values()]).pack(side=LEFT, padx=5)
    Button(bottom, text="Copiar", command=on_ok).pack(side=RIGHT, padx=5)
    Button(bottom, text="Copiar e Fechar", command=lambda: [on_ok(), window.destroy()]).pack(side=RIGHT, padx=5)


    
    if history:
        # Seleciona e carrega o primeiro item do histórico
        hist_listbox.selection_clear(0, tk.END)
        hist_listbox.selection_set(0)
        hist_listbox.activate(0)
        entry = history[0]
        load_selection(entry["path"], entry.get("selected", []))
    else:
        load_selection(abs_base, saved_selection)


if __name__ == "__main__":
    root = Tk()
    history = load_history()
    if history:
        last = history[0]
        initial_path = last["path"]
        sel = last.get("selected", [])
        root.deiconify()
        show_selection_gui(root, initial_path, sel)
        root.mainloop()
    else:
        # Não tem histórico: abre dialog para escolher
        root.withdraw()
        initial_path = filedialog.askdirectory(title="Selecione a pasta que deseja mapear")
        if not initial_path:
            print("Nenhuma pasta foi selecionada.")
        else:
            sel = []
            history = add_or_update_history(load_history(), initial_path, sel)
            save_history(history)
            root.deiconify()
            show_selection_gui(root, initial_path, sel)
            root.mainloop()

