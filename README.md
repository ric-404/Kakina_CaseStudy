# Kakina Food Products Mfg.: CLI Inventory, Production and Sales Management System

A beginner-friendly technical guide for understanding, running, maintaining, and presenting the **Kakina Case Study** application.

> **Project type:** Python command-line application (CLI) connected to a local FastAPI REST API.  
> **Storage:** JSON file, not MySQL/SQLite.  
> **Audience:** Students, maintainers, and case-study evaluators.  
> **Based on:** The public `ric-404/Kakina_CaseStudy` source code reviewed on November 11, 2026. If your local files differ from GitHub, verify the code before using these instructions.


## 1. What the system does

Kakina Food Products Mfg. produces chocolate products, purchases ingredients, prepares chocolates, sells at events or directly, receives customer reservations, and monitors unsold stock. This project joins those records in **one local management system**.

It is **not a point-of-sale (POS) checkout application**. It records individual sales but does not provide a cash register, payment gateway, printed receipt system, or online store.

### Main dashboard functions

| Menu | Feature | Main operation |
| --- | --- | --- |
| **1** | Finished product inventory | View stock, booth allocations, reservations and available quantity. |
| **2** | Ingredients and purchases | Add ingredients, record purchases, edit values/stock and archive unused ingredients. |
| **3** | Products and recipes | Create/edit products, save recipes, archive products and show archived products separately. |
| **4** | Produce chocolates | Enter actual ingredient quantities used and the number of finished chocolates produced. |
| **5** | Booth events and unsold stock | Allocate stock to a booth; record and compare remaining stock when closing. |
| **6** | Customer reservations | Hold products for pickup/delivery or cancel an active reservation. |
| **7** | Record an individual sale | Record direct, Messenger, booth or reservation sales. |
| **8** | Reports | Review sales, production, purchases, best sellers and revenue summaries. |
| **9** | Verified inventory adjustment | Correct finished-product stock after checking its physical quantity. |
| **0** | Exit | Close the program. |

### Default products

On a **fresh** JSON state, the program prepares these product records with zero stock:

| Product | Initial selling price |
| --- | ---: |
| Purong Cacao (Tablea) Pouch 100g (11 pcs) | PHP 120 |
| 60% Dark Chocolate with Pistachio Nuts Pouch 20g | PHP 40 |
| 60% Dark Chocolate with Pistachio Nuts Bar 60g | PHP 150 |
| 60% Dark Chocolate with Mango Bits Pouch 20g | PHP 40 |
| 60% Dark Chocolate with Mango Bits Bar 60g | PHP 150 |

Existing data is not reset to these values during every launch.

---

## 2. System architecture: how everything connects

```text
You (terminal input)
        |
        v
cli.py -> ui/menu.py -> ui/catalog.py / production.py / selling.py / reports.py
                           |
                           v
                     ui/client.py
                      (HTTPX)
                           |
                   HTTP request + JSON
                           |
                           v
                       api.py
                (FastAPI + Pydantic)
                           |
                           v
                 business/*.py
        (rules, calculations, stock updates)
                           |
                           v
                       core.py
           (validation, read, write, IDs)
                           |
                           v
                   kakina_data.json

Response travels back: JSON -> API -> ui/client.py -> terminal table/message.
```

**Important distinction:** The interface is terminal-based, but it is still an **API-based application**. The CLI does **not** normally update the JSON file directly; it requests changes from the API.

### Example: recording an ingredient purchase

1. The user opens **Function 2** and enters a purchase in `ui/catalog.py`.
2. `ui/client.py` sends `POST /api/purchases` with a JSON request body.
3. `api.py` validates the request against `PurchaseCreate`.
4. `api.py` calls `core.execute(ing.purchase_add, ...)`.
5. `business/ingredients.py` checks the purchase and adds the quantity/cost to the ingredient record.
6. `core.py` saves the updated state to `kakina_data.json`.
7. The API returns the saved purchase as JSON; the CLI displays a success message and refreshes the table.

