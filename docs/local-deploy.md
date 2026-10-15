# Local deployment

## Install and start

From the extracted `react-agent-aws` directory, run `make setup`, then `make dev`. Setup creates `.venv` and uses the committed npm lockfiles. Python 3.12 and Node.js 22/24 LTS are required. AWS CLI, Docker, and AWS credentials are unnecessary for this mode.

- Introduction: http://127.0.0.1:5173/
- Workbench: http://127.0.0.1:5173/app
- FastAPI: http://127.0.0.1:8000/docs

The launcher sets `DEMO_MODE=true`, `VITE_DEMO_MODE=true`, and `VITE_API_URL=/api` explicitly. No secrets or account config are loaded from `.env.example`. You do not need to copy an environment file to run the demo. Vite proxies `/api` to the local backend; browser traffic uses the same frontend origin.

A fixed `local-demo-user` owns local runs. In-process background jobs call the shared agent controller. The repository is in memory; the API must run as one process. This is a development deployment on loopback, unsuitable for public hosting. The frontend bypass additionally checks the hostname; Lambda rejects demo mode even if misconfigured.

## Exercise the workflow

Click AWS decision, inspect the filled input, and click Run task. Expect three events: curated search, calculator, validated final answer. Expected arithmetic: 7,200 images. Use Bounded loop for exactly five actions and STEP_LIMIT. Unsupported produces a visibly unsupported terminal answer. Enter `[invalid]` or `[error]` for explicit failure demonstrations.

The deterministic adapter is a scripted fixture engine. It does not understand arbitrary tasks. Use `Calculate: 100 + 25` to change arithmetic while retaining the canned AWS comparison. Token usage is “Not reported” in mock mode.

## Production preview and documentation

Stop `make dev` first. `make preview` builds the SPA and starts Vite preview plus FastAPI on the same ports. It verifies production assets with the local backend; it still uses mock inference and demo authentication.

`make docs-preview` builds and serves `docs/dist` at http://127.0.0.1:8080. It can run alongside the app. This bundle is standalone and can be published with its contents as the hosting root. `npm run docs:build` is an equivalent build command. Do not publish raw `/docs` with unresolved parent-relative architecture links.

## Verify and stop

With either application launcher running:

```sh
.venv/bin/python scripts/local_smoke.py
cd frontend
npm run test:e2e
```

Browser checks use installed Google Chrome on macOS. Set `CHROME_PATH` to another Chrome/Chromium executable as needed. The tests save actual screenshots under `docs/assets`.

Ctrl+C stops both application processes; Ctrl+C separately stops the docs server. Restarting the API clears all runs. Refreshing the workbench clears its selected run in the UI; existing local API records remain until restart. No background service or AWS resource is installed by the launcher.

## Troubleshooting

- Port occupied: reuse the existing app or stop its owning terminal. The launcher checks ports 5173 and 8000 before starting. `lsof -nP -iTCP:5173 -sTCP:LISTEN` identifies the listener; do not kill unrelated processes.
- Missing module or npm executable: activate the required runtime and rerun `make setup`.
- Connection failure: ensure both processes are running. Polling pauses after a network failure; use Reconnect after restoring the API. Failed writes are never retried automatically.
- Cognito screen during a local run: start with `make dev` and use the printed loopback URL. Do not use a LAN hostname for demo mode.
- No workspace after restarting API: start a new task; local runs are intentionally ephemeral.
