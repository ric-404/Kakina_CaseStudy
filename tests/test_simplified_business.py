"""Basic workflow checks for the simplified business modules.
Run from the project root: python -m unittest discover -s tests -p 'test_simplified_business.py' -v
"""
import unittest
import core
from business import ingredients, inventory, production, products, reports, selling


class SimplifiedWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.state = core.new_state()
        self.day = '2026-11-11'

    def make_product(self):
        cacao = ingredients.ingredient_add(self.state, 'Cacao', 'kg')
        self.assertEqual(cacao['unit'], 'g')
        self.assertEqual(cacao['display_unit'], 'kg')
        ingredients.purchase_add(self.state, cacao['id'], 500, 40, self.day)
        ingredients.purchase_add(self.state, cacao['id'], 500, 60, self.day)
        product_id = 2
        ingredients.recipe_set(self.state, product_id,
                               [{'ingredient_id': cacao['id'], 'quantity': 30}])
        return cacao, product_id

    def test_end_to_end_inventory_sales_and_reports(self):
        cacao, product_id = self.make_product()
        record = production.produce(self.state, self.day, product_id,
                                    [{'ingredient_id': cacao['id'], 'quantity': 300}], 10)
        self.assertEqual(record['total_cost'], 30)
        self.assertEqual(cacao['quantity'], 700)
        self.assertEqual(cacao['stock_value'], 70)
        self.assertEqual(inventory.free_stock(self.state, product_id), 10)

        reservation = selling.reservation_add(self.state, 'Sample Customer', product_id, 2,
                                              'pickup', self.day)
        booth = selling.event_open(self.state, 'Talavera', self.day,
                                   [{'product_id': product_id, 'quantity': 3}])
        self.assertEqual(inventory.free_stock(self.state, product_id), 5)

        selling.sale_add(self.state, product_id, 2, date_value=self.day)
        selling.sale_add(self.state, product_id, 1, channel='booth',
                         event_id=booth['id'], date_value=self.day)
        selling.sale_add(self.state, product_id, 2, channel='reservation',
                         reservation_id=reservation['id'], date_value=self.day)
        self.assertEqual(reservation['status'], 'completed')

        counts = [{'product_id': product_id, 'quantity': 2}]
        selling.event_close(self.state, booth['id'], counts)
        self.assertEqual(booth['status'], 'closed')
        self.assertEqual(booth['differences'][str(product_id)], 0)
        self.assertEqual(inventory.free_stock(self.state, product_id), 5)

        summary = reports.reports(self.state, self.day)
        self.assertEqual(summary['sales_revenue'], 200)
        self.assertEqual(summary['sales_count'], 3)
        self.assertEqual(summary['production_count'], 1)
        self.assertEqual(summary['recorded_production_expenses'], 30)
        self.assertEqual(summary['ingredient_purchase_expenses'], 100)
        self.assertEqual(summary['product_quantities_sold'][self.state['products'][1]['name']], 5)
        all_dates = reports.reports(self.state)
        self.assertIsNone(all_dates['filter_date'])
        self.assertEqual(all_dates['sales_revenue'], summary['sales_revenue'])

    def test_stock_guards_and_archiving(self):
        cacao, product_id = self.make_product()
        production.produce(self.state, self.day, product_id,
                           [{'ingredient_id': cacao['id'], 'quantity': 300}], 10)
        selling.reservation_add(self.state, 'Customer', product_id, 3, date_value=self.day)
        with self.assertRaisesRegex(core.RuleError, 'reserved/booth'):
            inventory.adjust(self.state, product_id, 2, 'Physical count')
        with self.assertRaisesRegex(core.RuleError, 'Cannot archive'):
            products.product_delete(self.state, product_id)
        with self.assertRaisesRegex(core.RuleError, 'referenced'):
            ingredients.ingredient_delete(self.state, cacao['id'])

    def test_product_edits_and_duplicate_protection(self):
        product = products.product_add(self.state, 'New chocolate', 55)
        self.assertEqual(product['price'], 55)
        with self.assertRaisesRegex(core.RuleError, 'already has this name'):
            products.product_add(self.state, 'NEW CHOCOLATE', 55)
        updated = products.product_update(self.state, product['id'], price=65)
        self.assertEqual(updated['price'], 65)
        products.product_delete(self.state, product['id'])
        self.assertFalse(product['active'])

    def test_missing_ingredient_does_not_change_stock(self):
        first = ingredients.ingredient_add(self.state, 'Cacao', 'g')
        second = ingredients.ingredient_add(self.state, 'Sugar', 'g')
        ingredients.purchase_add(self.state, first['id'], 100, 20, self.day)
        ingredients.purchase_add(self.state, second['id'], 100, 10, self.day)
        ingredients.recipe_set(self.state, 1, [
            {'ingredient_id': first['id'], 'quantity': 10},
            {'ingredient_id': second['id'], 'quantity': 10},
        ])
        with self.assertRaisesRegex(core.RuleError, 'every recipe ingredient'):
            production.produce(self.state, self.day, 1,
                               [{'ingredient_id': first['id'], 'quantity': 20}], 2)
        self.assertEqual(first['quantity'], 100)
        self.assertEqual(second['quantity'], 100)
        self.assertEqual(self.state['products'][0]['stock'], 0)


if __name__ == '__main__':
    unittest.main()
