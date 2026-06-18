# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  generator.py                                      :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: fcaval <fcaval@student.42.fr>             +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/06/16 11:15:18 by fcaval          #+#    #+#               #
#  Updated: 2026/06/18 14:54:55 by fcaval          ###   ########.fr        #
#                                                                           #
# ************************************************************************* #

import re
import sys
from typing import List
from transformers import pipeline, GenerationConfig
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

    print("\n" + "🚀​ Loading model: Qwen/Qwen3-0.6B" + "\n")

    # pipeline fais 3 étapes = tokenizer -> modèle -> detokenizer
    try:
        _cache_pipeline = pipeline("text-generation", model="Qwen/Qwen3-0.6B")
    except Exception as e:
        print(f"[ERROR] Failed to load model: {e}")
        sys.exit()

    print("\n" + "🌚 Model loaded !" "\n")


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


# injecte le contenu des chunks dans les messages chat
# Qwen3 est un modèle instruct/chat : il faut passer des messages formatés
# avec le chat template, pas un prompt texte brut. Sinon le modèle continue
# le contexte comme un document au lieu de répondre à la question.
def build_messages(question: str, sources: List[MinimalSource]) -> list:
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
    print("\n" + " Answer ".center(70, "=") + "\n")

    # on dit au modèle de rester fidèle aux sources et de ne pas inventer
    # /no_think désactive le mode thinking de Qwen3 qui sinon génère des
    # balises <think>...</think> avant de répondre
    return [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant. "
                "Answer the question using ONLY the provided context. "
                "Be concise and mention the source file. /no_think"
            ),
        },
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {question}",
        },
    ]


def generate_answer(question: str, sources: List[MinimalSource]) -> str:

    load_llm()

    messages = build_messages(question, sources)

    # pipeline génère du texte à partir des messages
    # on passe une liste de messages → transformers applique le chat template
    # du modèle automatiquement
    # GenerationConfig remplace les kwargs individuels pour éviter les
    # conflits avec la generation_config.json embarquée dans le modèle
    # (max_length=20, temperature, top_p, top_k incompatibles
    # avec do_sample=False)
    gen_cfg = GenerationConfig(max_new_tokens=256, do_sample=False)
    result = _cache_pipeline(messages, generation_config=gen_cfg)

    # avec le chat template, generated_text est une liste de messages ;
    # le dernier est la réponse de l'assistant
    # /no_think supprime la réflexion mais laisse des balises vides
    # <think></think> on les retire ici
    raw = result[0]["generated_text"][-1]["content"]
    answer = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

    if not answer:
        raise ValueError("No answer could be generated from the provided"
                         " context.")

    return answer
