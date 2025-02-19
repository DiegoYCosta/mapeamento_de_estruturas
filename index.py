import os
import pyperclip
from tkinter import Tk, filedialog, Toplevel, Checkbutton, Button, IntVar, Scrollbar, Canvas, Frame, VERTICAL, BOTH, RIGHT, LEFT, Y

IGNORED_PATTERNS = [
    ".git", "node_modules", "__pycache__", ".DS_Store", ".vscode", "*.pyc", "*.pyo", "*.exe",
    "*.dll", "*.so", "*.dylib", "*.log", "*.tmp", "*.swp", "*.swo", "*.bak", ".idea", "*.class",
    "*.jar", "*.war", "*.zip", "*.tar", "*.gz", "*.7z", "*.rar", "dist", "build", "*.egg-info",
    "env", ".env", "venv", ".coverage", ".pytest_cache", ".mypy_cache", "coverage.xml", ".gradle", ".next",
    ".nuxt", ".yarn", "yarn.lock", "package-lock.json", "*.lock", "Thumbs.db", ".sass-cache", ".cache"
]

def should_ignore(path):
    for pattern in IGNORED_PATTERNS:
        if pattern in path or (pattern.startswith("*") and path.endswith(pattern[1:])):
            return True
    return False

def get_directory_structure(base_path):
    structure = {}
    for root, dirs, files in os.walk(base_path):
        dirs[:] = [d for d in dirs if not should_ignore(os.path.join(root, d))]
        relative_path = os.path.relpath(root, base_path)
        parent = structure
        if relative_path != ".":
            for part in relative_path.split(os.sep):
                parent = parent.setdefault(part, {})
        for file in files:
            if not should_ignore(os.path.join(root, file)):
                parent[file] = None
    return structure

def show_selection_gui(base_path):
    def toggle_visibility(button, frame):
        if frame.winfo_viewable():
            frame.pack_forget()
            button.config(text="+")
        else:
            frame.pack(fill="x")
            button.config(text="-")

    def update_folder_selection(var, folder_dict):
        def toggle_selection(status, parent_dict):
            for key, value in parent_dict.items():
                if isinstance(value, dict):
                    toggle_selection(status, value)
                else:
                    vars_dict[key].set(status)

        toggle_selection(var.get(), folder_dict)

    def add_items(parent_frame, parent_dict):
        for key, value in parent_dict.items():
            if isinstance(value, dict):
                folder_var = IntVar()
                folder_frame = Frame(parent_frame, bg="#f0f0f0", bd=1, relief="solid")
                folder_frame.pack(fill="x", padx=5, pady=2)

                folder_checkbox = Checkbutton(
                    folder_frame, text=key, variable=folder_var,
                    command=lambda v=folder_var, d=value: update_folder_selection(v, d),
                    bg="#f0f0f0"
                )
                folder_checkbox.pack(side=LEFT, padx=5)

                child_frame = Frame(parent_frame)
                child_frame.pack(fill="x", padx=10)

                # Define a função lambda sem referência circular
                toggle_button = Button(folder_frame, text="-", width=2)
                toggle_button.config(command=lambda f=child_frame, b=toggle_button: toggle_visibility(b, f))
                toggle_button.pack(side=RIGHT, padx=5)

                add_items(child_frame, value)
            else:
                file_var = IntVar()
                vars_dict[key] = file_var
                file_checkbox = Checkbutton(parent_frame, text=key, variable=file_var)
                file_checkbox.pack(anchor="w", padx=20)

    def map_selected_files():
        selected_files = []

        def collect_selected_files(parent_path, parent_dict):
            for key, value in parent_dict.items():
                item_path = os.path.join(parent_path, key)
                if isinstance(value, dict):
                    collect_selected_files(item_path, value)
                elif vars_dict[key].get():
                    selected_files.append(item_path)

        collect_selected_files(base_path, structure)

        output_file = "output.txt"
        try:
            with open(output_file, "w", encoding="utf-8") as txt_file:
                for file_path in selected_files:
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            txt_file.write(f"=== {file_path} ===\n")
                            txt_file.write(f.read() + "\n\n")
                    except Exception as e:
                        txt_file.write(f"Erro ao ler {file_path}: {e}\n\n")

            with open(output_file, "r", encoding="utf-8") as txt_file:
                pyperclip.copy(txt_file.read())

            print("Arquivos selecionados foram copiados para o clipboard!")
        except Exception as e:
            print(f"Erro: {e}")

        window.destroy()

    window = Toplevel()
    window.title("Seleção de Arquivos")
    window.geometry("600x700")

    canvas = Canvas(window)
    scrollbar = Scrollbar(window, orient=VERTICAL, command=canvas.yview)
    scrollable_frame = Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    structure = get_directory_structure(base_path)
    vars_dict = {}

    add_items(scrollable_frame, structure)

    ok_button = Button(window, text="OK", command=map_selected_files)
    cancel_button = Button(window, text="Cancelar", command=window.destroy)

    canvas.pack(side=LEFT, fill=BOTH, expand=True)
    scrollbar.pack(side=RIGHT, fill=Y)
    ok_button.pack(side=LEFT, padx=10, pady=10)
    cancel_button.pack(side=RIGHT, padx=10, pady=10)

    window.mainloop()

if __name__ == "__main__":
    root = Tk()
    root.withdraw()
    user_path = filedialog.askdirectory(title="Selecione a pasta que deseja mapear")

    if user_path:
        show_selection_gui(user_path)
    else:
        print("Nenhuma pasta foi selecionada.")