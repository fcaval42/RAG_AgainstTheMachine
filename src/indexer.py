# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  indexer.py                                        :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: fcaval <fcaval@student.42.fr>             +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/06/11 16:50:18 by fcaval          #+#    #+#               #
#  Updated: 2026/06/15 12:01:19 by fcaval          ###   ########.fr        #
#                                                                           #
# ************************************************************************* #

import os
import sys
import zipfile
from tqdm import tqdm
import bm25s
from pathlib import Path
from typing import List, Tuple
from src.chunker import chunk_choice, Chunk


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


# Retourne fichiers supportés
def load_files(path_dir: str) -> List[Tuple[str, str]]:
    files = []

    # path = devient objet contenant fichier trouvé
    for path in Path(path_dir).rglob("*"):

        # traiter que les fichiers
        if not path.is_file():
            continue

        # vérifie fichiers cachés ou si on veut l'ignorer
        for part in path.parts:
            if any(part.startswith(".") or part in IGNORED_DIRS):
                continue

        try:
            # errors -> si caractères bizarres ou pas purement textuel
            with open(path, 'r', encoding='utf-8', errors="ignore") as file:
                content = file.read()

            #  On construit le chemin relatif depuis la racine du projet
            # (data/raw/...) car c'est ce que la moulinette utilise pour
            # comparer
            relatif_path = os.path.relpath(path)

            files.append((relatif_path, content))

        except Exception as e:
            print(f"Unreadable {relatif_path}: {e}")

    return files


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

    # on load les fichiers
    print(f"Reading files in {path_dir}...")
    files = load_files(path_dir)
    print(f"   {len(files)} files found")

    # Découpage en chunks de tous les fichiers
    all_chunks = []
    for file_path, content in tqdm(files, desc="Chunking"):
        chunks = chunk_choice(file_path, content, max_chunk_size)
        all_chunks.extend(chunks)

    print(f"{len(all_chunks)}: Total number of chunks created")

    # BM25 tokenise les textes
    # on va chercher le 4eme élément du tuple qui correspond au contenu texte
    # stopwords="en" -> ignore mots fréquents qui servent à r (the, a, is...)
    chunks_text = [chunk[3] for chunk in all_chunks]
    print("Corpus tokenization...")
    tokenized_text = bm25s.tokenize(chunks_text, stopwords="en")