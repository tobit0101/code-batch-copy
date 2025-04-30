#!/usr/bin/env python3

import os
import sys
import json
import questionary
from questionary import Choice
import pyperclip
from typing import List, Dict, Set

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(SCRIPT_DIR, ".code_batch_copy.json")

# --------------------------------------------------------------
# 1) STATE LOAD / SAVE  (nur absolute Pfade)
# --------------------------------------------------------------
def load_state() -> Dict[str, List[str]]:
    """
    Lädt .code_batch_copy.json
    { "directories": [...], "files": [...] }
    Falls vorhanden, wandelt die Pfade in absolute Pfade um.
    """
    if not os.path.exists(STATE_FILE):
        return {"directories": [], "files": []}

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        return {"directories": [], "files": []}

    abs_dirs = []
    for d in data.get("directories", []):
        abs_dirs.append(os.path.abspath(d))

    abs_files = []
    for f_ in data.get("files", []):
        abs_files.append(os.path.abspath(f_))

    return {"directories": abs_dirs, "files": abs_files}


def save_state(dirs: List[str], files: List[str]) -> None:
    """
    Schreibt die Pfade in .code_batch_copy.json
    """
    data = {
        "directories": dirs,
        "files": files
    }
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Fehler beim Speichern des States: {e}")


# --------------------------------------------------------------
# 2) PATH & FILE UTILS
# --------------------------------------------------------------
def get_language_by_extension(file_path: str) -> str:
    extension_map = {
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.ts': 'typescript',
        '.yml': 'yml',
        '.yaml': 'yaml',
        '.csv': 'csv',
        '.txt': 'text',
        '.c': 'c',
        '.cpp': 'cpp',
        '.java': 'java',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.pl': 'perl',
        '.py': 'python',
        '.json': 'json',
        '.html': 'html',
        '.css': 'css',
        '.c': 'c',
        '.cpp': 'cpp',
    }
    base = os.path.basename(file_path).lower()
    _, ext = os.path.splitext(base)
    if not ext:
        if base in ['dockerfile', '.env', '.gitignore', '.dockerignore']:
            return 'text'
    return extension_map.get(ext, '')


def format_file_contents(file_paths: List[str], base_dir: [str]) -> str:
    lines = []
    for fp in file_paths:
        rel = os.path.relpath(fp, base_dir)
        lines.append(f"## ./{rel}")
        lang = get_language_by_extension(fp)
        if lang:
            lines.append(f"```{lang}")
        else:
            lines.append("```")
        try:
            with open(fp, "r", encoding="utf-8") as f:
                lines.append(f.read())
        except Exception as e:
            lines.append(f"Fehler beim Lesen von ./{rel}: {e}")
        lines.append("```")
    return "\n".join(lines)


def is_child_of(child: str, parent: str) -> bool:
    """
    True, wenn 'child' (Datei oder Ordner) innerhalb von 'parent' liegt
    (inkl. dem Fall, dass child == parent).
    """
    c = os.path.abspath(child)
    p = os.path.abspath(parent)
    return os.path.commonpath([c, p]) == p


def remove_subtree(root_dir: str, selected_dirs: Set[str], selected_files: Set[str]):
    """
    Entfernt root_dir aus selected_dirs sowie alle Kinder (Verzeichnisse + Dateien).
    """
    root_abs = os.path.abspath(root_dir)
    if root_abs in selected_dirs:
        selected_dirs.remove(root_abs)

    # Alle Kinderverzeichnisse
    to_remove_dirs = {d for d in selected_dirs if is_child_of(d, root_abs)}
    selected_dirs -= to_remove_dirs

    # Alle Dateien
    to_remove_files = {f for f in selected_files if is_child_of(f, root_abs)}
    selected_files -= to_remove_files


