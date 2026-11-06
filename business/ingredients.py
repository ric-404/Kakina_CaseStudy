"""Ingredient catalog, measured stock, purchases, and product recipes."""
from datetime import date as CalendarDate
from decimal import Decimal, ROUND_HALF_UP
from core import (RuleError, get, next_id, text_value, valid_choice,
                  active_product, peso, valid_date, optional_text,
                  decimal_amount, as_decimal)

def ingredient_add(state, name, unit):
    name = text_value(name, "Ingredient name")
    unit = valid_choice(unit, ("g", "kg", "pcs"), "Ingredient unit")
    if any(item["active"] and item["name"].casefold() == name.casefold()
           for item in state["ingredients"]):
        raise RuleError("An active ingredient with this name already exists.")

    row = {"id": next_id(state), "name": name,
           "unit": "g" if unit == "kg" else unit,
           "display_unit": unit, "quantity": 0, "stock_value": 0.0,
           "active": True}
    state["ingredients"].append(row)
    return row


def active_ingredient(state, ingredient_id):
    ingredient = get(state, "ingredients", ingredient_id)
    if not ingredient["active"]:
        raise RuleError("This ingredient is archived.")
    return ingredient


def display_unit(row):
    """Keep all saved weights in grams, even when the screen uses kg."""
    return row.get("display_unit", row["unit"])


def quantity_in_base(value, unit, base_unit):
    places = 6 if unit == "kg" else 3 if unit == "g" else 0
    amount = decimal_amount(value, "Ingredient stock", allow_zero=True, places=places)
    if unit == "kg":
        amount *= 1000
    return decimal_amount(amount, "Ingredient stock", allow_zero=True,
                          places=3 if base_unit == "g" else 0)


def ingredient_update(state, ingredient_id, name=None, unit=None,
                      quantity=None, stock_value=None, unit_cost=None, reason=""):
    """Edit an ingredient and record any direct stock/cost correction."""
    row = active_ingredient(state, ingredient_id)
    old_qty = as_decimal(row["quantity"])
    old_value = as_decimal(row["stock_value"])

    new_name = text_value(name, "Ingredient name") if name is not None else row["name"]
    if any(item["active"] and item["id"] != ingredient_id and
           item["name"].casefold() == new_name.casefold()
           for item in state["ingredients"]):
        raise RuleError("An active ingredient with this name already exists.")

    current_unit = display_unit(row)
    new_unit = (valid_choice(unit, ("g", "kg", "pcs"), "Ingredient unit")
                if unit is not None else current_unit)
    if row["unit"] == "pcs" and new_unit != "pcs":
        raise RuleError("Pieces cannot be changed to a weight unit.")
    if row["unit"] == "g" and new_unit == "pcs":
        raise RuleError("Weight cannot be changed to pieces.")

    new_qty = (quantity_in_base(quantity, new_unit, row["unit"])
               if quantity is not None else old_qty)
    if stock_value is not None and unit_cost is not None:
        raise RuleError("Edit either stock value or unit cost, not both.")

    if stock_value is not None:
        new_value = as_decimal(peso(stock_value, "Total stock value"))
    elif unit_cost is not None:
        rate = decimal_amount(unit_cost, "Cost per unit", allow_zero=True, places=4)
        display_qty = new_qty / 1000 if new_unit == "kg" else new_qty
        new_value = (rate * display_qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        new_value = as_decimal(peso(new_value, "Total stock value"))
    elif quantity is not None:
        average = old_value / old_qty if old_qty else Decimal("0")
        new_value = (average * new_qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        new_value = old_value

    if new_qty == 0 and new_value != 0:
        raise RuleError("Stock value must be zero when quantity is zero.")

    financial_change = new_qty != old_qty or new_value != old_value
    if financial_change:
        reason = text_value(reason, "Adjustment reason", max_length=300)
        state.setdefault("ingredient_adjustments", []).append({
            "id": next_id(state), "date": CalendarDate.today().isoformat(),
            "ingredient_id": ingredient_id,
            "old_quantity": float(old_qty), "new_quantity": float(new_qty),
            "old_value": float(old_value), "new_value": float(new_value),
            "unit": row["unit"], "reason": reason,
        })

    row["name"] = new_name
    row["display_unit"] = new_unit
    row["quantity"] = float(new_qty) if row["unit"] == "g" else int(new_qty)
    row["stock_value"] = round(float(new_value), 2)
    return row


def ingredient_delete(state, ingredient_id):
    """Archive unused ingredients even if stock remains on hand.

    Purchases are historical receipts, not usage references. They remain saved.
    Recipes (including archived products) and production usage block archiving.
    """
    row = active_ingredient(state, ingredient_id)
    for product in state["products"]:
        if any(x["ingredient_id"] == ingredient_id for x in product.get("recipe", [])):
            raise RuleError("Ingredient is referenced in a product recipe. Remove the recipe link first.")
    for run in state["production"]:
        if any(x["ingredient_id"] == ingredient_id
               for x in run.get("ingredients_used", [])):
            raise RuleError("Ingredient is referenced in production history and cannot be archived.")
    row["active"] = False
    return row

def purchase_add(state, ingredient_id, quantity, total_cost, purchase_date, note=""):
    """Add a real purchase; update weighted-average ingredient stock value."""
    row = active_ingredient(state, ingredient_id)
    quantity = decimal_amount(quantity, "Purchased quantity", places=3 if row["unit"] == "g" else 0)
    cost = peso(total_cost, "Total purchase cost", allow_zero=False)
    purchase_date = valid_date(purchase_date)
    note = optional_text(note)
    old_qty = as_decimal(row["quantity"])
    new_qty = old_qty + quantity
    row["quantity"] = float(new_qty) if row["unit"] == "g" else int(new_qty)
    row["stock_value"] = round(float(as_decimal(row["stock_value"]) + as_decimal(cost)), 2)
    record = {"id": next_id(state), "date": purchase_date, "ingredient_id": ingredient_id,
              "quantity": float(quantity) if row["unit"] == "g" else int(quantity),
              "unit": row["unit"], "total_cost": cost, "note": note}
    state["purchases"].append(record)
    return record

def ingredient_inventory(state, include_archived=False):
    result = []
    for row in state["ingredients"]:
        if not row["active"] and not include_archived:
            continue
        unit = display_unit(row)
        quantity = as_decimal(row["quantity"])
        value = as_decimal(row["stock_value"])
        displayed = quantity / 1000 if unit == "kg" else quantity
        cost = value / displayed if displayed else Decimal("0")
        average = value / quantity if quantity else Decimal("0")
        result.append({**row,
                       "display_unit": unit,
                       "display_quantity": float(displayed),
                       "average_display_cost": round(float(cost), 4),
                       "average_unit_cost": round(float(average), 4)})
    return result

def recipe_set(state, product_id, items):
    """Save suggested quantities per finished piece; production uses actual weights."""
    product = active_product(state, product_id)
    if not isinstance(items, list) or not items:
        raise RuleError("Add at least one ingredient to the product recipe.")
    ids, recipe = set(), []
    for item in items:
        iid = item.get("ingredient_id")
        ingredient = active_ingredient(state, iid)
        if iid in ids:
            raise RuleError("The same ingredient appears twice in one recipe.")
        ids.add(iid)
        amount = decimal_amount(item.get("quantity"), "Recipe amount",
                                places=3 if ingredient["unit"] == "g" else 0)
        recipe.append({"ingredient_id": iid,
                       "quantity": float(amount) if ingredient["unit"] == "g" else int(amount)})
    product["recipe"] = recipe
    return product
