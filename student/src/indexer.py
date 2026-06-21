# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  indexer.py                                        :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: fcaval <fcaval@student.42.fr>             +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/06/11 16:50:18 by fcaval          #+#    #+#               #
#  Updated: 2026/06/21 16:28:23 by fcaval          ###   ########.fr        #
#                                                                           #
# ************************************************************************* #

import os
import sys
import bm25s
import pickle
import zipfile
from tqdm import tqdm
from pathlib import Path
from typing import List, Tuple
from .chunker import chunk_choice


#  Fichiers qu'on ignore
IGNORED_DIRS = {"__pycache__", "node_modules"}


# Racine du projet (student/src/ -> student/ -> project_root/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

#  Chemins de sauvegarde de l'index demandé par le sujet
INDEX_DIR = str(_PROJECT_ROOT / "data" / "processed")
BM25_PATH = str(_PROJECT_ROOT / "data" / "processed" / "bm25_index")
CHUNKS_PATH = str(_PROJECT_ROOT / "data" / "processed" / "chunks" /
                  "chunks.pkl")


# Charge index BM25 et métadonnées depuis le disque
def load_index() -> Tuple[bm25s.BM25, List[Tuple[str, int, int]]]:
    if not os.path.exists(BM25_PATH):
        raise FileNotFoundError("Index BM25 not found. First run:\n"
                                "  uv run python -m student index")

    if not os.path.exists(CHUNKS_PATH):
        raise FileNotFoundError("Chunk metadata not found. Retrying:\n"
                                "  uv run python -m student index")

    # chargement index BM25 (load_corpus=False car on a pas besoin de
    # recharger le texte vu qu'on l'a déjà, tu captes ?)
    retriever = bm25s.BM25.load(BM25_PATH, load_corpus=False)

    with open(CHUNKS_PATH, 'rb') as f:
        chunk_metadata = pickle.load(f)

    return retriever, chunk_metadata


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

    print("\n" + f"📁​ Extraction of {zip_path}...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(direction)
        print(f"     Extracted to {extracted_path}")
    except zipfile.BadZipFile:
        print("[ERROR] The ZIP file is corrupted or invalid.")
        sys.exit()
    except PermissionError as e:
        print("[ERROR] You don't have permission to access the "
              f"vllm file: {e}")
        sys.exit()

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
        if any(part.startswith(".") or part in IGNORED_DIRS
               for part in path.parts):
            continue

        try:
            # errors -> si caractères bizarres ou pas purement textuel
            with open(path, 'r', encoding='utf-8', errors="ignore") as file:
                content = file.read()

            # Chemin relatif à la racine du projet pour que la comparaison
            # avec le ground truth du moulinette soit cohérente, quel que
            # soit le CWD au moment de l'appel.
            try:
                relatif_path = str(path.resolve().relative_to(_PROJECT_ROOT))
            except ValueError:
                relatif_path = str(path)

            files.append((relatif_path, content))

        except Exception as e:
            print(f"[ERROR] Unreadable {path_dir}: {e}")
            sys.exit()

    return files


# Main/Pipeline du fichier
def main_indexer(path_dir: str, max_chunk_size: int) -> None:

    print("\n" + "\n" + "INDEXER".center(70, "-"))

    # extraction zip si besoin
    try:
        os.makedirs(BM25_PATH, exist_ok=True)
        os.makedirs(os.path.dirname(CHUNKS_PATH), exist_ok=True)
    except PermissionError as e:
        print("[ERROR] You don't have permission to access in "
              f"{CHUNKS_PATH}: {e}")
        sys.exit()

    # on load les fichiers
    print(f"\n📖​ Reading files in {path_dir}...")
    files = load_files(path_dir)
    print(f"     {len(files)} files found")

    # Découpage en chunks de tous les fichiers
    all_chunks = []
    for file_path, content in tqdm(files, desc="Chunking"):
        chunks = chunk_choice(file_path, content, max_chunk_size)
        all_chunks.extend(chunks)

    print(f"     {len(all_chunks)}: Total number of chunks created")

    # BM25 tokenise les textes
    # on va chercher le 4eme élément du tuple qui correspond au contenu texte
    # stopwords="en" -> ignore mots fréquents qui servent à r (the, a, is...)
    chunks_text = [chunk[3] for chunk in all_chunks]
    print("\n🖥️​ Corpus tokenization...")
    tokenized_text = bm25s.tokenize(chunks_text, stopwords="en",
                                    show_progress=False)

    # Construction index BM25 sur texte tokenisé et nettoyé
    print("\n📚 Construction of the BM25 Index...")
    retriever = bm25s.BM25()
    retriever.index(tokenized_text, show_progress=False)

    # sauvegarde de l'index BM25 sur disque (pour pouvoir le recharger sans
    # recalculer)
    retriever.save(BM25_PATH)
    print(f"     💾 BM25 index saved in {BM25_PATH}")

    # on sauvegarde les métadonnées des chunks séparément (file_path +
    # position). Pas besoin de stocker
    chunk_metadata = [(fp, start, end) for (fp, start, end, _) in all_chunks]
    try:
        with open(CHUNKS_PATH, "wb") as f:
            pickle.dump(chunk_metadata, f)
        print(f"     💾 Metadata chunks saved in {CHUNKS_PATH}")
    except pickle.PicklingError:
        print("Unable to serialize the chunk metadata.")
        sys.exit()
    except FileNotFoundError:
        print(f"The destination folder for {CHUNKS_PATH} does "
              "not exist.")
        sys.exit()

    print("\n" + "Ingestion complete! The indexes have been saved to "
          "the data/processed/directory".center(80, " ") + "\n")


# if __name__ == "__main__":
#    main_indexer("vllm-0.10.1")