This same **UI -> Client -> API -> Business -> Storage** pattern applies to most features.

---

## 3. Project structure and the purpose of each file

```text
Kakina_CaseStudy/
|
|-- cli.py                       Main terminal entry point
|-- api.py                       FastAPI routes and request models
|-- core.py                      JSON storage, IDs and shared validation
|-- requirements.txt             Third-party Python dependencies
|-- README.md                    This learning/documentation guide
|-- .gitignore                   Git exclusions (if present)
|
|-- business/                   Actual business rules
|   |-- ingredients.py           Ingredients, purchases, recipes, ingredient archive
|   |-- products.py              Product registration, editing and archiving
|   |-- production.py            Production and ingredient usage costing
|   |-- inventory.py             Available stock, allocations and adjustments
|   |-- selling.py               Booths, reservations and individual sales
|   `-- reports.py               Report totals and grouping
|
`-- ui/                         What the operator sees
    |-- client.py                HTTP communication with the API
    |-- menu.py                  Main dashboard and API startup
    |-- display.py               Headings, tables, borders, status messages
    |-- inputs.py                Input questions and checks
    |-- navigation.py            Stay in a feature, refresh, go back
    |-- catalog.py               Inventory, ingredient, product and recipe screens
    |-- production.py            Production prompts and confirmation
    |-- selling.py               Booth, reservation and sale screens
    |-- reports.py               Report selection and finished-stock correction
    `-- report_tables.py         Individual report tables and formatting