# --------------------------------------------------------------
# 3) REKURSION: EIN ORDNER, EINE FRAGE
# --------------------------------------------------------------
def explore_directory(
    current_dir: str,
    selected_dirs: Set[str],
    selected_files: Set[str],
    base_dir: str
):
    """
    Zeigt den Inhalt (1 Ebene) von current_dir.
    Vorab-Häkchen, wenn Pfade bereits in selected_dirs/files stehen.
    Danach:
      - Abwahlen => sofort remove_subtree
      - Ausgewählte Subdirs => wir rufen rekursiv explore_directory(...)
    """
    current_abs = os.path.abspath(current_dir)
    if not os.path.isdir(current_abs):
        return

    try:
        entries = os.listdir(current_abs)
    except Exception as e:
        print(f"Fehler beim Lesen von {current_abs}: {e}")
        return

    subdirs = []
    files = []
    for name in entries:
        fullp = os.path.join(current_abs, name)
        if os.path.isdir(fullp):
            subdirs.append((name, fullp))
        else:
            files.append((name, fullp))

    subdirs.sort(key=lambda x: x[0].lower())
    files.sort(key=lambda x: x[0].lower())

    # -- Checkbox-Liste
    choices = []
    for (subn, subp) in subdirs:
        subabs = os.path.abspath(subp)
        checked = (subabs in selected_dirs)
        choices.append(
            Choice(title=f"[DIR] {subn}", value=("dir", subabs), checked=checked)
        )
    for (fname, fpath) in files:
        fabs = os.path.abspath(fpath)
        checked = (fabs in selected_files)
        choices.append(
            Choice(title=fname, value=("file", fabs), checked=checked)
        )
    # (Fertig) Option
    choices.append(Choice(title="(Fertig / Weiter)", value=("done", None)))

    # Pfad relativ zu base_dir
    rel_cdir = os.path.relpath(current_abs, base_dir)
    if rel_cdir.startswith(".."):
        # evtl. base_dir == current_abs => relpath => "."
        if os.path.abspath(current_abs) == os.path.abspath(base_dir):
            rel_cdir = "."

    question_text = (
        "\n------------------------------------------\n"
        f"Verzeichnis: ./{rel_cdir}\n"
        "\n"
        "[Leertaste = (de)selektieren, Enter = Bestätigen]\n"
        "------------------------------------------\n"
    )

    answer = questionary.checkbox(question_text, choices=choices).ask()
    if not answer:
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

    # -- Ermitteln: welche Subdirs in diesem Ordner waren vorher selektiert?
    old_subs_in_this_dir = {
        d for d in selected_dirs if os.path.dirname(d) == current_abs
    }
    abgewählte_subs = old_subs_in_this_dir - newly_selected_dirs
    # -> remove_subtree für alle abgewählten
    for d in abgewählte_subs:
        remove_subtree(d, selected_dirs, selected_files)

    # -> neu/weiter gewählte Subdirs rein
    selected_dirs |= newly_selected_dirs

    # -- Dateien
    old_files_in_current = {
        f for f in selected_files if os.path.dirname(f) == current_abs
    }
    abgewählte_files = old_files_in_current - newly_selected_files
    selected_files -= abgewählte_files
    selected_files |= newly_selected_files

    # => Wenn done => return
    if done_chosen:
        return

    # => Ansonsten => für alle subdirs, die jetzt selektiert sind => Rekursion
    for sd in sorted(newly_selected_dirs):
        explore_directory(sd, selected_dirs, selected_files, base_dir)


# --------------------------------------------------------------
# 4) FINALE KONSISTENZPRÜFUNG (TOP-DOWN)
# --------------------------------------------------------------
def ensure_top_down_consistency(
    base_dir: str,
    selected_dirs: Set[str],
    selected_files: Set[str]
):
    """
    Entfernt alle Verzeichnisse und Dateien, deren Pfad-Kette nicht existiert.
    d. h. wenn ein Subordner in 'selected_dirs' ist, aber sein Parent
    nicht (außer base_dir selbst?), dann raus.

    Für Dateien: Jede Ebene ihres Ordnerpfads muss in selected_dirs sein,
    bis wir base_dir erreichen.
    """
    # 1) Wir bauen uns eine schnelle Prüfung, ob ein Pfad in selected_dirs ODER == base_dir
    #    Als Basis gilt: base_dir kann immer "existieren" (muss nicht in selected_dirs sein).
    #    Also: Ein Pfad ist "gültig", wenn base_dir == pfad oder in selected_dirs enthalten.
    #
    #    Dann klettern wir parent-aufwärts und checken, ob die chain unbroken ist.

    base_abs = os.path.abspath(base_dir)

    def is_chain_selected(path: str) -> bool:
        """
        Prüft, ob vom 'path' aufwärts bis base_dir jeder Ordner in selected_dirs
        oder == base_dir ist.
        """
        cur = os.path.abspath(path)
        while True:
            if cur == base_abs:
                # base_dir => Ok
                return True
            if cur not in selected_dirs:
                return False
            parent = os.path.dirname(cur)
            if parent == cur:
                # root
                return (cur == base_abs)
            cur = parent

    # -- erst: Direktories (außer base_dir selbst, das darf existieren)
    to_remove_dirs = set()
    for d in selected_dirs:
        if d == base_abs:
            # base_dir => ist okay, egal ob es in selected_dirs stand oder nicht
            continue
        if not is_chain_selected(d):
            to_remove_dirs.add(d)
    # remove sie
    for d in to_remove_dirs:
        remove_subtree(d, selected_dirs, selected_files)

    # -- dann: Dateien
    to_remove_files = set()
    for f in selected_files:
        # check chain
        folder = os.path.dirname(f)
        if not is_chain_selected(folder):
            to_remove_files.add(f)
    selected_files -= to_remove_files


# --------------------------------------------------------------
# 5) MINIMAL TREE AUSGABE
# --------------------------------------------------------------
def generate_minimal_tree(base_dir: str, selected_dirs: Set[str], selected_files: Set[str]) -> str:
    """
    Generiert eine minimale Baumstruktur im Markdown-Format,
    die nur die ausgewählten Dateien und Ordner zeigt.
    """
    # Sammle alle Pfade (Dateien und Ordner) relativ zum base_dir
    all_paths = []
    for dir_path in selected_dirs:
        if dir_path != base_dir:  # Exclude base_dir itself
            rel_path = os.path.relpath(dir_path, base_dir)
            all_paths.append(rel_path)
    
    for file_path in selected_files:
        rel_path = os.path.relpath(file_path, base_dir)
        all_paths.append(rel_path)
    
    # Sortiere die Pfade
    all_paths.sort()
    
    # Erstelle ein Dictionary für die Pfadstruktur
    path_structure = {}
    
    # Verarbeite jeden Pfad
    for path in all_paths:
        # Erstelle alle Zwischenverzeichnisse im Pfad
        parts = path.split(os.sep)
        current = path_structure
        
        # Für jeden Teil des Pfades
        for i, part in enumerate(parts):
            if part not in current:
                # Prüfe, ob es ein Verzeichnis oder eine Datei ist
                full_path = os.path.join(base_dir, os.sep.join(parts[:i+1]))
                is_dir = os.path.isdir(full_path)
                
                current[part] = {
                    'is_dir': is_dir,
                    'children': {},
                    'depth': i
                }
            
            # Gehe zum nächsten Level
            if i < len(parts) - 1:
                current = current[part]['children']
    
    # Generiere den Baum
    base_name = os.path.basename(base_dir)
    tree_lines = [f"{base_name}/"]
    
    # Funktion zum rekursiven Erstellen der Baumstruktur
    def build_tree(node, prefix=""):
        lines = []
        items = list(node.items())
        
        # Sortiere nach Verzeichnissen zuerst, dann nach Namen
        items.sort(key=lambda x: (not x[1]['is_dir'], x[0]))
        
        for i, (name, info) in enumerate(items):
            is_last = i == len(items) - 1
            is_dir = info['is_dir']
            
            # Wähle die richtigen Symbole basierend auf Position
            if is_last:
                branch = "└── "
                new_prefix = prefix + "    "
            else:
                branch = "├── "
                new_prefix = prefix + "│   "
            
            # Füge den Eintrag hinzu
            if is_dir:
                lines.append(f"{prefix}{branch}{name}/")
            else:
                lines.append(f"{prefix}{branch}{name}")
            
            # Rekursiv für Unterverzeichnisse
            if info['children']:
                lines.extend(build_tree(info['children'], new_prefix))
        
        return lines
    
    # Füge die Baumstruktur hinzu
    if path_structure:
        tree_lines.extend(build_tree(path_structure))
    
    return "\n".join(tree_lines)

