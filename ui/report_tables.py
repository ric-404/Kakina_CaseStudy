"""Small bordered ASCII tables for Kakina sales, production and purchase reports."""
import shutil

from ui.display import heading, notice, pesos, shorten, wrap_name


def report_table(title, headers, records):
    """Print a readable table; use bordered records if the terminal is narrow."""
    records = [[str(item) for item in row] for row in records]
    headers = [str(item) for item in headers]
    print(f"\n  {title.upper()}")
    if not records:
        print("  No records for the selected date.\n")
        return

    maximum_width = max(45, shutil.get_terminal_size((100, 24)).columns - 4)
    name_columns = {i for i, name in enumerate(headers)
                    if any(key in name.lower() for key in
                           ("product", "ingredient", "customer", "location", "name", "reason"))}
    widths = [min(32 if i in name_columns else 22,
                  max(len(headers[i]), *(len(row[i]) for row in records)))
              for i in range(len(headers))]
    minimums = [min(width, max(5, min(len(headers[i]), 12 if i in name_columns else 8)))
                for i, width in enumerate(widths)]
    while sum(widths) + 3 * len(widths) + 1 > maximum_width:
        flexible = [i for i in range(len(widths)) if widths[i] > minimums[i]]
        if not flexible:
            break
        index = max(flexible, key=lambda i: widths[i] - minimums[i])
        widths[index] -= 1

    if sum(widths) + 3 * len(widths) + 1 > maximum_width:
        for record in records:
            width = min(75, maximum_width - 4)
            print("  +" + "-" * (width + 2) + "+")
            for label, value in zip(headers, record):
                prefix = f"{label}: "
                for part in wrap_name(prefix + value, width):
                    print("  | " + part.ljust(width) + " |")
            print("  +" + "-" * (width + 2) + "+")
        return

    line = "  +" + "+".join("-" * (width + 2) for width in widths) + "+"
    print(line)
    print("  | " + " | ".join(shorten(h, w).ljust(w) for h, w in zip(headers, widths)) + " |")
    print(line)
    for record in records:
        cells = []
        for i, value in enumerate(record):
            cells.append(wrap_name(value, widths[i]) if i in name_columns
                         else [shorten(value, widths[i])])
        for row_index in range(max(len(cell) for cell in cells)):
            print("  | " + " | ".join(
                (cell[row_index] if row_index < len(cell) else "").ljust(width)
                for cell, width in zip(cells, widths)) + " |")
        print(line)
    print()


def summary_table(report, day):
    rows = [
        ("Total collected", pesos(report["sales_revenue"])),
        ("Product sales", pesos(report["product_revenue"])),
        ("Delivery fees", pesos(report["delivery_fees"])),
        ("Ingredient purchases", pesos(report["ingredient_purchase_expenses"])),
        ("Ingredients used in production", pesos(report["recorded_production_expenses"])),
        ("Revenue minus ingredient use", pesos(report["revenue_less_recorded_expenses_not_profit"])),
        ("Transactions", report["sales_count"]),
        ("Production runs", report["production_count"]),
    ]
    report_table(f"Business summary ({day or 'all dates'})", ["Item", "Amount"], rows)
    notice("Revenue minus ingredient use is NOT net profit.")


def quantity_table(report):
    rows = sorted(report["product_quantities_sold"].items(), key=lambda item: (-item[1], item[0]))
    report_table("Best sellers", ["Product", "Units sold"], rows)


def revenue_table(title, key, report):
    rows = sorted(report[key].items(), key=lambda row: row[0])
    report_table(title, [title.split(" by ")[-1].capitalize(), "Revenue"],
                 [(label, pesos(amount)) for label, amount in rows])


def sales_table(api, day):
    sales = [row for row in api.call("GET", "/api/sales")
             if not day or row["date"] == day]
    report_table("Individual sales history",
                 ["ID", "Date", "Product", "Qty", "Channel", "Total"],
                 [(row["id"], row["date"], row.get("product_name", ""), row["quantity"],
                   row["channel"], pesos(row["total"])) for row in sales])


def production_purchase_tables(api, day):
    runs = [row for row in api.call("GET", "/api/production")
            if not day or row["date"] == day]
    report_table("Production history", ["ID", "Date", "Product", "Units", "Cost"],
                 [(row["id"], row["date"], row.get("product_name", row.get("product_id", "")),
                   row.get("finished_quantity", sum(i["quantity"] for i in row.get("outputs", []))),
                   pesos(row["total_cost"])) for row in runs])

    purchases = [row for row in api.call("GET", "/api/purchases")
                 if not day or row["date"] == day]
    names = {row["id"]: row["name"] for row in
             api.call("GET", "/api/ingredients", params={"include_archived": True})}
    report_table("Ingredient purchases", ["ID", "Date", "Ingredient", "Quantity", "Paid"],
                 [(row["id"], row["date"], names.get(row["ingredient_id"], "#" + str(row["ingredient_id"])),
                   f"{row['quantity']:g} {row['unit']}" if isinstance(row["quantity"], (int, float))
                   else f"{row['quantity']} {row['unit']}",
                   pesos(row["total_cost"])) for row in purchases])


def render_report(api, day, choice):
    heading("Report: " + choice.replace("_", " ").title(),
            f"Reporting date: {day or 'all dates'}")
    report = api.call("GET", "/api/reports", params={"date": day} if day else None)
    if choice in ("summary", "all"):
        summary_table(report, day)
    if choice in ("bestsellers", "all"):
        quantity_table(report)
    if choice in ("booths", "all"):
        revenue_table("Sales by booth", "revenue_by_booth", report)
    if choice in ("channels", "all"):
        revenue_table("Sales by channel", "revenue_by_channel", report)
    if choice in ("daily", "all"):
        report_table("Daily revenue", ["Date", "Revenue"],
                     [(date, pesos(amount)) for date, amount in
                      sorted(report["revenue_by_date"].items())])
    if choice in ("sales", "all"):
        sales_table(api, day)
    if choice in ("production", "all"):
        production_purchase_tables(api, day)
