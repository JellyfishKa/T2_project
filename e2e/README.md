# T2 E2E Tests — Playwright + Allure

End-to-end and verification tests for the T2 logistics platform.  
Browser tests run via **Playwright**, reports generated with **Allure**.

---

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Node.js | 18+ |
| npm | 9+ |
| Running app | Docker or local dev server |

---

## First-Time Setup

```bash
# 1. Install dependencies
cd e2e
npm install

# 2. Install Playwright browser (Chromium)
npx playwright install chromium

# 3. (Optional) Install Allure CLI globally for report generation
npm install -g allure-commandline
```

---

## Start the App

Tests require the application to be running before you execute them.

**With Docker (recommended):**
```bash
# from project root
docker-compose up -d
# Frontend: http://localhost:80
# API:      http://localhost:8000
```

**With local dev servers:**
```bash
# Terminal 1 — Backend
cd backend && uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend && npm run dev
# Frontend: http://localhost:5173
```

---

## Running Tests

```bash
# Run all E2E tests (headless Chromium)
npm test

# Run only smoke tests (fast sanity check, ~30s)
npm run test:smoke

# Run tests with visible browser window
npm run test:headed

# Debug a single spec interactively (opens Playwright Inspector)
npm run test:debug -- tests/reps/crud.spec.ts
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_URL` | `http://localhost:5173` | Frontend URL for page navigation tests |
| `API_URL` | `http://localhost:8000/api/v1` | Backend API URL for direct API calls |

**Override for Docker setup:**
```bash
BASE_URL=http://localhost:80 API_URL=http://localhost:8000/api/v1 npm test
```

---

## Allure Reports

After any test run, raw result files are written to `allure-results/`.

**Generate + open report:**
```bash
npm run report
# Generates HTML report in allure-report/ and opens it in the browser
```

**Separate steps:**
```bash
npm run report:gen   # generate only (allure-report/ folder)
npm run report:open  # open already generated report
```

The Allure report shows:
- Test suite tree with pass/fail status
- Screenshots attached on failure
- Video recordings on failure
- Trace viewer link on first retry failure
- Test duration and history

---

## Test Structure

```
tests/
├── smoke/              # Health check + all pages load without JS errors
│   ├── api-regressions.spec.ts # benchmark/routing/optimize API smoke after backend fixes
│   └── network.spec.ts         # no same-origin 4xx/5xx on key pages (/dashboard, /schedule)
├── reps/               # Sales rep CRUD (create, status change, delete)
├── vehicles/           # Vehicle CRUD + assignment in reps dropdown
├── schedule/
│   ├── generate.spec.ts      # Generate plan, 409 on duplicate, force regenerate
│   ├── day-modal.spec.ts     # Day modal, metrics, map links, transport mode recalculation
│   └── visit-status.spec.ts  # State machine: planned→completed/skipped, invalid transitions
├── export/             # Excel download: content-type, file size, filename, UI button
├── force-majeure/      # FM event creation + redistribution
└── holidays/           # Holiday toggle with affected_visits_count verification
```

---

## CI Usage

```bash
cd e2e
npm ci
npx playwright install --with-deps chromium
BASE_URL=http://localhost:80 API_URL=http://localhost:8000/api/v1 npm test
npm run report:gen
# Upload allure-report/ folder as a build artifact
```

---

## Troubleshooting

**Tests fail with "page not found" / connection refused**  
→ Check the app is running and `BASE_URL` matches the actual frontend URL.

**`allure` command not found**  
→ Run `npm install -g allure-commandline` or use `npx allure-commandline generate ...`.

**Playwright browser not installed**  
→ Run `npx playwright install chromium`.

**Schedule tests skip with "no planned visits"**  
→ The monthly plan may be empty. Run `POST /api/v1/schedule/generate?month=YYYY-MM&force=true` once to seed data.
