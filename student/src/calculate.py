# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  calculate.py                                      :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: fcaval <fcaval@student.42.fr>             +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/06/18 11:15:33 by fcaval          #+#    #+#               #
#  Updated: 2026/06/21 16:28:02 by fcaval          ###   ########.fr        #
#                                                                           #
# ************************************************************************* #


# vérifie si le retriever a trouvé le bon morceau de code
# puisque découpage en chunks ne va jamais démarrer et s'arrêter exactement
# aux mêmes caractères que le corrigé (le gt), on calcule une intersection
# géométrique (overlap) entre notre texte et le vrai texte
def count_found(retrieved: list, gt_srcs: list, max_context_length:
                int) -> int:

    found = 0
    for gt in gt_srcs:
        for ret in retrieved:
            # il faut le même fichier pour comparer gt et le notre
            if ret.file_path != gt.file_path:
                continue

            # point départ le plus éloigné
            overlap_start = max(ret.first_character_index,
                                gt.first_character_index)
            # point de fin le plus proche
            overlap_end = min(min(ret.last_character_index,
                                  ret.first_character_index +
                                  max_context_length),
                              gt.last_character_index)
            # si résultat négatif pas de chevauchement, force à 0
            overlap = max(0, overlap_end - overlap_start)

            gt_length = gt.last_character_index - gt.first_character_index
            if gt_length > 0 and overlap / gt_length >= 0.05:
                found += 1
                # source trouvée on passe à la suivante
                break

    return found
