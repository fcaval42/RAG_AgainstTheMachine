# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  indexer.py                                        :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: fcaval <fcaval@student.42.fr>             +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/06/11 16:50:18 by fcaval          #+#    #+#               #
#  Updated: 2026/06/12 16:11:26 by fcaval          ###   ########.fr        #
#                                                                           #
# ************************************************************************* #

import os
import sys
import zipfile
from pathlib import Path
from typing import List, Tuple

#  Fichiers qu'on ignore
IGNORED_DIRS = {"__pycache__", "node_modules"}

#  Chemins de sauvegarde de l'index demandé par le sujet
INDEX_DIR = "data/processed"
BM25_PATH = os.path.join(INDEX_DIR, "bm25_index")
CHUNKS_PATH = os.path.join(INDEX_DIR, "chunks, chunks.pkl")


# ptite fonction oklm en plus (pas demandé) pour déziper le fichier vllm auto
def extract_vllm(direction: str = "data/raw") -> str:
    zip_path = os.path.join(direction, "vllm-0.10.1.zip")
    extracted_path = os.path.join(direction, "vllm-0.10.1")

    # déjà extrait
    if os.path.exists(extracted_path):
        return extracted_path

    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"Zip file not found: {zip_path}\n"
                                "Place the vllm-0.10.1.zip file in data/raw/")

    print(f"Extraction of {zip_path}...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(direction)
        print(f"Extracted to {extracted_path}")
    except zipfile.BadZipFile:
        print("The ZIP file is corrupted or invalid.")
        sys.exit()
    except PermissionError as e:
        print("[ERROR] You don't have permission to access the "
              f"vllm file: {e}")

    return extracted_path



#def load_files():
#    files = []

#    for path in REPO_PATH.rglob("*"):
#        if not path.is_file():
#            continue
#        if any(part.startswith(".") or part in IGNORED_DIRS for part in path.parts):
#            continue
#        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
#            continue

#        try:
#            content = path.read_text(encoding="utf-8", errors="ignore")
#            rel_path = os.path.relpath(path)  # garde le même comportement que ton code actuel
#            files.append((rel_path, content))
#        except Exception as e:
#            print(f"  Impossible de lire {path}: {e}")

#    return files

#
def load_files(path_dir: str) -> List[Tuple[str, str]]:
    files = []

    # path = devient objet content fichier trouvé
    for path in Path(path_dir).rglob("*"):

        # traiter que les fichiers
        if not path.is_file():
            continue

        


# Main/Pipeline du fichier
def main_indexer(path_dir: str = "../vllm-0.10.1",
                 max_chunk_size: int = 2000) -> None:

    # extraction zip si besoin
    try:
        os.makedirs(BM25_PATH, exist_ok=True)
        os.makedirs(os.path.dirname(CHUNKS_PATH), exist_ok=True)
    except PermissionError as e:
        print("[ERROR] You don't have permission to access in "
              f"{CHUNKS_PATH}: {e}")

    print(f"Reading files in {path_dir}...")
    files = load_files(path_dir)
    print(f"   {len(files)} files found")