```

`__init__.py` files and a local `tests/` directory may be present in some copies. They are not required to be manually created solely to follow this guide. The JSON data file and its `.lock` file are created/used at runtime.

### 3.1 Root files

#### `cli.py` — the application entry point

- Imports `main` from `ui.menu`.
- Calls that function when you run `python cli.py`.
- Does **not** contain the whole interface or business logic.

#### `api.py` — the REST API controller

- Creates `app = FastAPI(...)`.
- Declares **Pydantic request models**, such as `SaleCreate` and `ProductionCreate`.
- Registers routes such as `GET /api/inventory` and `POST /api/sales`.
- Calls the relevant `business/` function.
- Returns results as JSON and converts business errors into HTTP status codes.

#### `core.py` — shared rules and JSON storage

| Function / item | Job |
| --- | --- |
| `DATA_PATH` | Where the JSON file is stored. Can be changed with the `KAKINA_DATA` environment variable. |
| `SEED_PRODUCTS` / `new_state()` | Builds the first set of products and empty data collections when no data file exists. |
| `RuleError` | Represents an invalid business operation. |
| `locked_state()` | Loads the data; writes a temporary file and replaces the JSON file after successful changes. On Unix-like systems, uses file locking. |
| `read()` | Reads current data without intentionally saving changes. |
| `execute(function, ...)` | Loads state, calls a business function, and saves if the operation succeeds. |
| `get()` | Finds a record by ID or raises an error. |
| `next_id()` | Creates the next record ID. |
| `decimal_amount()`, `whole_number()`, `peso()` | Validate quantities and money. |
| `text_value()`, `optional_text()`, `valid_date()`, `valid_choice()` | Validate text, dates, and choices. |
| `active_product()` | Rejects archived products for new operations. |

**Why `execute()` matters:** The business functions receive a single `state` dictionary. They work on that state, while `core.py` takes responsibility for saving it. Validation errors prevent the normal save step. This helps keep the business functions separate from file handling.

#### `requirements.txt`

Lists the packages installed by `pip install -r requirements.txt`. Do not use it to store application data or custom Python code.

### 3.2 `business/` — calculations and business rules

| File | Important functions | What happens inside |
| --- | --- | --- |
| `business/ingredients.py` | `ingredient_add`, `ingredient_update`, `ingredient_delete`, `purchase_add`, `ingredient_inventory`, `recipe_set` | Registers ingredient names/units, stores purchase quantities/costs, provides average cost values, manages recipes, controls ingredient archiving. |
| `business/products.py` | `product_add`, `product_update`, `product_delete` | Adds and edits chocolate product records; archives only when there is no stock, booth allocation or active reservation. |
| `business/production.py` | `produce` | Verifies all recipe ingredients, checks actual usage against stock, calculates used ingredient cost, reduces ingredient inventory and increases finished chocolate stock. |
| `business/inventory.py` | `reserved`, `allocated`, `free_stock`, `inventory`, `adjust` | Calculates stock that is already committed, displays available units and checks verified physical-stock corrections. |
| `business/selling.py` | `event_open`, `event_close`, `reservation_add`, `reservation_cancel`, `sale_add` | Manages booth stock, customer holds, transaction channels, payment methods, and sale deductions. |
| `business/reports.py` | `reports` | Filters records to a given date if requested; totals sales revenue, fees, ingredient purchases, production ingredient cost and grouped figures. |

**Rule of thumb:** Put changes to **what is allowed or how numbers are calculated** in `business/`, not in the display files.

### 3.3 `ui/` — terminal interface and API communication

| File | Main function(s) | Responsibility |
| --- | --- | --- |
| `ui/client.py` | `ApiClient.call`, `ApiClient.close` | Sends `GET`, `POST`, `PUT`, `DELETE` requests using HTTPX; handles API/network errors. |
| `ui/menu.py` | `dashboard`, `menu`, `start_api`, `main` | Shows the main 9-function dashboard, starts Uvicorn in a background thread and dispatches selected menus. |
| `ui/display.py` | `heading`, `section`, `show_table`, `main_menu`, `success`, `warn`, `error` | Draws plain-text screens, borders and tables; adapts to terminal width. |
| `ui/inputs.py` | `ask`, `intask`, `moneyask`, `amountask`, `ask_date`, `choose`, `confirm`, `action_menu` | Accepts and checks input before sending it to the API. |
| `ui/navigation.py` | `run_section`, `saved`, `cancelled`, `info` | Keeps a feature open after an operation, reloads current records and allows `[0] Back`. |
| `ui/catalog.py` | `inventory_menu`, `ingredients_menu`, `products_menu`, `recipe_menu` | Function 1–3 screens, including active products and a separate archived-products view. |
| `ui/production.py` | `production_menu`, `produce_chocolates` | Function 4: select product, enter actual ingredient use and count finished items. |
| `ui/selling.py` | `booths_menu`, `reservations_menu`, `sales_menu` | Function 5–7: booth allocations, customer reservations and individual transactions. |
| `ui/reports.py` | `reports_menu`, `adjust_menu`, `adjust_stock` | Function 8–9: report selection/date filtering and confirmed stock corrections. |
| `ui/report_tables.py` | `render_report`, `report_table`, other table helpers | Displays summaries, best sellers, revenues, individual sales, production and purchase history. |

**If `ModuleNotFoundError: No module named 'ui.display'` appears:** restore `ui/display.py` from the original repository. Do not delete an entire folder when replacing only selected modules.

---

## 4. REST API explained

**API** means Application Programming Interface. In this project, the terminal program communicates with FastAPI over HTTP on your own computer.

- **Endpoint:** A particular URL, for example `/api/products`.
- **GET:** Read or list saved information.
- **POST:** Create a new record or perform a new action.
- **PUT:** Change an existing record or complete an action.
- **DELETE:** In this project, **archive** a product/ingredient; this is not permanent physical deletion.
- **JSON:** The text format used for request and response data.
- **Pydantic model:** Checks that a request has the required fields and supported types/choices.
- **Status code:** A number describing whether the request succeeded.

### 4.1 Complete API endpoint reference

The following list reflects the routes declared in the repository's `api.py`.

| Method | Endpoint | Purpose | Request body |
| --- | --- | --- | --- |
| `GET` | `/api/health` | Check that the API is running. | None |
| `GET` | `/api/products` | List all products, including archived. | None |
| `GET` | `/api/products/{product_id}` | Read a specific product record. | None |
| `POST` | `/api/products` | Create a new chocolate product. | `name`, `price` |
| `PUT` | `/api/products/{product_id}` | Edit product name and/or price. | `name?`, `price?` |
| `DELETE` | `/api/products/{product_id}` | Archive a product when permitted. | None |
| `GET` | `/api/inventory` | Show active-product inventory, reserved, allocated and available values. | None |
| `GET` | `/api/ingredients` | List ingredients; use `?include_archived=true` to include archived. | None |
| `POST` | `/api/ingredients` | Register ingredient. | `name`, `unit` |
| `PUT` | `/api/ingredients/{ingredient_id}` | Edit ingredient details and optionally stock/value/cost. | Selected fields; `reason` required for financial corrections |
| `DELETE` | `/api/ingredients/{ingredient_id}` | Archive unused ingredient if no recipe/production references. | None |
| `GET` | `/api/ingredient-adjustments` | View ingredient stock/value corrections. | None |
| `GET` | `/api/purchases` | View ingredient purchase history. | None |
| `POST` | `/api/purchases` | Save purchase and add ingredient stock/value. | `ingredient_id`, `quantity`, `total_cost`, `date`, `note?` |
| `PUT` | `/api/products/{product_id}/recipe` | Save/replace suggested recipe quantities. | `items` array |
| `GET` | `/api/production` | List production records. | None |
| `POST` | `/api/production` | Record actual ingredient use and finished products. | `date`, `product_id`, `ingredients_used`, `finished_quantity`, `note?` |
| `GET` | `/api/events` | List booth events. | None |
| `POST` | `/api/events` | Open booth with product allocations. | `name`, `date`, `allocations` |
| `PUT` | `/api/events/{event_id}/close` | Close booth using physically counted leftovers. | `counts` array |
| `GET` | `/api/reservations` | List customer reservations. | None |
| `POST` | `/api/reservations` | Reserve available product stock. | `customer`, `product_id`, `quantity`, `method?`, `date?` |
| `PUT` | `/api/reservations/{reservation_id}/cancel` | Cancel an active reservation. | None |
| `GET` | `/api/sales` | List individual sales. | None |
| `POST` | `/api/sales` | Record a direct/Messenger/booth/reservation sale. | `product_id`, `quantity`, `channel?`, `payment?`, other optional sale fields |
| `GET` | `/api/adjustments` | List finished-product stock corrections. | None |
| `POST` | `/api/adjustments` | Correct physical finished stock with a reason. | `product_id`, `new_stock`, `reason` |
| `GET` | `/api/reports` | Get report totals (all dates or one exact date). | Optional query `?date=YYYY-MM-DD` |

`{product_id}`, `{ingredient_id}`, `{event_id}` and `{reservation_id}` are **URL placeholders**. Replace them with an actual ID, e.g. `/api/products/1`. A question mark in the **Request body** column means a field is optional; it is not part of the JSON key.

### 4.2 Working request examples

The numeric IDs below are **examples only**. First use the corresponding `GET` endpoint to find the IDs in your own data.

**A. Check whether the API is running**

```http
GET http://127.0.0.1:8765/api/health
```

Possible response:

```json
{"status": "ok", "business": "Kakina Food Products Mfg."}
```

**B. Add an ingredient**

```http
POST /api/ingredients
Content-Type: application/json
```

```json
{
  "name": "Cacao powder",
  "unit": "g"
}
```

The API returns a new ingredient ID. Use **that actual ID** in the following examples.

**C. Record an ingredient purchase**

```http
POST /api/purchases
Content-Type: application/json
```

```json
{
  "ingredient_id": 6,
  "quantity": 1000,
  "total_cost": 450,
  "date": "2026-11-11",
  "note": "Example supplier"
}
```

This adds 1,000 g to ingredient #6 and increases its stock value by PHP 450. Ingredient #6 must exist and be active.

**D. Create a suggested recipe for a product**

```http
PUT /api/products/1/recipe
Content-Type: application/json
```

```json
{
  "items": [
    {"ingredient_id": 6, "quantity": 10}
  ]
}
```

This records a suggestion of **10 g per finished product** for product #1. The ingredient and product must exist and be active. A recipe can include multiple ingredients.

**E. Record a production run (actual use, not automatic recipe multiplication)**

```http
POST /api/production
Content-Type: application/json
```

```json
{
  "date": "2026-11-11",
  "product_id": 1,
  "ingredients_used": [
    {"ingredient_id": 6, "quantity": 200}
  ],
  "finished_quantity": 20,
  "note": "Example production run"
}
```

The API checks ingredient stock, deducts **200 g**, adds **20 finished units** to the product, and records the corresponding ingredient cost. This works only after creating the recipe and purchasing enough ingredients. Every ingredient in the recipe must have an actual-usage entry.

**F. Reserve finished products**

```http
POST /api/reservations
Content-Type: application/json
```

```json
{
  "customer": "Sample Customer",
  "product_id": 1,
  "quantity": 3,
  "method": "pickup",
  "date": "2026-11-11"
}
```

The products are held for the customer, but physical product stock is **not deducted yet**. The reservation status becomes `reserved`.

**G. Record a direct sale**

```http
POST /api/sales
Content-Type: application/json
```

```json
{
  "product_id": 1,
  "quantity": 2,
  "channel": "direct",
  "payment": "cash",
  "delivery_fee": 0,
  "customer": "Sample Customer",
  "date": "2026-11-11"
}
```

The product's physical stock decreases by 2 if enough **available stock** exists. The API calculates the subtotal using the product's saved selling price and adds any delivery fee.

**H. View a daily report**

```http
GET /api/reports?date=2026-11-11
```

Omit `?date=...` to include every saved date.

### 4.3 Response codes and errors

| Code | Meaning in this project |
| --- | --- |
| `200 OK` | Request worked; most `GET` and `PUT` operations. |
| `201 Created` | A new purchase, product, production run, event, reservation, sale or adjustment was saved. |
| `204 No Content` | Archive request succeeded; no response body. |
| `400 Bad Request` | A business rule or value is invalid. |
| `404 Not Found` | A requested record does not exist. |
| `409 Conflict` | A stock, reservation, archive or similar business-state restriction prevents the operation. |
| `422 Unprocessable Entity` | FastAPI/Pydantic rejected the request shape, missing required field or invalid type/choice. |

The custom `RuleError` handler chooses some error codes from the error-message text. Therefore, treat `detail` in the JSON response as the **actual explanation**. Do not assume every invalid operation always maps to the same code.

### 4.4 Where the HTTP request is made

The UI does not import each business function and call it directly. Instead, most screens use:

```python
result = api.call('GET', '/api/inventory')
```

`ApiClient.call()` in `ui/client.py` creates an HTTP request. For an operation that changes records, it sends a JSON body, such as:

```python
result = api.call('POST', '/api/products', {
    'name': 'Sample chocolate',
    'price': 50,
})
```

`api.py` matches the method/path and runs the corresponding business function. If there is an error, `ApiClient` raises `ApiError`, and the UI displays the message.

---

## 5. Detailed daily business workflow

Use the features in this order for a typical production-and-selling cycle:

### Step 1 — Register ingredients (Function 2)

Create ingredient records, select their measurement unit (`g`, `kg` or `pcs`), and use purchase records to increase quantity and value.

- The system stores weights in **grams** internally; `kg` is a display/input option.
- A purchase increases **ingredient quantity** and **stock value**.
- The system tracks ingredient purchases separately from production usage.
- Direct ingredient stock/value corrections require a reason and are logged.

### Step 2 — Register products and suggested recipes (Function 3)

Manage product names and selling prices. A recipe defines which ingredients may be used for that product and stores **suggested quantity per finished item**.

**Important:** Saving a recipe does **not** deduct inventory or produce chocolate. The actual weights are entered during production.

The **Show Archived Products** option shows inactive products separately. Archiving does not erase historical sales.

### Step 3 — Produce chocolates (Function 4)

Select a product with a recipe. Enter:

1. Date of production.
2. **Actual quantity** used for each recipe ingredient.
3. **Actual finished quantity** counted after production.
4. Optional production note.

Once saved, the system reduces each ingredient's stock/value and increases the product's finished stock. It saves a production history record with total ingredient cost.

### Step 4 — Allocate products to a booth (Function 5)

Enter the selling location, event date and allocated quantities. Allocated products are still part of physical stock, but they are **not available** for another direct sale or reservation.

For booth sales, use **Function 7** and select channel `booth` plus the correct event ID. Each completed sale deducts physical stock and updates the booth's sold counts.

### Step 5 — Close the booth and count leftovers (Function 5)

After selling, count the remaining units at the booth. The system compares:

```text
Expected unsold = Allocated units - Recorded booth sales
Difference       = Physical count - Expected unsold
```

Closing the booth stores the count and difference and releases the booth allocation. **It does not automatically add missing units or adjust the master stock total.** If the count reveals a discrepancy, investigate first, then use Function 9 if a correction is justified.

### Step 6 — Record customer reservations (Function 6)

Choose a product and quantity, enter the customer's name, and select pickup or delivery.

- A **reserved** quantity reduces available stock but not total physical stock.
- Cancelling an active reservation releases that reserved quantity.
- When the customer buys the order, record a sale through the `reservation` channel in Function 7.
- The current code requires the reservation sale's product and quantity to match the **full active reservation**; partial fulfillment is not supported.

### Step 7 — Record each individual sale (Function 7)

Supported sales channels:

| Channel | How it works |
| --- | --- |
| `direct` | Sale from free finished-product stock. |
| `messenger` | A customer found or ordered through Messenger; deducts free stock when saved. |
| `booth` | Sale connected to an **open event**; deducts from that event's allocated stock. |
| `reservation` | Completes an active reservation using the exact reserved product/quantity. |

Available payment values are **`cash`** and **`gcash`**. Optional customer and delivery-fee fields are available. The API computes:

```text
Subtotal = Selling price x Quantity sold
Total    = Subtotal + Delivery fee
```

The completed sale is appended to sales history and the finished-product stock decreases by the sold quantity.

### Step 8 — Check reports (Function 8)

Choose a date or leave it blank for all dates. Available report views include:

- Business summary
- Best sellers (quantities sold)
- Sales by booth
- Sales by channel
- Daily revenue
- Individual sales history
- Production and purchase history
- All report views

You can return to the report list, change the chosen date, and open another report without returning to the main dashboard.

### Step 9 — Correct finished-product inventory when needed (Function 9)

After physically verifying inventory, enter the **new total stock** and the reason.

The code prevents reducing a product below its current booth allocation plus active reservations. The adjustment is recorded in history. This is a controlled correction, not a sale or production entry.

---

## 6. Inventory, production, and costing rules

### 6.1 Physical stock, reserved, allocated and available

These numbers mean different things:

| Term | Definition |
| --- | --- |
| `stock` | Physical finished units recorded for the product. |
| `reserved` | Units held by active customer reservations. |
| `allocated` | Units still committed to open booths: allocation minus booth sales. |
| `available` | Physical stock minus reserved and allocated stock. |

```text
Available = Stock - Reserved - Allocated
```

**Example:** A product has 50 physical units; 10 are allocated to an open booth, and 5 are reserved.

```text
Stock      = 50
Allocated  = 10
Reserved   =  5
Available  = 35
```

If the booth sells 3, **stock becomes 47** and the remaining allocation becomes **7**, so available stays 35 until the booth is closed or another action changes it. Closing the booth releases its remaining allocation and makes the unsold stock available again.

### 6.2 Ingredient weighted-average cost

Ingredient purchases affect the value of remaining stock:

```text
New quantity   = Old quantity + Purchased quantity
New stock value = Old stock value + Purchase cost
Average cost   = Current stock value / Current stock quantity
```

Example, using grams:

```text
Existing cacao: 500 g, valued at PHP 200
Purchase:       500 g, costing PHP 300
After purchase: 1000 g, valued at PHP 500
Average:        PHP 0.50 per gram
```

The software stores money to centavo precision and performs additional quantity checks.

### 6.3 Cost of a production run

When recording a production run, the program calculates each ingredient's cost using the current weighted-average stock value:

```text
Cost of ingredient used
    = (Current ingredient stock value / Current ingredient stock quantity)
      x Actual quantity used

