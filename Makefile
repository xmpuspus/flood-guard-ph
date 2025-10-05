.PHONY: install seed dev clean help

help:
	@echo "FloodWatch PH - Makefile Commands"
	@echo ""
	@echo "  make install    - Install Python dependencies"
	@echo "  make seed       - Initialize and populate vector database"
	@echo "  make dev        - Start development server"
	@echo "  make clean      - Remove generated files"
	@echo ""

install:
	pip install -r requirements.txt

seed:
	python scripts/setup_vectordb.py
	python scripts/embed_projects.py

dev:
	uvicorn backend.main:app --reload --port 8000

clean:
	rm -rf chroma_data/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete