# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  chunker.py                                        :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: fcaval <fcaval@student.42.fr>             +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/06/08 14:35:44 by fcaval          #+#    #+#               #
#  Updated: 2026/06/10 16:51:01 by fcaval          ###   ########.fr        #
#                                                                           #
# ************************************************************************* #

import ast
from typing import List, Tuple


#  Chunk = (chemin du fichier, index début, index fin, texte du chunk)
Chunk = Tuple[str, int, int, str]


#  Découpe fichier Python en chunks par fonctions et classes
def chunk_python(file_path: str, content: str, max_size: int) -> List[Chunk]:
    chunks = []

    try:
        tree = ast.parse(content)
    except SyntaxError:
        #si fichier écrit bizarrement etc, on découpe en mode texte
        return chunk_text(file_path, content, max_size)

    #calcul des positions de chaque début de ligne pour convertir en AST
    lines = content.split("\n")
    line_start = []
    position = 0
    for line in lines:
        line_start.append(position)
        position += len(line) + 1

    #  prend les "branches" qui sont des fonctions et des classes principales
    direct_branch = []
    for branch in tree.body:
        if isinstance(branch, (ast.FunctionDef, ast.AsyncFunctionDef,
                               ast.ClassDef)):
            direct_branch.append(branch)

    #  pas de fonctions/classes : découpage texte simple
    if not direct_branch:
        return chunk_text(file_path, content, max_size)

    #  on va découper en fonction de la ligne de début et de fin dans le
    #  fichier d'origine
    for branch in direct_branch:
        start = line_start[branch.lineno - 1]
        end_line = getattr(branch, 'end_lineno', branch.lineno)

        #  ne pas dépasser fin du fichier
        if end_line < len(line_start):
            end = line_start[end_line]
        else:
            end = len(content)

        block = content[start:end]

        if len(block) <= max:
            chunks.append(file_path, start, end, block)
        else:
            #  bloc trop grand : on le redécoupe par paragraphes
            big_chunk = chunk_text(file_path, block, max_size)
            for (filepath, strt, ed, text) in big_chunk:
                chunks.append(filepath, start + strt, start + ed, text)

    return chunks


#  Découpe texte en chunks en utilisant découpage par sections (car Markdown)
#  -> on empile plusieurs paragraphes tant que reste sous max_size = un chunk
def chunk_text(file_path: str, content: str, max_size: int) -> List[Chunk]:
    chunks = []
    paragraphes = content.split("\n\n")

    current_chunk = ""
    current_start = 0
    position = 0

    for para in paragraphes:
        #si ajouter le paragraphe dépasse la taille max, on ferme le chunk
        if current_chunk and len(current_chunk) + 2 + len(para) > max_size:
            end = current_start + len(current_chunk)
            chunks.append((file_path, current_chunk, end, current_chunk))

            #nouveau chunk qui commence à la position courante
            current_start = position
            current_chunk = para

        else:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para

        position += len(para) + 2    # +2 pour le "\n\n"

    #si dernier chunk non vide
    if current_chunk.strip():
        end = current_start + len(current_chunk)
        chunks.append(file_path, current_start, end, current_chunk)

    return chunks


#  Entrée -> choisit stratégie chunking
def chunk_choice(file_path: str, content: str, max_size: int) -> List[Chunk]:
    if file_path.find(".py"):
        return chunk_python(file_path, content, max_size)
    else:
        return chunk_text(file_path, content, max_size)



VOIR ERREUR 