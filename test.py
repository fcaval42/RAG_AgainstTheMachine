import ast

#tree = ast.parse("print('Hello World!')")
#print(ast.dump(tree, indent=4))

# Parser le code en arbre
tree = ast.parse("print('Hello World!')")

# Compiler l'arbre en code Python exécutable
code_obj = compile(tree, filename="<ast>", mode="exec")

# Exécuter le code
exec(code_obj)



def chunk_text_simple(file_path: str, content: str, max_size: int) -> List[Chunk]:
    chunks: List[Chunk] = []
    # on garde les retours de ligne pour conserver les indices exacts
    units = content.splitlines(keepends=True)

    pos = 0               # position dans content (début de l'unité courante)
    current = ""          # texte accumulé pour le chunk en cours
    current_start = 0     # index de début du chunk en cours

    for u in units:
        # si on commence un nouveau chunk, current_start doit être la pos actuelle
        if not current:
            current_start = pos

        # si l'ajout dépasse la taille max, on ferme le chunk courant
        if current and len(current) + len(u) > max_size:
            chunks.append((file_path, current_start, current_start + len(current), current))
            current = u
            current_start = pos
        else:
            current += u

        pos += len(u)

    # dernier chunk
    if current:
        chunks.append((file_path, current_start, current_start + len(current), current))

    return chunks