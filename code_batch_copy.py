#!/usr/bin/env python3

import sys
import os
import json

# --------------------------------------------------------------
# 0) VERSION CHECK (Muss ganz oben stehen)
# --------------------------------------------------------------
MIN_VER = (3, 9)
if sys.version_info < MIN_VER:
    sys.stderr.write(
        f"\n[CRITICAL ERROR] Deine Python Version {sys.version_info.major}.{sys.version_info.minor} ist zu alt.\n"
        f"Dieses Tool benötigt Python {MIN_VER[0]}.{MIN_VER[1]} oder neuer.\n"
        "Bitte installiere eine neuere Python Version.\n\n"
    )
    sys.exit(1)

# Erst jetzt importieren wir Libraries
try:
    import questionary
    from questionary import Choice
    import pyperclip
except ImportError:
    print("Fehler: Abhängigkeiten fehlen. Bitte starte das Skript über .sh oder .bat")
    sys.exit(1)

from typing import List, Dict, Set

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(SCRIPT_DIR, ".code_batch_copy.json")

# --------------------------------------------------------------
# 1) STATE LOAD / SAVE
# --------------------------------------------------------------
def load_state() -> Dict[str, List[str]]:
    if not os.path.exists(STATE_FILE):
        return {"directories": [], "files": []}

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        return {"directories": [], "files": []}

    abs_dirs = [os.path.abspath(d) for d in data.get("directories", [])]
    abs_files = [os.path.abspath(f_) for f_ in data.get("files", [])]

    return {"directories": abs_dirs, "files": abs_files}


def save_state(dirs: List[str], files: List[str]) -> None:
    data = {
        "directories": dirs,
        "files": files
    }
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Warnung: State konnte nicht gespeichert werden: {e}")


# --------------------------------------------------------------
# 2) PATH & FILE UTILS
# --------------------------------------------------------------
def get_language_by_extension(file_path: str) -> str:
    extension_map = {
        '.js': 'javascript', '.jsx': 'javascript', '.ts': 'typescript', '.tsx': 'typescript',
        '.yml': 'yaml', '.yaml': 'yaml', '.csv': 'csv', '.txt': 'text',
        '.c': 'c', '.cpp': 'cpp', '.java': 'java', '.go': 'go', '.rs': 'rust',
        '.rb': 'ruby', '.php': 'php', '.pl': 'perl', '.py': 'python',
        '.json': 'json', '.html': 'html', '.css': 'css', '.sh': 'bash', '.bat': 'batch',
        '.md': 'markdown', '.sql': 'sql', '.vue': 'vue'
    }
    base = os.path.basename(file_path).lower()
    _, ext = os.path.splitext(base)
    if not ext:
        if base in ['dockerfile', 'makefile']:
            return 'makefile'
        if base in ['.env', '.gitignore', '.dockerignore']:
            return 'text'
    return extension_map.get(ext, '')


def format_file_contents(file_paths: List[str], base_dir: str) -> str:
    lines = []
    for fp in file_paths:
        rel = os.path.relpath(fp, base_dir)
        lines.append(f"## ./{rel}")
        lang = get_language_by_extension(fp)
        lines.append(f"```{lang}" if lang else "```")
        try:
            with open(fp, "r", encoding="utf-8", errors="replace") as f:
                lines.append(f.read())
        except Exception as e:
            lines.append(f"Fehler beim Lesen von ./{rel}: {e}")
        lines.append("```")
    return "\n".join(lines)


def is_child_of(child: str, parent: str) -> bool:
    c = os.path.abspath(child)
    p = os.path.abspath(parent)
    try:
        return os.path.commonpath([c, p]) == p
    except ValueError:
        return False


def remove_subtree(root_dir: str, selected_dirs: Set[str], selected_files: Set[str]):
    root_abs = os.path.abspath(root_dir)
    if root_abs in selected_dirs:
        selected_dirs.remove(root_abs)

    to_remove_dirs = {d for d in selected_dirs if is_child_of(d, root_abs)}
    selected_dirs -= to_remove_dirs

    to_remove_files = {f for f in selected_files if is_child_of(f, root_abs)}
    selected_files -= to_remove_files


