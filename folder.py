import os

IGNORE = {".venv", "__pycache__", "node_modules", ".git"}

def walk_filtered(root="."):
    for current, dirs, files in os.walk(root):
        # remove ignored directories from the list so os.walk doesn't enter them
        dirs[:] = [d for d in dirs if d not in IGNORE]

        level = current.count(os.sep)
        indent = " " * 4 * level
        print(f"{indent}{os.path.basename(current)}/")

        subindent = " " * 4 * (level + 1)
        for f in files:
            print(f"{subindent}{f}")

walk_filtered(".")
