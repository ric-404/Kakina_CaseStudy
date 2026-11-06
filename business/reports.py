"""Date-filtered reports: revenue, product sales, purchases and production costs."""
from core import valid_date, get


def reports(state, date=None):
    if date:
        date = valid_date(date)
    sales = [x for x in state['sales'] if not date or x['date'] == date]
    production = [x for x in state['production'] if not date or x['date'] == date]
    purchases = [x for x in state['purchases'] if not date or x['date'] == date]
    quantities, channels, booths, payments, daily = {}, {}, {}, {}, {}
    for sale in sales:
        name = sale['product_name']
        quantities[name] = quantities.get(name, 0) + sale['quantity']
        for table, key in ((channels, sale['channel']), (payments, sale['payment']), (daily, sale['date'])):
            table[key] = round(table.get(key, 0) + sale['total'], 2)
        if sale.get('event_id') is not None:
            booth = get(state, 'events', sale['event_id'])['name']
            booths[booth] = round(booths.get(booth, 0) + sale['total'], 2)
    product_revenue = round(sum(x['subtotal'] for x in sales), 2)
    fees = round(sum(x['delivery_fee'] for x in sales), 2)
    revenue = round(product_revenue + fees, 2)
    production_cost = round(sum(x['total_cost'] for x in production), 2)
    return {'filter_date': date, 'sales_revenue': revenue, 'product_revenue': product_revenue,
            'delivery_fees': fees, 'recorded_production_expenses': production_cost,
            'revenue_less_recorded_expenses_not_profit': round(revenue - production_cost, 2),
            'product_quantities_sold': quantities, 'revenue_by_channel': channels,
            'revenue_by_booth': booths, 'revenue_by_payment': payments,
            'revenue_by_date': daily, 'sales_count': len(sales),
            'production_count': len(production),
            'ingredient_purchase_expenses': round(sum(x['total_cost'] for x in purchases), 2)}
