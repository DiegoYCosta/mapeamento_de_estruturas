import os
import json
import pyperclip
from datetime import datetime
import tkinter as tk
from tkinter import (
    Tk, filedialog, Checkbutton, Button, IntVar,
    Scrollbar, Canvas, Frame, VERTICAL, BOTH, RIGHT, LEFT, Y, messagebox, simpledialog, messagebox
)

IGNORED_PATTERNS = [
    ".git", "node_modules", "__pycache__", ".DS_Store", ".vscode", "*.pyc", "*.pyo", "*.exe",
    "*.dll", "*.so", "*.dylib", "*.log", "*.tmp", "*.swp", "*.swo", "*.bak", ".idea", "*.class",
    "*.jar", "*.war", "*.zip", "*.tar", "*.gz", "*.7z", "*.rar", "dist", "build", "*.egg-info",
    "env", ".env", "venv", ".coverage", ".pytest_cache", ".mypy_cache", "coverage.xml", ".gradle", ".next",
    ".nuxt", ".yarn", "yarn.lock", "package-lock.json", "*.lock", "Thumbs.db", ".sass-cache", ".cache"
]

STATE_FILE = "selection_state.json"
MAX_HISTORY = 10

FIXED_NAMES = [
    "Última Sel.",
    "Save 02",
    "Save 03",
    "Save 04",
    "Save 05",
    "Save 06",
    "Save 07",
    "Save 08",
    "Save 09",
    "Save 10"
]

def load_history():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            history = data.get("history", [])
    except Exception:
        history = []

    normalized = []
    for i in range(MAX_HISTORY):
        if i < len(history):
            entry = history[i]
            if i == 0 and not entry.get("path"):
                normalized.append({
                    "path": "",
                    "selected": [],
                    "saved_at": "",
                    "name": FIXED_NAMES[0]
                })
            else:
                normalized.append({
                    "path": entry.get("path", ""),
                    "selected": entry.get("selected", []),
                    "saved_at": entry.get("saved_at", ""),
                    "name": entry.get("name", FIXED_NAMES[i])[:10]
                })
        else:
            normalized.append({
                "path": "",
                "selected": [],
                "saved_at": "",
                "name": FIXED_NAMES[i]
            })

    normalized[0]["name"] = FIXED_NAMES[0]
    if not normalized[0]["path"]:
        normalized[0]["selected"] = []
        normalized[0]["saved_at"] = ""

    return normalized

def save_history(history):
    for i in range(len(history)):
        history[i]["name"] = history[i].get("name", FIXED_NAMES[i])[:10]
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"history": history[:MAX_HISTORY]}, f, indent=2, ensure_ascii=False)

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
    if index == 0:
        messagebox.showinfo("Atenção", "O item 'Última Seleção' não pode ser renomeado.")
        return
    old_name = history[index]['name']
    new_name = simpledialog.askstring(
        "Renomear",
        "Informe novo nome (máx 10 caracteres):",
        initialvalue=old_name)
    if new_name:
        new_name = new_name.strip()[:10]
        history[index]['name'] = new_name
        listbox.delete(index)
        listbox.insert(index, new_name)
        save_history(history)

def create_history_listbox(parent, history):
    listbox = tk.Listbox(parent, font=("Segoe UI", 11), height=15)
    listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    for entry in history:
        display_name = entry.get("name") or entry.get("path") or "Nenhuma pasta"
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
    listbox.bind("<Double-Button-1>", lambda e: rename_item(listbox, listbox.nearest(e.y), history))
    return listbox

