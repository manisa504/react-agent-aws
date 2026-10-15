PY := .venv/bin/python
.PHONY: setup dev preview test eval lint build package synth docs-build docs-preview verify
setup:
	python3 -m venv .venv
	$(PY) -m pip install -r backend/requirements-dev.lock
	cd frontend && npm ci --no-audit --no-fund
	cd infra && npm ci --no-audit --no-fund
dev:
	$(PY) scripts/dev.py
preview:
	$(PY) scripts/dev.py --preview
test: package
	cd backend && ../.venv/bin/python -m pytest -q
	cd frontend && npm test
	cd infra && npm test
eval:
	cd backend && PYTHONPATH=. ../.venv/bin/python evals/run_evals.py
lint:
	$(PY) -m ruff check backend scripts
	cd frontend && npm run lint && npm run typecheck
	cd infra && npm run typecheck
build:
	cd frontend && npm run build
package:
	$(PY) scripts/package_lambda.py
synth: package
	cd infra && npm run synth
docs-build:
	$(PY) scripts/build_docs.py
docs-preview: docs-build
	$(PY) -m http.server 8080 --bind 127.0.0.1 --directory docs/dist
verify: lint package test eval build
	cd infra && npm run synth
	$(PY) scripts/build_docs.py