Production ingredient cost = Sum of the used-ingredient costs
```

For the previous cacao example, using 200 g would cost approximately **PHP 100** and reduce cacao stock to 800 g. If 20 chocolates are counted, 20 finished units are added. The code records **ingredient usage cost**, not every possible business overhead expense.

**Recipe suggestion versus actual production:** The recipe's quantity is a guide per finished unit, but the production record uses the weights the operator actually entered. The current system does not automatically multiply recipe amounts and deduct that estimate.

### 6.4 Ingredient archiving

- An ingredient cannot be archived if it appears in **any saved product recipe**, including an archived product's recipe.
- An ingredient cannot be archived if it appears in **production history**.
- Purchase history alone does not prevent ingredient archiving.
- An otherwise unused ingredient **may be archived even with remaining stock**; that remaining quantity/value is no longer shown in the active ingredient view.

### 6.5 Product archiving

A product can be archived only when it has **no physical finished stock**, **no open booth allocation** and **no active reservation**. Archiving changes its `active` flag rather than deleting the record from history.

### 6.6 Revenue and expenses are not the same as net profit

The report calculation uses:

```text
Product revenue        = Sum of sale subtotals
Delivery fees          = Sum of recorded delivery fees
Total collected        = Product revenue + Delivery fees
Ingredient purchases   = Sum of purchase costs in the selected period
Production use expense = Sum of ingredient-use costs in production records
Displayed difference   = Total collected - Production use expense
```

**The displayed difference is NOT net profit.** It does not fully account for labor, transport, booth rental, electricity, packaging (unless tracked as ingredients), spoilage, unsold goods, or other expenses. Also, a purchase may happen on a different day than the production that uses those ingredients. The system reports **purchases** and **ingredient consumption** as separate measurements; do not simply add them together as though both are newly incurred costs for the same inventory.

---

## 7. JSON data storage explained

### 7.1 Where records go

The default path is a file named **`kakina_data.json`** beside `core.py`. If it is missing, `core.new_state()` creates the initial in-memory state; a saving operation writes the file to disk.

It holds collections such as:

```json
{
  "next_id": 6,
  "products": [],
  "ingredients": [],
  "purchases": [],
  "production": [],
  "events": [],
  "reservations": [],
  "sales": [],
  "adjustments": [],
  "ingredient_adjustments": []
}
```

**This is only a simplified example of the collection names.** A fresh real state also includes five seeded product objects, so do not paste this example over your actual data file.

### 7.2 Why IDs matter

Every saved product, ingredient, sale, event and other record has an ID created by `next_id()`. APIs link records by these IDs (for example, `product_id` in a sale). When testing, always retrieve the actual IDs; do not assume a record will always have ID 1 or 6.

### 7.3 How saving works

On operations routed through `core.execute()`:

1. Open and load the JSON data, or initialize default data if the file does not exist.
2. Run business validation and update in-memory records.
3. If no exception occurs, write the state to a temporary file.
4. Replace the previous JSON file with the completed temporary file.

On systems supporting `fcntl`, the program also locks the data file through a `.lock` companion file while accessing it. The code does **not** provide equivalent `fcntl` locking on Windows, so this should not be treated as a multi-user enterprise database.

---

## 8. Validation and error handling

### Input validation is performed in two places

1. **UI validation** (`ui/inputs.py`) guides the user and reprompts for values that do not match the expected input format.
2. **API/business validation** (`api.py`, `core.py`, `business/*.py`) protects the data even if someone sends an HTTP request directly, without the CLI.

Examples of restrictions:

| Area | Example rule |
| --- | --- |
| Dates | Use a real date in `YYYY-MM-DD` format. |
| Product prices | Valid positive peso amount. |
| Money fields | At most two decimal places for peso amounts. |
| Ingredient units | `g`, `kg` or `pcs`; weight and piece categories cannot be interchanged. |
| Product quantities | Whole numbers, not fractions. |
| Ingredient weights | Decimal amounts, with precision based on unit. |
| Production | Must use the recipe ingredients and cannot exceed ingredient stock. |
| Booth sales | Must use an open booth and available allocated quantity. |
| Reservations | Cannot reserve more than currently free stock. |
| Inventory corrections | Cannot leave less physical stock than reserved + allocated. |
| Archiving | Cannot archive records with prohibited current or historical references. |

HTTP/network errors are caught by `ui/client.py` and shown by the menu system. Damaged JSON triggers an error asking for a backup to be restored; do not replace it with an empty file and lose records.

---

### Suggested IPT-01 demonstration sequence

1. Explain the **CLI -> HTTP API -> business logic -> JSON** architecture.
2. Open `/docs` to show that the system exposes actual HTTP endpoints.
3. Show Function 2 (register ingredient and purchase).
4. Show Function 3 (product and suggested recipe).
5. Show Function 4 (actual weighed usage and counted finished units).
6. Show Function 1 (inventory changes after production).
7. Show Function 5 (allocate to booth), then Function 7 (sell at booth).
8. Show Function 6 (reservation) and a reservation sale.
9. Show Function 8 (reports by date) and Function 9 (stock adjustment).
10. Show the JSON data file and explain why operators should **not** manually edit it.

---

## 9. Scope and known limitations

This is an educational **local application** suitable for explaining modular Python, REST APIs, request validation and JSON-based record keeping.

Current limitations of the reviewed version include:

- **CLI-only interface:** no browser-based management dashboard or mobile UI.
- **Local API:** intended for `127.0.0.1`, not a public deployment.
- **No user login/roles or API authentication:** do not expose the service to an untrusted network.
- **JSON storage:** not a replacement for a centrally managed multi-user database; Windows does not use the same `fcntl` locking as Unix.
- **No POS/payment integration:** GCash and cash are recorded as payment labels; the app does not collect or verify payment.
- **No automatic reconciliation for booth count discrepancies:** adjust verified differences separately.
- **No partial reservation sales** in the current reservation workflow.
- **Reports filter to one exact date or all dates**, not an arbitrary start/end date range.
- **Basic financial reporting:** does not compute complete net profit or full accounting statements.
- **No automatic cloud backup or synchronization.**

These are **scope limits**, not necessarily errors. They identify future improvements for a larger system.

---

## 10. Short reviewer

| Term | Simple explanation |
| --- | --- |
| **CLI** | Command-line interface: the menu you operate in the terminal. |
| **API** | An interface that lets one program request data or actions from another. |
| **REST API** | An HTTP-based API organized around resources and request methods. |
| **Endpoint** | A method and URL, such as `POST /api/sales`. |
| **HTTP** | The protocol used for requests and responses between the CLI and FastAPI. |
| **JSON** | Text format used for API data and local saved records. |
| **FastAPI** | Python framework that defines the project's API routes. |
| **Pydantic** | Checks the required fields and types of incoming API requests. |
| **HTTPX** | Library the CLI uses to make HTTP calls. |
| **Uvicorn** | Server that runs the FastAPI application. |
| **Validation** | Rejecting invalid input before it changes stored data. |
| **Business logic** | Rules for inventory, purchasing, production, selling and reporting. |
| **Weighted average cost** | Cost per stock unit based on current stock value divided by quantity. |
| **Allocation** | Finished products reserved for use at an open booth event. |
| **Reservation** | Stock held for a specific customer but not sold yet. |
| **Archiving** | Marking an item inactive without erasing its saved history. |
