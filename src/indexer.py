# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  indexer.py                                        :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: fcaval <fcaval@student.42.fr>             +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/06/11 16:50:18 by fcaval          #+#    #+#               #
#  Updated: 2026/06/12 16:20:55 by fcaval          ###   ########.fr        #
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


Cette ligne de code sert à filtrer et ignorer les fichiers ou dossiers cachés et inutiles du dépôt 
vLLM pour éviter de polluer votre index de recherche.  C'est une excellente '
'sécurité pour votre projet. Décomposons son fonctionnement :1. path.parts '
'(Le découpage du chemin)La propriété .parts (fournie par pathlib) découpe '
'le chemin complet d'un fichier en une liste contenant chaque dossier et le 
nom du fichier.Si le chemin est : 
data/raw/vllm-0.10.1/.github/workflows/ci.ymlpath.parts va renvoyer : 
('data', 'raw', 'vllm-0.10.1', '.github', 'workflows', 'ci.yml')2. 
part.startswith(".") (Détecter le caché)En informatique (particulièrement 
                                                         sous Linux/macOS), 
tout fichier ou dossier dont le nom commence par un point est caché (ex: .git, 
.github, .vscode, .gitignore).
Ces dossiers contiennent des configurations ou l'historique Git, et non du'
' code source ou de la documentation vLLM utile à indexer.  3. part in '
'IGNORED_DIRS (Détecter les dossiers exclus)Cela vérifie si l'un des 
morceaux du chemin se trouve dans une liste personnalisée de dossiers à 
bannir (que vous devez définir plus haut dans votre code, par exemple : 
        IGNORED_DIRS = ["__pycache__", "node_modules", "build"]).4. 
Le any(...) (La condition globale)La fonction any() renvoie True si au 
moins un des éléments de la boucle respecte l'une des conditions.'
'En résuméCette ligne dit à Python :"Regarde chaque dossier qui compose'
' le chemin de ce fichier. Si l'un de ces dossiers commence par un point 
(dossier caché) ou s'appelle comme un dossier à ignorer (comme __pycache__), '
'alors renvoie True."Dans votre code, vous l'utiliserez généralement avec un 
continue pour passer directement au fichier suivant sans le découper en chunks
:

#
def load_files(path_dir: str) -> List[Tuple[str, str]]:
    files = []

    # path = devient objet content fichier trouvé
    for path in Path(path_dir).rglob("*"):

        # traiter que les fichiers
        if not path.is_file():
            continue

        CONTINUER A VOIR POUR LOAD LES FICHIERS 


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