# --------------------------------------------------------------
# 3) REKURSION
# --------------------------------------------------------------
def explore_directory(
        current_dir: str,
        selected_dirs: Set[str],
        selected_files: Set[str],
        base_dir: str
):
    current_abs = os.path.abspath(current_dir)
    if not os.path.isdir(current_abs):
        return

    try:
        entries = os.listdir(current_abs)
    except Exception as e:
        print(f"Zugriff verweigert auf {current_abs}: {e}")
        return

    subdirs = []
    files = []
    for name in entries:
        if name.startswith(".") and name != ".":
            pass

        fullp = os.path.join(current_abs, name)
        if os.path.isdir(fullp):
            subdirs.append((name, fullp))
        else:
            files.append((name, fullp))

    subdirs.sort(key=lambda x: x[0].lower())
    files.sort(key=lambda x: x[0].lower())

    choices = []
    for (subn, subp) in subdirs:
        subabs = os.path.abspath(subp)
        checked = (subabs in selected_dirs)
        choices.append(Choice(title=f"[DIR]  {subn}", value=("dir", subabs), checked=checked))

    for (fname, fpath) in files:
        fabs = os.path.abspath(fpath)
        checked = (fabs in selected_files)
        choices.append(Choice(title=f"       {fname}", value=("file", fabs), checked=checked))

    choices.append(Choice(title=">> Fertig mit diesem Ordner / Weiter", value=("done", None)))

    rel_cdir = os.path.relpath(current_abs, base_dir)
    display_path = "/" if rel_cdir == "." else f"./{rel_cdir}"

    question_text = (
        "\n------------------------------------------\n"
        f"Verzeichnis: {display_path}\n"
        "[Leertaste = (de)selektieren, Enter = Bestätigen]\n"
        "------------------------------------------"
    )

    answer = questionary.checkbox(question_text, choices=choices).ask()
    if answer is None:
        return

    newly_selected_dirs = set()
    newly_selected_files = set()
    done_chosen = False

    for (typ, path) in answer:
        if typ == "dir" and path:
            newly_selected_dirs.add(path)
        elif typ == "file" and path:
            newly_selected_files.add(path)
        elif typ == "done":
            done_chosen = True

    old_subs_in_this_dir = {d for d in selected_dirs if os.path.dirname(d) == current_abs}
    abgewaehlte_subs = old_subs_in_this_dir - newly_selected_dirs
    for d in abgewaehlte_subs:
        remove_subtree(d, selected_dirs, selected_files)

    selected_dirs |= newly_selected_dirs

    old_files_in_current = {f for f in selected_files if os.path.dirname(f) == current_abs}
    abgewaehlte_files = old_files_in_current - newly_selected_files
    selected_files -= abgewaehlte_files
    selected_files |= newly_selected_files

    if done_chosen:
        return

    for sd in sorted(newly_selected_dirs):
        explore_directory(sd, selected_dirs, selected_files, base_dir)


# --------------------------------------------------------------
# 4) KONSISTENZPRÜFUNG
# --------------------------------------------------------------
def ensure_top_down_consistency(base_dir: str, selected_dirs: Set[str], selected_files: Set[str]):
    base_abs = os.path.abspath(base_dir)

    def is_chain_selected(path: str) -> bool:
        cur = os.path.abspath(path)
        while True:
            if cur == base_abs:
                return True
            if cur not in selected_dirs:
                return False
            parent = os.path.dirname(cur)
            if parent == cur:
                return (cur == base_abs)
            cur = parent

    to_remove_dirs = set()
    for d in selected_dirs:
        if d == base_abs: continue
        if not is_chain_selected(d):
            to_remove_dirs.add(d)
    for d in to_remove_dirs:
        remove_subtree(d, selected_dirs, selected_files)

    to_remove_files = set()
    for f in selected_files:
        if not is_chain_selected(os.path.dirname(f)):
            to_remove_files.add(f)
    selected_files -= to_remove_files


