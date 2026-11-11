"""FastAPI endpoints for the Kakina terminal client (HTTP + JSON)."""
from typing import Literal
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, StrictInt, StrictFloat
import core
from business import ingredients as ing, products as products_service
from business import inventory as stock, production as production_service
from business import selling as selling_service, reports as report_service

app = FastAPI(title='Kakina Food Products Mfg. REST API', version='2.0.0')
Money = StrictInt | StrictFloat


@app.exception_handler(core.RuleError)
async def handle_error(request, exc):
    message = str(exc)
    if 'not found' in message.lower():
        code = 404
    elif any(term in message.lower() for term in
             ('stock', 'not enough', 'already', 'archived', 'reserved', 'referenced', 'cannot archive')):
        code = 409
    else:
        code = 400
    return JSONResponse(status_code=code, content={'detail': message})


class ProductCreate(BaseModel):
    name: str
    price: Money


class ProductEdit(BaseModel):
    name: str | None = None
    price: Money | None = None


class IngredientCreate(BaseModel):
    name: str
    unit: Literal['g', 'kg', 'pcs']


class IngredientEdit(BaseModel):
    name: str | None = None
    unit: Literal['g', 'kg', 'pcs'] | None = None
    quantity: Money | None = None
    stock_value: Money | None = None
    unit_cost: Money | None = None
    reason: str = ''


class PurchaseCreate(BaseModel):
    ingredient_id: StrictInt
    quantity: Money
    total_cost: Money
    date: str
    note: str = ''


class RecipeItem(BaseModel):
    ingredient_id: StrictInt
    quantity: Money


class RecipeUpdate(BaseModel):
    items: list[RecipeItem]


class ProductQty(BaseModel):
    product_id: StrictInt
    quantity: StrictInt


class ProductionCreate(BaseModel):
    date: str
    product_id: StrictInt
    ingredients_used: list[RecipeItem]
    finished_quantity: StrictInt
    note: str = ''


class EventCreate(BaseModel):
    name: str
    date: str
    allocations: list[ProductQty]


class EventClose(BaseModel):
    counts: list[ProductQty]


class ReservationCreate(BaseModel):
    customer: str
    product_id: StrictInt
    quantity: StrictInt
    method: Literal['pickup', 'delivery'] = 'pickup'
    date: str | None = None


class SaleCreate(BaseModel):
    product_id: StrictInt
    quantity: StrictInt
    channel: Literal['direct', 'messenger', 'booth', 'reservation'] = 'direct'
    event_id: int | None = None
    reservation_id: int | None = None
    payment: Literal['cash', 'gcash'] = 'cash'
    delivery_fee: Money = 0
    customer: str = ''
    date: str | None = None


class AdjustmentCreate(BaseModel):
    product_id: StrictInt
    new_stock: StrictInt
    reason: str


@app.get('/api/health')
def health():
    return {'status': 'ok', 'business': 'Kakina Food Products Mfg.'}


@app.get('/api/products')
def products():
    return core.read()['products']


@app.get('/api/products/{product_id}')
def product(product_id: int):
    return core.get(core.read(), 'products', product_id)


@app.post('/api/products', status_code=201)
def add_product(data: ProductCreate):
    return core.execute(products_service.product_add, data.name, data.price)


@app.put('/api/products/{product_id}')
def edit_product(product_id: int, data: ProductEdit):
    return core.execute(products_service.product_update, product_id, data.name, data.price)


@app.delete('/api/products/{product_id}', status_code=204)
def archive_product(product_id: int):
    core.execute(products_service.product_delete, product_id)
    return Response(status_code=204)


@app.get('/api/inventory')
def inventory():
    return stock.inventory(core.read())


@app.get('/api/ingredients')
def ingredients(include_archived: bool = False):
    return ing.ingredient_inventory(core.read(), include_archived)


@app.post('/api/ingredients', status_code=201)
def add_ingredient(data: IngredientCreate):
    return core.execute(ing.ingredient_add, data.name, data.unit)


@app.put('/api/ingredients/{ingredient_id}')
def edit_ingredient(ingredient_id: int, data: IngredientEdit):
    return core.execute(ing.ingredient_update, ingredient_id,
                        data.name, data.unit, data.quantity,
                        data.stock_value, data.unit_cost, data.reason)


@app.delete('/api/ingredients/{ingredient_id}', status_code=204)
def archive_ingredient(ingredient_id: int):
    core.execute(ing.ingredient_delete, ingredient_id)
    return Response(status_code=204)


@app.get('/api/ingredient-adjustments')
def ingredient_adjustments():
    return core.read()['ingredient_adjustments']


@app.get('/api/purchases')
def purchases():
    return core.read()['purchases']


@app.post('/api/purchases', status_code=201)
def record_purchase(data: PurchaseCreate):
    return core.execute(ing.purchase_add, data.ingredient_id,
                        data.quantity, data.total_cost, data.date, data.note)


@app.put('/api/products/{product_id}/recipe')
def save_recipe(product_id: int, data: RecipeUpdate):
    return core.execute(ing.recipe_set, product_id, [x.model_dump() for x in data.items])


@app.get('/api/production')
def production():
    return core.read()['production']


@app.post('/api/production', status_code=201)
def record_production(data: ProductionCreate):
    return core.execute(production_service.produce, data.date, data.product_id,
                        [x.model_dump() for x in data.ingredients_used],
                        data.finished_quantity, data.note)


@app.get('/api/events')
def events():
    return core.read()['events']


@app.post('/api/events', status_code=201)
def open_event(data: EventCreate):
    return core.execute(selling_service.event_open, data.name, data.date,
                        [x.model_dump() for x in data.allocations])


@app.put('/api/events/{event_id}/close')
def close_event(event_id: int, data: EventClose):
    return core.execute(selling_service.event_close, event_id,
                        [x.model_dump() for x in data.counts])


@app.get('/api/reservations')
def reservations():
    return core.read()['reservations']


@app.post('/api/reservations', status_code=201)
def add_reservation(data: ReservationCreate):
    return core.execute(selling_service.reservation_add, data.customer,
                        data.product_id, data.quantity, data.method, data.date)


@app.put('/api/reservations/{reservation_id}/cancel')
def cancel_reservation(reservation_id: int):
    return core.execute(selling_service.reservation_cancel, reservation_id)


@app.get('/api/sales')
def sales():
    return core.read()['sales']


@app.post('/api/sales', status_code=201)
def record_sale(data: SaleCreate):
    return core.execute(selling_service.sale_add, data.product_id, data.quantity,
                        data.channel, data.event_id, data.reservation_id,
                        data.payment, data.date, data.delivery_fee, data.customer)


@app.get('/api/adjustments')
def adjustments():
    return core.read()['adjustments']


@app.post('/api/adjustments', status_code=201)
def record_adjustment(data: AdjustmentCreate):
    return core.execute(stock.adjust, data.product_id, data.new_stock, data.reason)


@app.get('/api/reports')
def reports(date: str | None = None):
    return report_service.reports(core.read(), date)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('api:app', host='127.0.0.1', port=8765)
