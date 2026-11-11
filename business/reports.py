"""Calculate reports from the saved sales, production, and purchases."""

from core import valid_date, get


def reports(state, date=None):
    if date:
        date = valid_date(date)

    sales = []
    production = []
    purchases = []

    for sale in state['sales']:
        if not date or sale['date'] == date:
            sales.append(sale)
    for record in state['production']:
        if not date or record['date'] == date:
            production.append(record)
    for purchase in state['purchases']:
        if not date or purchase['date'] == date:
            purchases.append(purchase)

    quantities = {}
    channels = {}
    booths = {}
    payments = {}
    daily = {}

    for sale in sales:
        name = sale['product_name']
        total = sale['total']

        quantities[name] = quantities.get(name, 0) + sale['quantity']

        channel = sale['channel']
        channels[channel] = round(channels.get(channel, 0) + total, 2)

        payment = sale['payment']
        payments[payment] = round(payments.get(payment, 0) + total, 2)

        sale_date = sale['date']
        daily[sale_date] = round(daily.get(sale_date, 0) + total, 2)

        if sale.get('event_id') is not None:
            event = get(state, 'events', sale['event_id'])
            booth_name = event['name']
            booths[booth_name] = round(booths.get(booth_name, 0) + total, 2)

    product_revenue = round(sum(sale['subtotal'] for sale in sales), 2)
    fees = round(sum(sale['delivery_fee'] for sale in sales), 2)
    revenue = round(product_revenue + fees, 2)
    production_cost = round(sum(record['total_cost'] for record in production), 2)
    purchase_cost = round(sum(purchase['total_cost'] for purchase in purchases), 2)

    return {
        'filter_date': date,
        'sales_revenue': revenue,
        'product_revenue': product_revenue,
        'delivery_fees': fees,
        'recorded_production_expenses': production_cost,
        'revenue_less_recorded_expenses_not_profit': round(revenue - production_cost, 2),
        'product_quantities_sold': quantities,
        'revenue_by_channel': channels,
        'revenue_by_booth': booths,
        'revenue_by_payment': payments,
        'revenue_by_date': daily,
        'sales_count': len(sales),
        'production_count': len(production),
        'ingredient_purchase_expenses': purchase_cost
    }
