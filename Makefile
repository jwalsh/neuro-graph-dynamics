.PHONY: run test lint clean install

run:
	poetry run python app.py

test:
	poetry run pytest

lint:
	poetry run flake8 .
	poetry run mypy .
	poetry run black --check .
	poetry run isort --check-only .

format:
	poetry run black .
	poetry run isort .

clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete

install:
	poetry install

tangle:
	emacs --batch -l org README.org -f org-babel-tangle

versioned-responses:
	sqlite3 -csv  knowledge_graph.db "SELECT  * FROM versioned_responses;" | xsv table 
	# sqlite3 -json  knowledge_graph.db "SELECT  * FROM versioned_responses;" | jq | tee versioned_responses_export.json
