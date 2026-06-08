# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  chunker.py                                        :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: fcaval <fcaval@student.42.fr>             +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/06/08 14:35:44 by fcaval          #+#    #+#               #
#  Updated: 2026/06/08 15:25:01 by fcaval          ###   ########.fr        #
#                                                                           #
# ************************************************************************* #

import os
from typing import List, Tuple


#  Chunk = (chemin du fichier, index début, index fin, texte du chunk)
Chunk = Tuple[str, int, int, str]


#  Entrée -> choisit stratégie chunking
def chunk_choice(file_path: str, content: str, max_size: int) -> List[Chunk]:
    if file_path.find(".py"):
        return chunk_python(file_path, content, max_size)