def should_ignore(path):
    for pattern in IGNORED_PATTERNS:
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
    history = load_history()

    left_frame = Frame(window)
    left_frame.pack(side=tk.LEFT, fill=BOTH, expand=True)

    right_frame = Frame(window, width=280, bg="#f8f8f8", bd=1, relief="solid")
    right_frame.pack(side=tk.RIGHT, fill=Y)

    hist_listbox = create_history_listbox(right_frame, history)
    current_path = abs_base
    current_saved = set(saved_selection or [])

    save_var = IntVar(master=window, value=1 if saved_selection else 0)
    vars_dict = {}

    bottom = Frame(left_frame)
    bottom.pack(fill="x", pady=5)
    save_checkbox = Checkbutton(bottom, text="Salvar Seleção", variable=save_var)
    save_checkbox.pack(side=LEFT, padx=5)

    def refresh_hist_listbox():
        hist_listbox.delete(0, tk.END)
        h = load_history()
        for entry in h:
            display_name = entry.get("name") or entry.get("path") or "Nenhuma pasta"
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

        def add_items(parent_frame, parent_dict):
            files = [(p, s) for p, s in parent_dict.items() if s is None]
            folders = [(p, s) for p, s in parent_dict.items() if isinstance(s, dict)]
            for path, _ in sorted(files, key=lambda kv: os.path.basename(kv[0]).lower()):
                name = os.path.basename(path)
                var = IntVar(master=window, value=1 if path in current_saved else 0)
                vars_dict[path] = var
                Checkbutton(parent_frame, text=name, variable=var).pack(anchor="w", padx=20)
            for path, subtree in sorted(folders, key=lambda kv: os.path.basename(kv[0]).lower()):
                name = os.path.basename(path)
                var = IntVar(master=window, value=1 if any(p.startswith(path) for p in current_saved) else 0)
                vars_dict[path] = var
                folder_frame = Frame(parent_frame, bg="#f0f0f0", bd=1, relief="solid")
                folder_frame.pack(fill="x", padx=5, pady=2)
                Checkbutton(
                    folder_frame, text=name, variable=var,
                    command=lambda v=var, d=subtree: update_folder_selection(v, d),
                    bg="#f0f0f0"
                ).pack(side=LEFT, padx=5)
                toggle_btn = Button(folder_frame, text="-", width=2)
                child_frame = Frame(parent_frame)
                child_frame.pack(fill="x", padx=10)
                toggle_btn.config(command=lambda b=toggle_btn, f=child_frame: toggle_visibility(b, f))
                toggle_btn.pack(side=RIGHT, padx=5)
                add_items(child_frame, subtree)

        dir_structure = get_directory_structure(path)
        add_items(scroll_f, dir_structure)

        if current_path == load_history()[0]["path"]:
            save_var.set(1)
            save_checkbox.config(state="disabled")
        else:
            save_checkbox.config(state="normal")

    def on_ok():
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

            history = load_history()

            # Atualiza slot 0 somente se for a pasta inicial (base_path)
            if current_path == os.path.abspath(base_path):
                history[0]["selected"] = selected
                history[0]["saved_at"] = datetime.now().isoformat()

            # Atualiza outros slots conforme lógica existente
            slot_found = False
            for i in range(1, MAX_HISTORY):
                h = history[i]
                if h["path"] == current_path:
                    history[i]["selected"] = selected
                    history[i]["saved_at"] = datetime.now().isoformat()
                    slot_found = True
                    break
            if not slot_found and save_var.get() and current_path != history[0]["path"]:
                inserted = False
                for i in range(1, MAX_HISTORY):
                    if history[i]["path"] == "":
                        history[i] = {
                            "path": current_path,
                            "selected": selected,
                            "saved_at": datetime.now().isoformat(),
                            "name": history[i]["name"]
                        }
                        inserted = True
                        break
                if not inserted:
                    messagebox.showwarning("Aviso", "Não há espaço para salvar esta pasta na lista. Limpe um slot antes.")
            elif not save_var.get() and current_path != history[0]["path"]:
                for i, h in enumerate(history):
                    if h["path"] == current_path:
                        history[i]["selected"] = []
                        history[i]["saved_at"] = ""

            save_history(history)
            refresh_hist_listbox()
            save_var.set(0)
            save_checkbox.config(state="normal")
            messagebox.showinfo("Sucesso", "Arquivos copiados para o clipboard!")
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
        new_path = filedialog.askdirectory(title="Selecione a pasta que deseja mapear")
        if new_path:
            sel = hist_listbox.curselection()
            index_to_update = sel[0] if sel else 0
            if index_to_update == 0:
                messagebox.showwarning("Aviso", "A pasta 'Última Sel.' não pode ser alterada aqui.")
                return
            history = load_history()
            now_str = datetime.now().isoformat()
            old_name = history[index_to_update].get("name", FIXED_NAMES[index_to_update])
            history[index_to_update] = {
                "path": new_path,
                "selected": [],
                "saved_at": now_str,
                "name": old_name
            }
            save_history(history)
            refresh_hist_listbox()
            hist_listbox.selection_clear(0, tk.END)
            hist_listbox.selection_set(index_to_update)
            hist_listbox.activate(index_to_update)
            load_selection(new_path, [])

    Button(right_frame, text="Abrir Nova Pasta", command=open_new_folder).pack(pady=10, padx=10)
    Button(bottom, text="Selecionar Tudo", command=lambda: [var.set(1) for var in vars_dict.values()]).pack(side=LEFT, padx=5)
    Button(bottom, text="OK", command=on_ok).pack(side=RIGHT, padx=5)
    Button(bottom, text="Cancelar", command=window.destroy).pack(side=RIGHT, padx=5)
    load_selection(abs_base, saved_selection)

if __name__ == "__main__":
    root = Tk()
    root.withdraw()
    initial_path = filedialog.askdirectory(title="Selecione a pasta que deseja mapear")
    if not initial_path:
        print("Nenhuma pasta foi selecionada.")
    else:
        history = load_history()
        now_str = datetime.now().isoformat()

        # Determina seleção para o index 0 sem sobrescrever se já existir
        if history[0]["path"] == initial_path and history[0]["selected"]:
            saved_selection = history[0]["selected"]
        else:
            history[0]["path"] = initial_path
            history[0]["selected"] = []
            history[0]["saved_at"] = now_str
            history[0]["name"] = FIXED_NAMES[0]
            save_history(history)
            saved_selection = None

        root.deiconify()
        show_selection_gui(root, initial_path, saved_selection)
        root.mainloop()
