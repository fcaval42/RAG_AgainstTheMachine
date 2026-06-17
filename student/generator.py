# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  generator.py                                      :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: fcaval <fcaval@student.42.fr>             +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/06/16 11:15:18 by fcaval          #+#    #+#               #
#  Updated: 2026/06/17 14:59:18 by fcaval          ###   ########.fr        #
#                                                                           #
# ************************************************************************* #

import sys
from typing import List
from transformers import pipeline
from student.structure import MinimalSource

# on garde le modèle en mémoire entre les appels pour éviter de recharger
# à chaque fois (voir principe singleton)
_cache_pipeline = None


# charge modèle llm si pas encore chargé
def load_llm() -> None:
    global _cache_pipeline

    # si déjà chargé = ok
    if _cache_pipeline is not None:
        return

    print("Loading model: Qwen/Qwen3-0.6B")

    # pipeline fais 3 étapes = tokenizer -> modèle -> detokenizer
    try:
        _cache_pipeline = pipeline("text-generation", model="Qwen/Qwen3-0.6B")
    except Exception as e:
        print(f"[ERROR] Failed to load model: {e}")
        sys.exit()

    print("Model loaded !")


# relit le fichier source pour extraire le texte exact du chunk
def read_chunk(source: MinimalSource) -> str:
    try:
        with open(source.file_path, "r", encoding="utf-8",
                  errors="ignore") as f:
            content = f.read()
        return content[
            source.first_character_index:source.last_character_index]
    except Exception:
        # si fichier existe plus on ignore le chunk
        return ""


# injecte le contenu des chunks dans le prompt
def build_prompt(question: str, sources: List[MinimalSource]) -> str:
    # on protège la mémoire du llm = ne pas dépasser sa fenêtre de contexte
    # si on ne met pas de limite on peut avoir un llm qui hallucine
    # option : couper si on va dépasser. Le retriever classe des meilleurs
    # chunks au moins ouf.
    context_parts = []
    budget = 3000

    for src in sources:
        chunk_text = read_chunk(src)
        if not chunk_text:
            continue
        if len(chunk_text) > budget:
            chunk_text = chunk_text[:budget]
            # on source pour LLM puisse citer ses sources dans sa réponse
            context_parts.append(f"[Source: {src.file_path}]\n{chunk_text}"
                                 "(truncated...)")
            break

        context_parts.append(f"[Source: {src.file_path}]\n{chunk_text}")
        budget -= len(chunk_text)

    context = "\n\n---\n\n".join(context_parts)

    # on dit au modèle de rester fidèle aux sources et de ne pas inventer
    prompt = (
        "You are a helpful assistant. "
        "Answer the question using ONLY the provided context. "
        "Be concise and mention the source file. \n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer:"
    )

    return prompt


def generate_answer(question: str, sources: List[MinimalSource]) -> str:

    load_llm()

    prompt = build_prompt(question, sources)

    # pipeline génère du texte à partir du prompt
    # do_sample=False -> empêche IA d'être créatif dans la réponse
    # return_full_text=False -> pipeline retourne prompt + réponse ensemble
    #   on enlève le prompt pour garder uniquement la réponse
    result = _cache_pipeline(prompt, max_new_tokens=256, do_sample=False,
                             return_full_text=False)

    answer = result[0]["generated_text"].strip()

    if not answer:
        raise ValueError("No answer could be generated from the provided"
                         " context.")

    return answer
