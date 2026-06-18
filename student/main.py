# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  main.py                                           :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: fcaval <fcaval@student.42.fr>             +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/06/08 13:43:02 by fcaval          #+#    #+#               #
#  Updated: 2026/06/18 16:45:11 by fcaval          ###   ########.fr        #
#                                                                           #
# ************************************************************************* #

import os
import sys
import tqdm
import json
import fire
from student.retriever import search
from student.calculate import count_found
from student.indexer import main_indexer, load_index
from student.generator import generate_answer
from student.structure import MinimalSearchResults, MinimalAnswer, \
    RagDataset, StudentSearchResults, StudentSearchResultsAndAnswer,AnsweredQuestion

ERROR = "\033[5m\033[31m[ERROR]\033[0m"


# Système RAG -> commande pour le CLI
class RAGSystem():

    # indexe le repository vLLM et sauvegarde l'index BM25
    # = crée juste la base de données
    def index(self, repo_path: str = "data/raw/vllm-0.10.1",
              max_chunk_size: int = 2000) -> None:

        try:
            main_indexer(repo_path, max_chunk_size)
        except Exception as e:
            print("\n" + ERROR + f" {e}\n")
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
        print("\n" + " Result of search ".center(70, "°") + "\n")
        print(result.model_dump_json(indent=2))
        print(" OK search ".center(70, "°") + "\n")


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
        print("\n" + f"  ❓ Processing {len(questions)} questions...")

        # on extrait toutes les questions pour le batch
        requests_text = [q.question for q in questions]

        print("  🔍 ​BM25 Search in Progress...")
        all_sources = search(requests_text, retriever, chunk_metadata, k=k)

        all_results = []
        print("\n")
        for question, sources in tqdm.tqdm(zip(questions, all_sources),
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

        print("\n" + "✅​ Saved student_search_results to "
              f"{save_path}".center(100, " ") + "\n")


    # génère réponses pour toutes les questions d'un fichier de resultats
    # = prend fichier JSON, lit les chunks trouvés et utilise le LLM pour
    # répondre à la chaîne
    def answer_dataset(self, student_search_results_path: str,
                       save_directory: str = \
                        "data/output/search_results_and_answer") -> None:

        if not os.path.exists(student_search_results_path):
            print("\n" + ERROR + ": dataset not "
                  f"found ({student_search_results_path})")
            sys.exit()

        with open(student_search_results_path, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        search_results = StudentSearchResults.model_validate(raw)

        total = len(search_results.search_results)
        print(f"Loaded {total} questions from {student_search_results_path}")

        all_answers = []
        for i, result in enumerate(tqdm.tqdm(
            search_results.search_results, desc="Generating answers")):
            answer_text = generate_answer(
                result.question_str, result.retrieved_sources)
            all_answers.append(MinimalAnswer(question_id=result.question_id,
                                             question_str=result.question_str,
                                             retrieved_sources=\
                                                result.retrieved_sources,
                                                answer=answer_text))

            print(f"Processed {i + 1} of {total} questions")

        output = StudentSearchResultsAndAnswer(search_results=all_answers,
                                               k=search_results.k)

        os.makedirs(save_directory, exist_ok=True)
        filename = os.path.basename(student_search_results_path)
        save_path = os.path.join(save_directory, filename)

        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(output.model_dump_json(indent=2))

        print("\n" + "✅​ Saved student_search_results_and_answer "
              f"to {save_path}".center(120, " ") + "\n")


    # Evalue résultats de recherche avec la métrique recall@k.
    # on monte à k=10 car si recall@5 = 40% mais que recall@10 = 90% -> 
    # retriever trouve bonnes infos, mais mal classées. Dans le code, on prend
    # les 10 premiers résultats, mais pour calculer Recall@5, on recoupe la
    # liste pour ne garder que les 5 premiers.
    def evaluate(self, student_answer_path: str, dataset_path: str,
                 k: int = 10, max_context_length : int = 2000) -> None:
        
        print("\n" + " EVALUATE ".center(70, "~") + "\n")

        if not os.path.exists(student_answer_path):
            print("\n" + ERROR + f"{student_answer_path} not found\n")
            sys.exit()

        if not os.path.exists(dataset_path):
            print("\n" + ERROR + f": dataset not found ({dataset_path})\n")
            sys.exit()

        with open(student_answer_path, 'r', encoding='utf-8') as f:
            student_raw = json.load(f)
        student_results = StudentSearchResults.model_validate(student_raw)

        with open(dataset_path, 'r', encoding='utf-8') as f:
            gt_raw = json.load(f)
        gt_dataset = RagDataset.model_validate(gt_raw)

        # gt veut dire Ground Truth. Créé dico pour lister les bonnes réponses
        # dico indexé par identifiant de la question (question_id) = trouver 
        # corrigé de n'importe quelle question instantanément
        # {"q_1" : [vrais_chunks_utiles], ...}
        gt_by_id = {}
        for q in gt_dataset.rag_questions:
            if isinstance(q, AnsweredQuestion):
                gt_by_id[q.question_id] = q.sources

        # stocke les notes de Recall obtenues pour chaque question.
        # à la fin on fera la moyenne de ces listes pour obtenir le score
        # final de recall@5
        recall_scores = {1: [], 3: [], 5: [], 10: []}

        # boucle principale => comparaison. On prend les résultats pour les 
        # #noter
        for student_q in student_results.search_results:
            qid = student_q.question_id
            # si question pas dans le corrigé, bye bye
            if qid not in gt_by_id:
                continue

            # on récupère la bonne réponse (le corrigé)
            gt_src = gt_by_id[qid]
            #on prend les k meilleurs résultats
            retrieved = student_q.retrieved_sources[:k]

            # va boucler sur top1, top3, top5 et top10
            for k_val in recall_scores.keys():
                retrieved_k = retrieved[:k_val]
                
                # on compte combien de vraies sources on a trouvées dans le 
                # top
                found = count_found(retrieved_k, gt_src, max_context_length)

                # calcul le % de réussite pour la question
                score = found / len(gt_src) if gt_src else 0.0

                recall_scores[k_val].append(score)

            # permet évaluer combien de questions ont été évaluées
            # 1 = si liste pas vide sinon on prend la valeur 1
            n = len(recall_scores[1]) if recall_scores[1] else 1

            print("\n👨‍🎓 Student data is valid: True")
            print(f"  Total number of questions: {len(
                student_results.search_results)}")
            print(f"  Total number")

            CONTINUER ICI


# lance le CLI avec Python Fire
def main() -> None:
    fire.Fire(RAGSystem)


if __name__ == "__main__":
    main()
