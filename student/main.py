# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  main.py                                           :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: fcaval <fcaval@student.42.fr>             +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/06/08 13:43:02 by fcaval          #+#    #+#               #
#  Updated: 2026/06/17 17:09:03 by fcaval          ###   ########.fr        #
#                                                                           #
# ************************************************************************* #

import os
import sys
import tqdm
import json
import fire
from student.retriever import search
from student.indexer import main_indexer, load_index
from student.generator import generate_answer
from student.structure import MinimalSearchResults, MinimalAnswer, \
    RagDataset, StudentSearchResults

ERROR = "\033[5m\033[31m[ERROR]\033[0m"


# Système RAG -> commande pour le CLI
class RAGSystem():

    # indexe le repository vLLM et sauvegarde l'index BM25
    # = crée juste la base de données
    def index(self, repo_path: str = "data/raw/vllm-0.10.1",
              max_chunk_size: int = 2000) -> None:

        try:
            main_indexer(repo_path=repo_path, max_chunk_size=max_chunk_size)
        except Exception as e:
            print("\n" + ERROR + f"{e}\n")
            sys.exit()


    # recherche les k chunks les plus pertinents pour la requête
    # = teste uniquement le retriever sur une question. Appelle pas llm. 
    # affiche juste si BM25 a trouvé les bons fichiers
    def search(self, request: str, k: int = 5) -> None:

        if not request or not request.strip():
            print("\n" + ERROR + ": the request cannot be empty")
            sys.exit()

        try:
            retriever, chunk_metadata = load_index()
        except FileNotFoundError as e:
            print("\n" + ERROR + f"{e}\n")
            sys.exit()

        sources = search(request, retriever, chunk_metadata, k=k)

        result = MinimalSearchResults(question_id="single-query",
            question_str=request, retrieved_sources=sources)

        # on peut utiliser direct la méthode json car pydantic v2
        print(result.model_dump_json(indent=2))


    # répond à la question en récupérant le contexte puis en générant réponse
    # = teste la chaîne RAG complète sur une question (mot-clés -> BM25 ->
    # création prompt -> LLM -> réponse)
    def answer(self, request: str, k: int = 5) -> None:

        if not request or not request.strip():
            print("\n" + ERROR + ": the request cannot be empty")
            sys.exit()

        try:
            retriever, chunk_metadata = load_index()
        except FileNotFoundError as e:
            print("\n" + ERROR + f"{e}\n")
            sys.exit()

        # étape 1 : récupération chunks pertinents
        sources = search(request, retriever, chunk_metadata, k=k)

        # étape 2 : génération réponse avec le LLM
        answer_text = generate_answer(request, sources)

        result = MinimalAnswer(question_id="single-query",
                               question_str=request,
                               retrieved_sources=sources,
                               answer=answer_text)

        print(result.model_dump_json(indent=2))


    # traite un dataset de questions et sauvgarde les résultats
    # = prend tout d'un coup via calcul en lot
    def search_dataset(self, dataset_path: str, k: int = 10,
                       save_directory: \
                        str = "data/output/search_results") -> None:

        if not os.path.exists(dataset_path):
            print("\n" + ERROR + f": dataset not found ({dataset_path})")
            sys.exit()

        try:
            retriever, chunk_metadata = load_index()
        except FileNotFoundError as e:
            print("\n" + ERROR + f"{e}\n")
            sys.exit()

        # chargement du dataset
        with open(dataset_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        # transforme en objet python + plantera si JSON malformé ou corrompu
        dataset = RagDataset.model_validate(raw)

        questions = dataset.rag_questions
        print(f"Processing {len(questions)} questions...")

        # on extrait toutes les questions pour le batch
        requests_text = [q.question for q in questions]

        print("BM25 Search in Progress...")
        all_sources = search(requests_text, retriever, chunk_metadata, k=k)

        all_results = []
        for question, sources in tqdm(zip(questions, all_sources),
                                          total=len(questions),
                                          desc="Formatting the results"):
            all_results.append(MinimalSearchResults(
                question_id=question.question_id,
                question_str=question.question,
                retrieved_sources=sources))
            
        output = StudentSearchResults(search_results=all_results, k=k)

        # sauvegarde avec même nom de fichier que le dataset d'entrée
        os.makedirs(save_directory, exist_ok=True)
        filename = os.path.basename(dataset_path)
        save_path = os.path.join(save_directory, filename)

        with open(save_path, "w", encoding="utf-8") as f:
            f.write(output.model_dump_json(indent=2))

        print(f"Saved student_search_results to {save_path}")



    # génère réponses pour toutes les questions d'un fichier de resultats
    # = 



# lance le CLI avec Python Fire
def main() -> None:
    fire.Fire(RAGSystem)


if __name__ == "__main__":
    main()