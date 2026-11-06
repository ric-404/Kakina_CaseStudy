# Kakina Food Products Mfg. — Modular CLI Management System

### Contents

- [1. Installation and setup](#1-installation-and-setup)
- [2. Project overview and guidelines](#2-project-overview-and-guidelines)
- [3. Code organization](#3-code-organization)
- [4. Editing guide](#4-editing-guide)
- [5. Daily business workflow](#5-daily-business-workflow)
- [6. Production and costing behavior](#6-production-and-costing-behavior)
- [7. Validation and data protection](#7-validation-and-data-protection)
- [8. REST API requirements](#8-rest-api-requirements-ipt-01)
- [9. Scope and limitations](#9-scope-and-limitations)
- [10. Troubleshooting](#10-troubleshooting)
- [11. Suggested IPT-01 demonstration sequence](#11-suggested-ipt-01-demonstration-sequence)

## 1. Installation and setup

### Requirements

- Python 3.10 or newer (a recent supported Python 3 version is recommended)
- A terminal: Windows PowerShell/Command Prompt, Linux terminal, or VS Code terminal
- The project files, including `cli.py` and `requirements.txt`
- Internet access for the first dependency installation

Download or clone the repository, then open a terminal **inside the project directory** (the folder containing `cli.py`).

To clone a GitHub repository:

```bash
git clone https://github.com/ric-404/Kakina_CaseStudy.git
cd Kakina_CaseStudy
```

If you downloaded a ZIP instead, extract it and open the folder that directly contains `cli.py` and `requirements.txt`. The directory name may differ depending on how you downloaded the project.

### Windows 10/11 — PowerShell or Command Prompt

Check Python:

```powershell
py --version
```

Create a virtual environment, install dependencies, and run the application:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe cli.py
```

You **do not need to activate** the virtual environment because these commands call its Python interpreter directly. They also work in Command Prompt.

**Next time:**

```powershell
.\.venv\Scripts\python.exe cli.py
```

If `py` is not recognized but `python` works, use `python -m venv .venv` for the first command.

### Arch Linux and other Linux distributions

Check Python:

```bash
python --version
```

Create the virtual environment, install dependencies, and launch:

Go to the Directory of the folder, then:

```bash
python -m venv .venv
source .venv/bin/activate.fish
python -m pip install -r requirements.txt
python cli.py
```

**Next time:**

```bash
python cli.py
```

These commands work without activation, including in Fish, Bash, and Zsh.

If you prefer to activate the environment first:

| Shell | Activation command |
|---|---|
| Fish | `source .venv/bin/activate.fish` |
| Bash/Zsh | `source .venv/bin/activate` |

After activation, use `python cli.py`. Run `deactivate` to leave the environment.

### Starting the program and using the API

Running `cli.py` **automatically starts a local FastAPI server** and opens the CLI menus. You usually need only one terminal.

While the CLI is running, the interactive API documentation is available at:

**http://127.0.0.1:8765/docs**

For an API-only demonstration, use one of the following:

```powershell
# Windows
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8765
```

```bash
# Linux
.venv/bin/python -m uvicorn api:app --host 127.0.0.1 --port 8765
```

To connect the CLI to an API server you **already started**, open a second terminal in the project folder:

```powershell
# Windows
.\.venv\Scripts\python.exe cli.py --connect
```

```bash
# Linux
.venv/bin/python cli.py --connect
```

**Do not start two API servers on port 8765.** The application is intended for local use at `127.0.0.1`, not public hosting.

### Useful commands

| Task | Windows | Linux |
|---|---|---|
| Run the CLI | `.\.venv\Scripts\python.exe cli.py` | `.venv/bin/python cli.py` |
| Run automated tests | `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` | `.venv/bin/python -m unittest discover -s tests -v` |
| Run only the API | `.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8765` | `.venv/bin/python -m uvicorn api:app --host 127.0.0.1 --port 8765` |
| Connect CLI to existing API | `.\.venv\Scripts\python.exe cli.py --connect` | `.venv/bin/python cli.py --connect` |

---

## 2. Project overview and guidelines

A Python command-line management system for **Kakina Food Products Mfg.**, developed as an IPT-01 (Integrative Programming Technologies) case study. It supports ingredient purchasing, chocolate production, inventory, booth events, reservations, individual sales, adjustments, and reports through a **FastAPI REST API** and **local JSON storage**.

The interface is terminal-based, not a website.

Kakina produces and sells locally made chocolate products. Its business process includes purchasing ingredients, preparing chocolates, bringing selected quantities to selling booths, recording individual transactions, accepting reservations, and keeping unsold products for future sales.

**Purpose:** Organize these connected activities and reduce repeated manual recording while preserving a clear history of stock movements, costs, sales, and adjustments.

### Main technologies

| Technology | Role |
|---|---|
| Python | CLI screens, input validation, and business functions |
| FastAPI | Local REST API server and HTTP endpoints |
| Pydantic | Request data models and API input checking |
| HTTPX | Client that sends CLI requests to FastAPI |
| JSON | Local record storage and API data exchange |
| Uvicorn | Runs the FastAPI server |

### Program guidelines

1. Use the CLI menus for normal data entry; do not edit the JSON file manually while the program is running.
2. Register ingredients before recording purchases or creating recipes.
3. Define a product recipe before recording its production.
4. Record **actual ingredient quantities used** and **actual finished products counted** during production.
5. Use booth allocation, reservations, and individual sales so that stock remains consistent.
6. Verify physical inventory before recording corrections, and always provide a reason.
7. Use the reports to review operations; do not treat the displayed revenue-minus-production-expense figure as full net profit.
8. Keep backups of business data and use fictional customer details in demo or public repository files.

### Main dashboard functions

| No. | Function | Main purpose |
|---|---|---|
| 1 | View finished product inventory | Show physical, allocated, reserved, and available stock |
| 2 | Ingredients and purchases | Register ingredients, purchase stock, edit costs/units, archive unused ingredients |
| 3 | Products and recipes | Add/edit chocolates, manage recipes, archive products, view archived products |
| 4 | Produce chocolates | Record actual ingredient usage and number of finished units |
| 5 | Booth events and unsold stock | Allocate products to events, close booths, count leftovers |
| 6 | Customer reservations | Reserve stock for customers or cancel an active reservation |
| 7 | Record an individual sale | Save direct, Messenger, booth, or reservation sales |
| 8 | Reports | View date-filtered operational and financial summaries |
| 9 | Verified inventory adjustment | Correct physical finished-product stock with a reason |
| 0 | Exit | Close the program |

---

## 3. Code organization

The project is organized into separate layers. **UI code displays prompts, API code handles requests, and business code applies the rules.**

```text
Kakina_CaseStudy/
├── cli.py                   # Entry point for the CLI
├── api.py                   # FastAPI endpoints and request models
├── core.py                  # Validation, JSON storage, locking, seed products
├── requirements.txt         # Required Python packages
├── README.md                # Project guide
├── NAVIGATION_GUIDE.md      # CLI menu and navigation notes
├── .gitignore               # Files excluded from Git
├── business/
│   ├── __init__.py
│   ├── ingredients.py       # Catalog, purchases, cost calculation, recipes
│   ├── products.py          # Product create, update, and archive
│   ├── production.py        # Ingredient consumption and finished stock
│   ├── inventory.py         # Available, reserved, allocated stock, adjustments
│   ├── selling.py           # Events, reservations, and sales
│   └── reports.py           # Date-filtered report calculations
├── ui/
│   ├── __init__.py
│   ├── client.py            # HTTP client for the FastAPI backend
│   ├── display.py           # Bordered tables, headers, status messages
│   ├── inputs.py            # Input prompts and reusable checks
│   ├── navigation.py        # Repeated menus and refresh after each action
│   ├── menu.py              # Dashboard and API startup
│   ├── catalog.py           # Inventory, ingredients, products, recipes
│   ├── production.py        # Production CLI screens
│   ├── selling.py           # Booths, reservations, individual sales screens
│   ├── report_tables.py     # Formatted report tables
│   └── reports.py           # Report selection and stock adjustment screens
└── tests/
    ├── test_complete_project.py
    └── test_ui_navigation.py
```

`kakina_data.json` and `kakina_data.json.lock` are **runtime data files**, not source files. They may appear after the application creates or accesses data and are normally excluded from the repository.

### How the modules communicate

```text
User enters data in terminal
            |
            v
ui/ (prompts and tables)
            |
            v
ui/client.py (HTTP request with JSON)
            |
            v
api.py (FastAPI endpoint, request model)
            |
            v
business/ (validation and business operations)
            |
            v
core.py (load/save JSON data)
            |
            v
kakina_data.json
```

For example, a purchase entered in `ui/catalog.py` is sent through the HTTP client to `POST /api/purchases`. The API calls the ingredient purchasing function, which updates stock and purchase history in the JSON state.

**The CLI must not modify `kakina_data.json` directly.** All normal changes go through the API and business functions.

---

## 4. Editing guide

Use this table when changing the system so related code remains organized.

| Change you want to make | File to examine first |
|---|---|
| Main menu labels and numbering | `ui/menu.py` |
| Refresh screens and return to previous menu | `ui/navigation.py` |
| Spacing, headings, borders, and table formatting | `ui/display.py` |
| Questions, confirmations, date/number inputs | `ui/inputs.py` |
| Ingredient or purchase terminal screens | `ui/catalog.py` |
| Product, archived-products, and recipe screens | `ui/catalog.py` |
| Ingredient stock, purchases, weighted costs, archiving | `business/ingredients.py` |
| Product names, prices, archive restrictions | `business/products.py` |
| Production prompts and review steps | `ui/production.py` |
| Ingredient deductions and production costs | `business/production.py` |
| Available stock and verified stock adjustments | `business/inventory.py` |
| Booths, reservations, and sales rules | `business/selling.py` |
| Booths, reservations, and sales prompts | `ui/selling.py` |
| Report menu and date selection | `ui/reports.py` |
| Report table layout | `ui/report_tables.py` |
| Report totals and aggregations | `business/reports.py` |
| API routes and request schemas | `api.py` |
| JSON loading/saving and shared validation | `core.py` |
| Program regression tests | `tests/` |

### Recommended editing procedure

1. Identify whether the change affects the **screen**, **API route**, or **business rule**.
2. Edit the smallest relevant module instead of putting everything in `cli.py`.
3. Keep function names and responsibilities clear.
4. For business-rule changes, update or add an automated test.
5. Run the tests and check the complete workflow in the CLI.
6. Back up `kakina_data.json` before testing changes against real records.

### Readable terminal layout and navigation

The project uses Python `print()` and `input()` with reusable display helpers. No third-party terminal styling library is required.

- Each of the nine features **stays open after saving, editing, cancelling, or an API error**.
- After an operation, the screen refreshes and displays the feature's current table and options again.
- `[0] Back` returns from a feature to the main dashboard.
- Headings, separated input prompts, and short status messages keep screens readable.
- Long names wrap in bordered tables; the existing table style remains largely unchanged.
- On a narrow terminal, records may be shown as individual bordered entries instead of wide columns.

**Products and Recipes:** Active products appear in the main table. Choose **`[5] Show Archived Products`** to view archived items in a separate table; press Enter to return to Products and Recipes.

**Reports:** Choose the date filter once, view several reports, press Enter to choose another report, select `[9] Change report date`, or `[0] Back`.

---

## 5. Daily business workflow

The recommended order follows Kakina's actual business process instead of treating each menu as a separate activity.

### Step 1 — Register ingredients and record purchases (Function 2)

Register ingredients such as cacao, sugar, mango bits, and pistachios. Choose the appropriate unit: `g`, `kg`, or `pcs`. Record the purchased quantity, amount paid, purchase date, and optional supplier note.

- Purchases **increase ingredient stock**.
- New purchase costs are added to existing ingredient stock value.
- Weighted-average cost is derived from the current quantity and stock value.
- Ingredient names, g/kg display units, stock quantities, unit costs, and total stock values can be edited.
- Direct stock/value corrections require a reason and are recorded separately from purchases.

**Archive rule:** An ingredient can be archived even if it has remaining stock, provided no product recipe (including an archived product's recipe) or production-use record references it. Purchase history is retained. Archived ingredients are not available for new purchases or production.

### Step 2 — Manage products and recipes (Function 3)

The initial catalog contains five Kakina chocolate products, with their starting prices and zero stock:

| Product | Starting price |
|---|---:|
| Purong Cacao (Tablea) Pouch 100g (11 pcs) | PHP 120 |
| 60% Dark Chocolate with Pistachio Nuts Pouch 20g | PHP 40 |
| 60% Dark Chocolate with Pistachio Nuts Bar 60g | PHP 150 |
| 60% Dark Chocolate with Mango Bits Pouch 20g | PHP 40 |
| 60% Dark Chocolate with Mango Bits Bar 60g | PHP 150 |

You can add products, edit names/prices, and create or replace product recipes.

**Recipe quantities are suggested amounts per finished pouch/bar.** A recipe guides production; it is not an automatic stock deduction. Products can be archived only when their finished stock is zero and they have no active reservations or booth allocations. Archived products are displayed using option `[5]`, not below the active products table.

### Step 3 — Record actual production (Function 4)

Choose the product and date, record the **actual amounts of each recipe ingredient used**, then enter the **actual count of finished pouches/bars**. Review the details before saving.

When a production record is successfully saved, the system:

1. Verifies the product and ingredients are active and the recipe exists.
2. Checks that all recipe ingredients were provided with valid quantities.
3. Checks that enough ingredient stock is available.
4. Deducts the actual ingredient amounts and their proportional costs.
5. Adds the counted finished quantity to product stock.
6. Records the production date, ingredients used, total cost, and output quantity.

The deductions and finished-stock increase are saved as one operation, so failed validation does not partially record the production run.

### Step 4 — Check finished inventory (Function 1)

Review the stock columns:

| Column | Meaning |
|---|---|
| Stock | Total physical finished-product quantity recorded |
| Booth | Quantity still allocated to open booths |
| Reserved | Quantity committed to active customer reservations |
| Available | `Stock - Booth - Reserved` |

The Available figure is the amount that can be allocated or sold through an unreserved, non-booth sale.

### Step 5 — Allocate products to booth events (Function 5)

Create an event (for example, a booth in Talavera or at CLSU), select products and quantities, and allocate them from available stock.

Record each booth transaction using **Function 7**, choosing the booth sales channel and the relevant event. When the event ends:

1. Open Function 5 and select the open booth.
2. Count the unsold products physically remaining at the booth.
3. Enter the final count for every product allocated to that booth.
4. Review any differences between expected and counted stock.
5. Close the booth.

Closing the booth releases its remaining allocation so unsold products can be offered later. **Count discrepancies are flagged; they do not automatically alter physical inventory.** Use a verified stock adjustment when a correction is actually needed.

### Step 6 — Record customer reservations (Function 6)

Save the customer name, product, quantity, reservation date, and pickup/delivery method. The system holds that quantity from general available stock.

A reservation can be cancelled while active. A reservation sale must match its product and full reserved quantity; once sold, the reservation is marked completed and cannot be sold a second time.

### Step 7 — Record individual sales (Function 7)

Record each transaction separately. Supported sales channels are:

- `direct` — direct sale or personal offer
- `messenger` — order recorded after customer contact through Messenger
- `booth` — sale from an open event's allocation
- `reservation` — fulfillment of an existing reservation

Enter the sold product and quantity, payment label (`cash` or `gcash`), date, and optional delivery fee/customer details. The program calculates the subtotal and total, then deducts sold units from physical stock after successful confirmation.

Choose **`[0] Back`** to leave the sales menu. Cancelling **before saving** leaves inventory unchanged; the program does not provide transaction reversal for an already recorded sale.

### Step 8 — Review reports (Function 8)

Choose an optional date (`YYYY-MM-DD`; blank includes all dates), then choose:

| Option | Report |
|---|---|
| `[1]` | Business summary |
| `[2]` | Best sellers |
| `[3]` | Sales by booth |
| `[4]` | Sales by channel |
| `[5]` | Daily revenue |
| `[6]` | Individual sales history |
| `[7]` | Production and purchase history |
| `[8]` | Show all reports |
| `[9]` | Change report date |
| `[0]` | Back |

Reports use bordered tables and can be viewed repeatedly without returning to the dashboard.

### Step 9 — Perform verified inventory adjustments (Function 9)

After counting the actual finished products, select a product, enter the corrected physical stock quantity, and provide a reason.

The correction is recorded with the old and new counts. **Stock cannot be reduced below the sum of quantities already reserved for customers and still allocated to open booths.**

---

## 6. Production and costing behavior

### Recipes are suggestions; production uses measured amounts

Suppose a sample 60 g chocolate bar has this suggested recipe:

| Ingredient | Suggested per bar | Suggested for 10 bars |
|---|---:|---:|
| Cacao | 36 g | 360 g |
| Sugar | 18 g | 180 g |
| Mango bits | 6 g | 60 g |
| **Total** | **60 g** | **600 g** |

These are **demonstration values, not Kakina's actual recipe**. In Function 4, the program does **not** automatically multiply the recipe amounts to deduct them. The operator enters the actual quantities weighed and then counts finished bars or pouches. Actual ingredient use and actual output may differ from the suggested recipe.

### Grams, kilograms, and pieces

- Weighted ingredients use **grams internally**.
- The terminal can display and accept appropriate ingredient stock values in **g or kg**.
- `1 kg = 1,000 g`; changing the display between g and kg does **not** convert a weight ingredient into a different kind of ingredient.
- `pcs` is for ingredients or materials counted as whole pieces; it cannot be converted to g/kg using the unit edit feature.

### Weighted-average ingredient cost

Example: purchase 500 g of sugar for PHP 40, then 500 g more for PHP 60.

| Item | Quantity | Value |
|---|---:|---:|
| First purchase | 500 g | PHP 40 |
| Second purchase | 500 g | PHP 60 |
| Combined stock | 1,000 g | PHP 100 |
| Average cost | 1 g | PHP 0.10 |

If production consumes 300 g, the estimated recorded ingredient usage cost is **PHP 30**, leaving 700 g with approximately PHP 70 of stock value.

Unit cost and stock value can be corrected in Function 2, but **purchase records and adjustment records remain separate**.

### Production-day expenses versus purchases

The business calculates total ingredient production expenses for the day. The program can record several production runs, then sums their **recorded ingredient usage costs** for the selected date.

Purchasing ingredients and using ingredients are different events:

- **Ingredient purchases**: money spent acquiring stock.
- **Production usage cost**: recorded cost of ingredients actually consumed in making chocolates.
- **Sales revenue**: money recorded from sales, including any recorded delivery fees.

A displayed calculation such as **sales revenue minus recorded production expenses is not net profit**. It excludes other business costs and does not match sold items to their exact production costs, especially when some finished stock remains unsold.

---

## 7. Validation and data protection

The system checks inputs both in the CLI and through the API/business functions.

| Area | Validation or protection |
|---|---|
| Text | Required names cannot be blank, excessively long, or contain control characters |
| Dates | Must be valid `YYYY-MM-DD` dates |
| Quantities | Must fit the required positive/zero and integer/decimal rules |
| Money | Amounts are validated, generally to two decimal places; displayed unit costs can use more precision |
| Duplicate records | Active products/ingredients cannot reuse an active name |
| Recipes | Ingredients must exist; repeated ingredients in a recipe are rejected |
| Production | Requires a recipe, actual use of every recipe ingredient, and enough stock |
| Booths | Cannot allocate more than available stock or close an event twice |
| Reservations | Cannot reserve beyond available stock or resell completed/cancelled reservations |
| Sales | Cannot sell more than the permitted stock for the selected channel |
| Product archive | Blocked when stock, active booth allocation, or reservations remain |
| Ingredient archive | Blocked when recipe or production-use references exist; purchase history is preserved |
| Inventory adjustments | Require a reason; cannot violate reserved/allocated stock minimums |
| JSON writes | Changes are written to a temporary file and then replace the data file atomically |

Business-rule errors appear in the terminal with an explanation. API calls return appropriate HTTP error responses, including `400`, `404`, and `409` for several invalid business operations; request-schema validation may return `422`.

**Data privacy:** This is an academic local application without user accounts or access controls. Do not upload live customer details, private records, or credentials to a public GitHub repository.

---

## 8. REST API requirements (IPT-01)

This application demonstrates **Create, Read, Update, and Delete (CRUD)** through REST-style HTTP routes. The CLI is an HTTP client; it does not bypass FastAPI to change business data.

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/health` | Check local API status |
| `GET` / `POST` | `/api/products` | Read/create chocolate products |
| `GET` | `/api/products/{product_id}` | View one product |
| `PUT` / `DELETE` | `/api/products/{product_id}` | Edit/archive a product |
| `GET` / `POST` | `/api/ingredients` | Read/register ingredients |
| `PUT` / `DELETE` | `/api/ingredients/{ingredient_id}` | Edit/archive an ingredient |
| `GET` | `/api/ingredient-adjustments` | View ingredient correction history |
| `GET` / `POST` | `/api/purchases` | Read/record ingredient purchases |
| `PUT` | `/api/products/{product_id}/recipe` | Create or replace recipe |
| `GET` / `POST` | `/api/production` | Read/record production |
| `GET` | `/api/inventory` | View finished-product stock |
| `GET` / `POST` | `/api/events` | Read/create booth events |
| `PUT` | `/api/events/{event_id}/close` | Close and reconcile booth |
| `GET` / `POST` | `/api/reservations` | Read/create reservations |
| `PUT` | `/api/reservations/{reservation_id}/cancel` | Cancel an active reservation |
| `GET` / `POST` | `/api/sales` | Read/record sales |
| `GET` / `POST` | `/api/adjustments` | Read/record verified stock corrections |
| `GET` | `/api/reports` | Read date-filtered reports |

`DELETE` **archives** applicable catalog records rather than erasing them from historical data. Successful archive endpoints return HTTP `204 No Content`; create endpoints return `201 Created`. Normal reads/updates commonly return `200 OK`.

### Demonstrating CRUD

With `cli.py` running, open **http://127.0.0.1:8765/docs** in a browser.

1. **Create:** Use `POST /api/ingredients` with a fictional sample ingredient.
2. **Read:** Use `GET /api/ingredients` to view it.
3. **Update:** Use `PUT /api/ingredients/{ingredient_id}` to change its name or display unit.
4. **Delete:** Use `DELETE /api/ingredients/{ingredient_id}` to archive it **only if it has no recipe or production references**.

Use disposable demonstration records when testing mutation endpoints because the API operates on the same local JSON file used by the CLI.


### Data files

- `kakina_data.json` — Local business records (created on the first saved change if absent).
- `kakina_data.json.lock` — File used to coordinate data access. It is not the business database.
- `.venv/` — Local Python environment, automatically recreated using the setup instructions.
- `__pycache__/` — Temporary Python cache, not required in a source-code submission.

A damaged JSON file produces an error rather than silently resetting the records. Always keep a backup before modifying or migrating saved business data.

### Fresh start or reset

1. Stop the CLI and any separately running API server.
2. Back up your existing `kakina_data.json`.
3. For a fresh demonstration, use a **new `KAKINA_DATA` path** rather than deleting real records.
4. When the new file does not exist, the app starts with the five default products at zero stock and empty business histories; it saves a JSON file after the first successful change.
5. Do not delete an active lock file while a process is using it. You usually do not need to delete the lock file to reset records.

### Preparing the repository for GitHub or Google Drive

Exclude generated files and private records from the public source code. Recommended `.gitignore` entries:

```gitignore
.venv/
venv/
__pycache__/
*.pyc
.pytest_cache/
.env
kakina_data.json
kakina_data.json.lock
kakina_demo.json
```

Keep the **source files, `requirements.txt`, README, and test files** in the repository. GitHub and Google Drive store the code; they do not automatically run the local FastAPI server.

If a file was already committed, adding it to `.gitignore` does not erase it from Git history. Remove sensitive data from Git history before sharing a public repository.

---

## 9. Scope and limitations

### Included

- Ingredient registration, purchasing, stock/value corrections, and reference-safe archiving
- Chocolate product and recipe management
- Actual production quantities and ingredient usage costing
- Finished inventory, open booth allocations, and unsold stock reconciliation
- Customer reservations and sale recording
- Date-filtered reports and verified inventory adjustments
- Local FastAPI REST endpoints with JSON requests and responses
- Terminal menus with reusable display functions, refreshed tables, and `[0] Back`
- Automated regression tests

### Not included

- Online website, mobile app, or graphical user interface
- Live Messenger integration or automatic message imports
- Real GCash payment processing or online payment collection
- Point-of-sale hardware, barcode checkout, or receipt printing
- Product expiration or shelf-life tracking
- Automated production yield estimation or full finished-goods cost accounting
- Complete net-profit accounting, payroll, taxes, or all overhead expenses
- Multi-user roles, authentication, hosted deployment, or cloud synchronization
- Automatic reversal of completed sales

This project is designed for **single-user local academic use**. The JSON file and locking design should not be treated as a replacement for a production-ready multi-user database. On platforms without `fcntl` (such as Windows), the included implementation does not provide the same OS-level file locking as on Unix systems. Avoid multiple independently running API server processes pointing at the same data file.

---

## 10. Troubleshooting

| Problem | What to do |
|---|---|
| `py` is not recognized on Windows | Check Python installation; use `python -m venv .venv` if `python` is available. |
| `python: command not found` | Check that Python 3 is installed and available on PATH. |
| `No module named fastapi` / `httpx` | Install requirements with the Python interpreter inside `.venv`, then run using that same interpreter. |
| PowerShell script activation is blocked | Use `.\.venv\Scripts\python.exe` directly. Activation is optional. |
| Port `8765` is already in use | Stop the existing server, or use `cli.py --connect` when you intentionally started the API first. |
| Cannot connect to API | Make sure `cli.py` started correctly or that the API-only server is running before using `--connect`. |
| `HTTP 409` when archiving an ingredient | Check whether any recipe or production-use history references it. Remaining ingredient stock alone does not block archiving. |
| Cannot archive a product | Ensure physical stock is zero and no active reservation or open booth allocation remains. |
| Cannot adjust stock | Ensure the corrected count is not below reserved plus open-booth-allocated quantities. |
| No available products for direct sale | Check whether the recorded stock is already allocated to booths or reserved. |
| Recipes are not automatically scaled | Function 4 requires actual ingredient usage; Function 3's recipe amounts are a guide per item. |
| The main menu reappears unexpectedly | Use the latest CLI edition; its feature menus stay open after actions, and `[0] Back` returns to the dashboard. |
| JSON file appears missing | It is created after the first successful write. Check whether `KAKINA_DATA` points to another path. |
| JSON data is damaged | Stop the program and restore a known good backup rather than manually guessing the missing fields. |
| `cli.py` or `requirements.txt` cannot be found | Open the terminal inside the correct extracted/cloned project folder. |

---

## 11. Suggested IPT-01 demonstration sequence

A useful live demonstration follows one complete business transaction instead of showing disconnected menus:

1. **Function 2:** Register ingredients and record a purchase.
2. **Function 3:** Show a product and its suggested per-item recipe.
3. **Function 4:** Record actual ingredient usage and finished chocolates.
4. **Function 1:** Verify the resulting finished-product stock.
5. **Function 5:** Allocate chocolates to a booth.
6. **Function 6:** Reserve some available stock for a customer.
7. **Function 7:** Record individual booth and/or direct sales.
8. **Function 5:** Close the booth and count unsold stock.
9. **Function 8:** Show the business summary and other reports.
10. **Function 9:** Demonstrate a verified correction using safe sample data.
11. **FastAPI `/docs`:** Demonstrate GET, POST, PUT, and DELETE operations.
