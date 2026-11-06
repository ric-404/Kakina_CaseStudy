<<<<<<< HEAD
# Kakina Food Products Mfg. — Complete CLI project

## Setup

**Windows (PowerShell or Command Prompt):**

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe cli.py
```

**Linux:**

```bash
python -m venv .venv
source .venv/bin/activate.fish
python -m pip install -r requirements.txt
python cli.py
```

For an API-only demo, run `python -m uvicorn api:app --host 127.0.0.1 --port 8765`. Open `http://127.0.0.1:8765/docs` for GET/POST/PUT/DELETE examples. If you started the API separately, open another terminal and run `python cli.py --connect` instead of starting a second server.

## Project structure

- `cli.py`: Starts terminal program.
- `api.py`: REST API endpoint definitions, Pydantic request models.
- `core.py`: Safe JSON persistence and validations.
- `business/`: Business rules (`ingredients`, `products`, `inventory`, `production`, `selling`, `reports`).
- `ui/`: Terminal menus, tables, questions, API client, reusable `navigation.py` feature loop.
- `tests/`: Regression tests for the changed functions and API behavior.

## Limits

Single-user, locally hosted academic software; no payment gateway or actual Messenger integration. Ingredient purchases and production-usage costs are separate; revenue minus ingredient usage is **not full net profit**. HTML/JS are not used. Sale cancellation does not undo a saved transaction.
=======
# Kakina_CaseStudy
>>>>>>> ada866c6dd675c668275ac106508df38a6a3dc60
