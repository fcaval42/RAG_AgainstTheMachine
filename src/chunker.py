# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  chunker.py                                        :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: fcaval <fcaval@student.42.fr>             +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/06/08 14:35:44 by fcaval          #+#    #+#               #
#  Updated: 2026/06/15 14:45:38 by fcaval          ###   ########.fr        #
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

        if len(block) <= max_size:
            chunks.append((file_path, start, end, block))
        else:
            #  bloc trop grand : on le redécoupe par paragraphes
            big_chunk = chunk_text(file_path, block, max_size)
            for (filepath, strt, ed, text) in big_chunk:
                chunks.append((filepath, start + strt, start + ed, text))

    return chunks


#  Découpe texte en chunks en utilisant découpage par taille fixe.
def chunk_text_size(file_path: str, content: str, max_size:
                    int) -> List[Chunk]:
    chunks = []

    parts = content.splitlines(keepends=True)
    #print(f"\n\n{parts}\n\n")

    current = ""
    current_start = 0
    position = 0

    for part in parts:
        # si nv chunk, current_start doit être la position
        if not current:
            current_start = position

        # si ajout dépasse taille max, on ferme le chunk
        if current and len(current) + len(part) > max_size:
            chunks.append((file_path, current_start,
                           current_start + len(current), current))
            #  il faut repartir avec un chunk vide
            current = part
            current_start = position
        else:
            current += part

        position += len(part)

    # dernier chunk
    if current:
        chunks.append((file_path, current_start, current_start +
                       len(current), current))
        
    return chunks


#  Découpe texte en chunks en utilisant découpage par sections (car Markdown)
#  -> on empile plusieurs paragraphes tant que reste sous max_size = un chunk
def chunk_text_markdown(file_path: str, paragraphes: list[str],
                        max_size: int) -> List[Chunk]:
    chunks = []

    current = ""        # texte accumulé pour le chunk en cours
    current_start = 0   # index de début du chunk en cours
    position = 0        # position dans content

    for para in paragraphes:
        #si ajouter le paragraphe dépasse la taille max, on ferme le chunk
        if current and len(current) + 2 + len(para) > max_size:
            end = current_start + len(current)
            chunks.append((file_path, current_start, end, current))

            #nouveau chunk qui commence à la position courante
            current_start = position
            current = para

        else:
            if current:
                current += "\n\n" + para
            else:
                current = para

        position += len(para) + 2    # +2 pour le "\n\n"

    #si dernier chunk non vide
    if current.strip():
        end = current_start + len(current)
        chunks.append((file_path, current_start, end, current))

    return chunks


#  On choisit ici si on découpe le texte en fonction de paragraphes (\n\n) ou
#  si pas de paragraphes = on découpe par taille fixe
def chunk_text(file_path: str, content: str, max_size: int) -> List[Chunk]:
    paragraphes = content.split("\n\n")
    if len(paragraphes) > 1:
        return chunk_text_markdown(file_path, paragraphes, max_size)
    else:
        return chunk_text_size(file_path, content, max_size)


#  Entrée -> choisit stratégie chunking
def chunk_choice(file_path: str, content: str, max_size: int) -> List[Chunk]:
    if file_path.lower().endswith(".py"):
        #print("\n\nJE PASSE ICI : CHUNK PYTHON\n\n")
        return chunk_python(file_path, content, max_size)
    if file_path.lower().endswith(".md"):
        #print("\n\nJE PASSE ICI : MARKDOWN\n\n")
        paragraphes = content.split("\n\n")
        return chunk_text_markdown(file_path, paragraphes, max_size)
    #print("\n\nJE PASSE ICI : TEXT\n\n")
    return chunk_text(file_path, content, max_size)


#def main():
#    with open("testerpy.py", "r") as f:
#        PYTHON_SAMPLE = f.read()

#    with open("tester.txt", "r") as f:
#        MARKDOWN_SAMPLE = f.read()

#    #liste = chunk_choice("testerpy.py", PYTHON_SAMPLE, 2000)
#    liste2 = chunk_choice("tester.txt", MARKDOWN_SAMPLE, 2000)

#    #for lst in liste:
#    #    print(f"\n\n{lst}\n\n")

#    for lste in liste2:
#        print(f"\n\n{lste}\n\n")

#main()