# --------------------------------------------------------------
# 6) main
# --------------------------------------------------------------
def main():
    # a) base_dir
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
    
    # Auswahl des Ausgabeformats
    output_choice = questionary.select(
        "Ausgabeformat wählen:",
        choices=[
            Choice("Tree & Code", value="both"),
            Choice("Project Tree", value="tree"),
            Choice("Code", value="code")
        ]
    ).ask()
    
    if output_choice is None:  # Falls der Benutzer abbricht
        sys.exit(0)

    # b) State laden (absolute Pfade)
    old_state = load_state()
    selected_dirs = set(old_state["directories"])
    selected_files = set(old_state["files"])

    # c) REKURSION: beginne bei base_dir
    #    (Optional: base_dir auch in selected_dirs?
    #     Wenn du willst, kannst du es dazupacken, um den Pfad consistent zu halten.)
    #    Hier belasse ich es bei "wir zeigen base_dir IMMER"
    explore_directory(base_dir, selected_dirs, selected_files, base_dir)

    # d) Top-Down-Konsistenzprüfung
    ensure_top_down_consistency(base_dir, selected_dirs, selected_files)
    
    # e) Minimaler Baum der ausgewählten Dateien und Ordner
    tree_output = generate_minimal_tree(base_dir, selected_dirs, selected_files)
    
    # f) Dateiinhalte formatieren
    final_files = sorted(selected_files)
    file_contents = format_file_contents(final_files, base_dir) if final_files else ""
    
    # g) Ausgabe basierend auf der Auswahl
    if output_choice in ["tree", "both"]:
        print("\n--- MINIMALER BAUM DER AUSGEWÄHLTEN DATEIEN UND ORDNER ---\n")
        print(tree_output)
    
    if output_choice in ["code", "both"] and final_files:
        print("\n--- AUSGEWÄHLTE DATEIEN UND INHALTE ---\n")
        print(file_contents)
    elif output_choice == "code" and not final_files:
        print("\nKeine Dateien final ausgewählt.")
    
    # h) In die Zwischenablage kopieren basierend auf der Auswahl
    try:
        if output_choice == "both" and final_files:
            combined_text = f"{tree_output}\n\n{file_contents}"
            pyperclip.copy(combined_text)
            print("\nBaum und Inhalte wurden in die Zwischenablage kopiert.")
        elif output_choice == "tree":
            pyperclip.copy(tree_output)
            print("\nBaum wurde in die Zwischenablage kopiert.")
        elif output_choice == "code" and final_files:
            pyperclip.copy(file_contents)
            print("\nInhalte wurden in die Zwischenablage kopiert.")
    except Exception as e:
        print(f"Fehler beim Kopieren in die Zwischenablage: {e}")
        
    if not final_files and output_choice in ["code", "both"]:
        print("\nKeine Dateien final ausgewählt.")

    # g) State speichern
    new_dirs = sorted(selected_dirs)
    new_files = sorted(selected_files)
    save_state(new_dirs, new_files)

    print("\n========================================================")
    print("========================================================\n")


if __name__ == "__main__":
    main()
