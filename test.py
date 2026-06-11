import ast

#tree = ast.parse("print('Hello World!')")
#print(ast.dump(tree, indent=4))

# Parser le code en arbre
tree = ast.parse("print('Hello World!')")

# Compiler l'arbre en code Python exécutable
code_obj = compile(tree, filename="<ast>", mode="exec")

# Exécuter le code
exec(code_obj)
