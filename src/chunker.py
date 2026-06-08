# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  chunker.py                                        :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: fcaval <fcaval@student.42.fr>             +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/06/08 14:35:44 by fcaval          #+#    #+#               #
#  Updated: 2026/06/08 16:18:20 by fcaval          ###   ########.fr        #
#                                                                           #
# ************************************************************************* #

import os
from typing import List, Tuple


#  Chunk = (chemin du fichier, index début, index fin, texte du chunk)
Chunk = Tuple[str, int, int, str]


#  Découpe texte en chunks en utilisant découpage par sections (car Markdown)
def chunk_text(file_path: str, content: str, max_size: int) -> List[Chunk]:
    faire le code section et après le python 


#  Entrée -> choisit stratégie chunking
def chunk_choice(file_path: str, content: str, max_size: int) -> List[Chunk]:
    if file_path.find(".py"):
        return chunk_python(file_path, content, max_size)
    else:
        return chunk_text(file_path, content, max_size)