# --------------------------------------------------------------
# 5) TREE GENERATOR
# --------------------------------------------------------------
def generate_minimal_tree(base_dir: str, selected_dirs: Set[str], selected_files: Set[str]) -> str:
    all_paths = []
    for dir_path in selected_dirs:
        if dir_path != base_dir:
            rel_path = os.path.relpath(dir_path, base_dir)
            all_paths.append(rel_path)

    for file_path in selected_files:
        rel_path = os.path.relpath(file_path, base_dir)
        all_paths.append(rel_path)

    all_paths.sort()
    path_structure = {}

    for path in all_paths:
        parts = path.split(os.sep)
        current = path_structure
        for i, part in enumerate(parts):
            if part not in current:
                full_path = os.path.join(base_dir, os.sep.join(parts[:i+1]))
                is_dir = os.path.isdir(full_path)
                current[part] = {'is_dir': is_dir, 'children': {}}
            if i < len(parts) - 1:
                current = current[part]['children']

    base_name = os.path.basename(base_dir)
    tree_lines = [f"{base_name}/"]

    def build_tree(node, prefix=""):
        lines = []
        items = list(node.items())
        items.sort(key=lambda x: (not x[1]['is_dir'], x[0]))

        for i, (name, info) in enumerate(items):
            is_last = i == len(items) - 1
            branch = "└── " if is_last else "├── "
            new_prefix = prefix + ("    " if is_last else "│   ")

            suffix = "/" if info['is_dir'] else ""
            lines.append(f"{prefix}{branch}{name}{suffix}")

            if info['children']:
                lines.extend(build_tree(info['children'], new_prefix))
        return lines

    if path_structure:
        tree_lines.extend(build_tree(path_structure))

    return "\n".join(tree_lines)


# --------------------------------------------------------------
# 6) MAIN
# --------------------------------------------------------------
def main():
    if len(sys.argv) > 1:
        base_dir = os.path.abspath(sys.argv[1])
        if not os.path.isdir(base_dir):
            print(f"Fehler: '{base_dir}' ist kein Ordner.")
            sys.exit(1)
    else:
        base_dir = os.getcwd()

    print("========================================================")
    print(f"Basisverzeichnis: {base_dir}")
    print("========================================================\n")

    try:
        output_choice = questionary.select(
            "Ausgabeformat wählen:",
            choices=[
                Choice("Tree & Code", value="both"),
                Choice("Project Tree", value="tree"),
                Choice("Code", value="code")
            ]
        ).ask()
    except Exception:
        output_choice = None

    if output_choice is None:
        sys.exit(0)

    old_state = load_state()
    selected_dirs = set(old_state["directories"])
    selected_files = set(old_state["files"])

    explore_directory(base_dir, selected_dirs, selected_files, base_dir)
    ensure_top_down_consistency(base_dir, selected_dirs, selected_files)

    tree_output = generate_minimal_tree(base_dir, selected_dirs, selected_files)
    final_files = sorted(selected_files)
    file_contents = format_file_contents(final_files, base_dir) if final_files else ""

    # --- AUSGABE IM TERMINAL ---
    if output_choice in ["tree", "both"]:
        print("\n--- TREE VORSCHAU ---\n")
        print(tree_output)

    if output_choice in ["code", "both"] and final_files:
        print("\n--- AUSGEWÄHLTE DATEIEN UND INHALTE ---\n")
        print(file_contents)
    elif output_choice == "code" and not final_files:
        print("\nKeine Dateien final ausgewählt.")

    # --- ZWISCHENABLAGE ---
    try:
        content_to_copy = ""
        success_msg = ""

        if output_choice == "both" and final_files:
            content_to_copy = f"{tree_output}\n\n{file_contents}"
            success_msg = "Baum und Code wurden in die Zwischenablage kopiert."
        elif output_choice == "tree":
            content_to_copy = tree_output
            success_msg = "Baum wurde in die Zwischenablage kopiert."
        elif output_choice == "code" and final_files:
            content_to_copy = file_contents
            success_msg = "Code wurde in die Zwischenablage kopiert."

        if content_to_copy:
            pyperclip.copy(content_to_copy)
            print(f"\n✅ {success_msg}")
        else:
            print("\nKein Inhalt zum Kopieren vorhanden.")

    except pyperclip.PyperclipException:
        print("\n⚠️  FEHLER: Clipboard Zugriff fehlgeschlagen.")
    except Exception as e:
        print(f"\n⚠️  Unerwarteter Fehler beim Kopieren: {e}")

    save_state(sorted(selected_dirs), sorted(selected_files))
    print("\n========================================================\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAbbruch durch Benutzer.")
        sys.exit(0)
