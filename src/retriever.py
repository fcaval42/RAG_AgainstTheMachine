# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  retriever.py                                      :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: fcaval <fcaval@student.42.fr>             +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/06/15 15:36:23 by fcaval          #+#    #+#               #
#  Updated: 2026/06/16 11:03:26 by fcaval          ###   ########.fr        #
#                                                                           #
# ************************************************************************* #

import bm25s
from typing import List, Tuple
from src.structure import MinimalSource


#  cherche les k chunks, pour une seule question, donc on refait la même pour
#  request que ce qu'on a fait pour indexer
def search(request: List[str], retriever: bm25s.BM25, chunk_metadata:
           List[Tuple[str, int, int]], k: int = 5) -> List[MinimalSource]:

    # mettre faux show parce que sinon on va avoir une barre de progression
    tokenized_request = bm25s.tokenize(request, stopwords="en",
                                       show_progress=False)

    # éviter dépassement
    mini_k = min(k, len(chunk_metadata))

    # ici, on prend les meilleurs résultats
    results, scores = retriever.retrieve(tokenized_request, k=mini_k,
                                         show_progress=False)

    all_sources = []
    for request_result in results:
       sources = []
       for idx in request_result:
            file_path, start, end = chunk_metadata[int(idx)]
            sources.append(MinimalSource(file_path=file_path,
                                         first_character_index=start,
                                         last_character_index=end))
       all_sources.append(sources)

       return all_sources