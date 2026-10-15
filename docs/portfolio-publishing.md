# Portfolio and static playground

Public portfolio: https://manisa504.github.io/react-agent-aws/

Interactive mockup: https://manisa504.github.io/react-agent-aws/demo.html

The portfolio explains the deployed application. The second page is a static replica intended for hiring managers: six preset scenarios, adjustable numeric inputs, a 3–8 step budget, queued/running/terminal transitions, expandable evidence, reset during execution and copyable answers. It uses browser-local JavaScript, has no login, and makes no runtime API or AWS requests. Editable task text does not drive an LLM; the chosen fixture determines the result. Reloading resets the demo.

## Build and preview

```sh
make docs-build
make docs-preview
# Open http://127.0.0.1:8080/ and /demo.html
```

The builder produces standalone `docs/dist` with both root pages, local CSS/JavaScript, screenshots, all three diagram exports, and referenced documentation. All links are relative so publishing under `/react-agent-aws/` works. No CDN, external fonts, runtime API keys or model calls are required. The generated directory is ignored; source files in `docs/` are committed.

## Publishing

GitHub Pages is configured to use GitHub Actions. `.github/workflows/pages.yml` builds and validates the bundle, uploads it with `upload-pages-artifact`, and deploys it with `deploy-pages`. Pushes on `main` affecting the website trigger publication; the workflow can also be started manually. The deployment environment is `github-pages` and exposes the published URL. HTTPS is enabled. The existing AWS Amplify app continues serving the live authenticated application independently.

## Verification

With the preview server running:

```sh
CHROME_PATH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' node scripts/verify_portfolio.mjs
```

In CI, Playwright's installed Chromium path is supplied instead. Set `PORTFOLIO_URL` to verify another deployment or a project subpath. The checks cover real asset loading, the diagram dialog, desktop and 320px layouts, six scenarios, three/eight-step loops, calculation validation, input escaping, reset cancellation, and running scenarios after all network access is blocked. Browser screenshots are saved under ignored `.build/`; a labeled static-demo screenshot is saved under `docs/assets`.

Higgsfield was used during authoring for a conceptual image, not HTML generation. The downloaded image is served as a static asset and is explicitly labeled. Credentials are never needed by visitors or the Pages workflow. See [asset provenance](assets/README.md).

## Removing this static publication

After explicit owner approval, disable Pages in repository Settings → Pages (or delete the Pages site through GitHub's API) and disable/remove its publishing workflow. Keep the source unless its deletion is also requested. This publication is separate from Amplify and the retained AWS resources described in the [AWS teardown guide](aws-deploy-teardown.md).


## Evidence-backed visual case study

The current portfolio is rendered from `portfolio.template.html` by `scripts/generate_portfolio.py`, called by `make docs-build`. Edit the template/CSS/JS rather than manually changing the generated index. The renderer reads the executed evaluation report, the sanitized recorded live evidence, and the architecture catalog. It validates fixture IDs, expected termination reasons, step bounds, positive actual model usage, event ordering/counts and retrieved citation IDs before rendering.

The page includes an inline SVG system drawing, nine visible architecture panels with filters and full-size viewers, an accessible three-step observed-trace explainer, actual run usage, all twelve evaluation rows, live acceptance checks, tradeoffs and original-resolution screenshot viewers. Every diagram can be opened as SVG or downloaded as editable draw.io. No new inference is required to build or read the case study.

The sanitized snapshot `assets/live-verification.json` records the previously executed live smoke checks. It contains no owner credentials or tokens and does not imply continuous monitoring. Updated evaluations must come from running the fixtures. Browser acceptance now checks the nine-view atlas, filters, diagram/screenshot viewers, trace tabs and result rows in addition to the static demo scenarios.
