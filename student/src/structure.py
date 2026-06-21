# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  structure.py                                      :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: fcaval <fcaval@student.42.fr>             +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/06/08 13:53:11 by fcaval          #+#    #+#               #
#  Updated: 2026/06/17 14:33:21 by fcaval          ###   ########.fr        #
#                                                                           #
# ************************************************************************* #

from typing import List
from pydantic import BaseModel


#   Représente un morceau de fichier récupéré (chemin +     #
#       position dans le fichier)                           #
class MinimalSource(BaseModel):
    file_path: str                  # chemin du fichier
    first_character_index: int      # où commence le chunk dans le fichier
    last_character_index: int       # où il finit


#  Question sans réponse (juste la question + un id unique  #
class UnansweredQuestion(BaseModel):
    question_id: str
    question: str


#  Question avec réponse + sources utilisées  #
class AnsweredQuestion(UnansweredQuestion):
    sources: List[MinimalSource]
    answer: str


#  Dataset complet (peut mélanger questions répondues et non répondues) #
class RagDataset(BaseModel):
    rag_questions: List[AnsweredQuestion | UnansweredQuestion]


#  Le retriever met les meilleurs chunks et la question dedans #
class MinimalSearchResults(BaseModel):
    question_id: str
    question_str: str
    retrieved_sources: List[MinimalSource]


#  Résultat de recherche + réponse générée par le LLM  #
class MinimalAnswer(MinimalSearchResults):
    answer: str


#  Ensemble des résultats de recherche pour tout un dataset  #
class StudentSearchResults(BaseModel):
    search_results: List[MinimalSearchResults]
    k: int


#  Même chose mais avec les réponses générées  #
class StudentSearchResultsAndAnswer(StudentSearchResults):
    search_results: List[MinimalAnswer]  # type: ignore[assignment]
