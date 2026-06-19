# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  Makefile                                          :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: fcaval <fcaval@student.42.fr>             +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/04/24 13:54:45 by fcaval          #+#    #+#               #
#  Updated: 2026/06/19 18:05:53 by fcaval          ###   ########.fr        #
#                                                                           #
# ************************************************************************* #

UV		= uv run python -m student.src

RAW_SEARCH_QUERY	= $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
RAW_ANSWER_QUERY	= $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))

# Dataset par défaut (peut être surchargé : make search_dataset DATASET=...)
DATASET		= datasets_public/public/UnansweredQuestions/dataset_docs_public.json
# Ground truth pour evaluate (AnsweredQuestions = corrigé)
GT_DATASET	= datasets_public/public/AnsweredQuestions/dataset_docs_public.json
SEARCH_OUT	= data/output/search_results
ANSWER_OUT	= data/output/search_results_and_answer
REPO		= data/raw/vllm-0.10.1
K		= 10

RED		= \033[0;31m
GREEN		= \033[0;32m
YELLOW		= \033[0;33m
BLUE		= \033[0;34m
PINK		= \033[35m
NC		= \033[0m

ifneq ($(filter search answer,$(firstword $(MAKECMDGOALS))),)
.DEFAULT:
	@:
endif

# ── Targets obligatoires (sujet) ────────────────────────────────────────── #

install :
	uv venv .venv --python 3.10
	uv sync

run :
	@$(UV)

debug :
	@uv run python -m pdb -m student.src

all : help

help :
	@echo ""
	@echo "$(BLUE)╔══════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║              RAG — commandes Make            ║$(NC)"
	@echo "$(BLUE)╚══════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "  $(GREEN)make index$(NC)              Indexe le repo vLLM (BM25)"
	@echo "  $(GREEN)make search Q=\"...\"$(NC)    Teste le retriever sur une question"
	@echo "  $(GREEN)make answer Q=\"...\"$(NC)    Chaîne RAG complète sur une question"
	@echo "  $(GREEN)make search_dataset$(NC)     Recherche sur tout le dataset"
	@echo "  $(GREEN)make answer_dataset$(NC)     Génère les réponses LLM pour le dataset"
	@echo "  $(GREEN)make evaluate$(NC)           Calcule le Recall@k"
	@echo ""
	@echo "  $(YELLOW)make lint$(NC)               Flake8 + mypy"
	@echo "  $(YELLOW)make lint-strict$(NC)        Mypy strict"
	@echo "  $(YELLOW)make clean$(NC)              Supprime caches Python"
	@echo "  $(YELLOW)make clean_index$(NC)        Supprime l'index BM25"
	@echo "  $(YELLOW)make clean_output$(NC)       Supprime les fichiers de sortie"
	@echo "  $(YELLOW)make fclean$(NC)             Tout nettoyer"
	@echo ""

# ── Pipeline RAG ────────────────────────────────────────────────────────── #

index :
	@echo ""
	@echo "$(YELLOW)INDEXATION EN COURS...$(NC)"
	@$(UV) index --repo_path=$(REPO)
	@echo "$(GREEN)INDEX OK$(NC)"

# make search Q="What is vLLM ?"
search :
	@QUERY="$(strip $(if $(Q),$(Q),$(RAW_SEARCH_QUERY)))"; \
	echo ""; \
	echo "$(BLUE)SEARCH : $$QUERY$(NC)"; \
	$(UV) search --request="$$QUERY" --k=$(K)

# make answer Q="What is vLLM ?"
answer :
	@QUERY="$(strip $(if $(Q),$(Q),$(RAW_ANSWER_QUERY)))"; \
	echo ""; \
	echo "$(BLUE)ANSWER : $$QUERY$(NC)"; \
	$(UV) answer --request="$$QUERY" --k=$(K)

search_dataset :
	@echo ""
	@echo "$(YELLOW)SEARCH DATASET : $(DATASET)$(NC)"
	@$(UV) search_dataset --dataset_path=$(DATASET) --k=$(K) \
		--save_directory=$(SEARCH_OUT)
	@echo "$(GREEN)SEARCH DATASET OK$(NC)"

answer_dataset :
	@echo ""
	@echo "$(YELLOW)ANSWER DATASET...$(NC)"
	@$(UV) answer_dataset \
		--student_search_results_path=$(SEARCH_OUT)/$(notdir $(DATASET)) \
		--save_directory=$(ANSWER_OUT)
	@echo "$(GREEN)ANSWER DATASET OK$(NC)"

evaluate :
	@echo ""
	@echo "$(PINK)EVALUATION RECALL@K...$(NC)"
	@$(UV) evaluate \
		--student_answer_path=$(SEARCH_OUT)/$(notdir $(DATASET)) \
		--dataset_path=$(GT_DATASET) \
		--k=$(K)

# ── Qualité du code ──────────────────────────────────────────────────────── #

lint :
	@echo ""
	@echo "$(RED)TESTING FLAKE8 / MYPY...$(NC)"
	@uv run flake8 --exclude venv,__pycache__ .
	@uv run mypy . --exclude venv --cache-dir .mypy_cache \
		--warn-return-any --warn-unused-ignores \
		--ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
	@echo ""

lint-strict :
	@echo ""
	@echo "$(RED)TESTING FLAKE8 / MYPY STRICT...$(NC)"
	@uv run flake8 . --exclude venv,__pycache__
	@uv run mypy . --strict --exclude venv --cache-dir .mypy_cache
	@echo ""

# ── Nettoyage ────────────────────────────────────────────────────────────── #

clean :
	@echo ""
	@echo "$(RED)CLEANING CACHES...$(NC)"
	@find . -name "__pycache__" -exec rm -rf {} \+
	@find . -name ".mypy_cache" -exec rm -rf {} \+
	@find . -name ".vscode"     -exec rm -rf {} \+
	@find . -name "*.pyc"       -exec rm -f  {} \+
	@echo "$(GREEN)DELETE [OK]$(NC)"

clean_index :
	@echo ""
	@echo "$(RED)SUPPRESSION INDEX BM25...$(NC)"
	@rm -rf data/processed/bm25_index data/processed/chunks
	@echo "$(GREEN)INDEX SUPPRIMÉ$(NC)"

clean_output :
	@echo ""
	@echo "$(RED)SUPPRESSION OUTPUTS...$(NC)"
	@rm -rf data/output
	@echo "$(GREEN)OUTPUTS SUPPRIMÉS$(NC)"

fclean : clean clean_index clean_output

.PHONY: all help install run debug index search answer search_dataset \
        answer_dataset evaluate lint lint-strict clean clean_index \
        clean_output fclean