import os
import string
from pathlib import Path


# TODO: If you want faster searches, add folders to skip here.
# Example: {"Windows", "Program Files", "Program Files (x86)"}
SKIP_FOLDERS = {
    "Windows",
    "Program Files",
    "Program Files (x86)",
}


def get_windows_drives():
    """Return a list of available drive roots on Windows."""
    drives = []
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            drives.append(drive)
    return drives


def should_skip_folder(folder_path):
    """Skip folders that are likely to slow the search down."""
    parts = Path(folder_path).parts
    return any(part in SKIP_FOLDERS for part in parts)


def search_files(search_term, roots):
    """
    Search for files whose names contain the search term.

    If you want exact-name matching instead of partial matching, change:
        search_term.lower() in file_name.lower()
    to:
        search_term.lower() == file_name.lower()
    """
    matches = []
    search_term = search_term.strip().lower()

    for root in roots:
        for folder_path, _, file_names in os.walk(root):
            if should_skip_folder(folder_path):
                continue

            for file_name in file_names:
                if search_term in file_name.lower():
                    full_path = Path(folder_path) / file_name
                    matches.append(full_path)

    return matches


def main():
    # TODO: Change this prompt if you want a different style of input.
    search_term = input("Enter the file name to search for: ").strip()

    if not search_term:
        print("Please enter a file name.")
        return

    roots = get_windows_drives()

    if not roots:
        print("No drives found.")
        return

    print("Searching. This may take a while...")

    matches = search_files(search_term, roots)

    if not matches:
        print("No files found.")
        return

    print(f"\nFound {len(matches)} file(s):\n")

    for index, path in enumerate(matches, start=1):
        print(f"{index}. File name: {path.name}")
        print(f"   Full path: {path}")
        print(f"   Folder: {path.parent}\n")


if __name__ == "__main__":
    main()
