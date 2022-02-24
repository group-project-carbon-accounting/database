from types import SimpleNamespace
import main
import tornado
import configparser
import sqlalchemy
import json


class TestApp(tornado.testing.AsyncHTTPTestCase):
    def __init__(self, *args, **kwargs) -> None:
        """
        Initialise the test database with fixture data
        Add the following 2 fields for utility purposes
        self.config
        self.db
        """
        super().__init__(*args, **kwargs)
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        mode = 'TEST'
        self.config['MODE']['mode'] = mode

        # initialise own connection to db to verify correctness of handlers
        engine = sqlalchemy.create_engine(
            self.config[mode]['database_url'], echo=True, future=True)
        with open('test/integration/fixtures/initialise_postgresdb.sql') as f:
            stmt = sqlalchemy.text(''.join(f.readlines()))

        with engine.begin() as conn:
            conn.execute(stmt)

        metadata = sqlalchemy.MetaData()
        entity = sqlalchemy.Table(
            'entity', metadata, autoload=True, autoload_with=engine)
        product = sqlalchemy.Table(
            'product', metadata, autoload=True, autoload_with=engine)
        company_product = sqlalchemy.Table(
            'company_product', metadata, autoload=True, autoload_with=engine)
        purchase = sqlalchemy.Table(
            'purchase', metadata, autoload=True, autoload_with=engine)
        products_purchased = sqlalchemy.Table(
            'products_purchased', metadata, autoload=True, autoload_with=engine)
        self.db = SimpleNamespace(engine=engine, metadata=metadata)

    def get_app(self):
        return main.make_app(self.config)

    def test_ping(self):
        """
        self-explanatory
        """
        response = self.fetch('/ping')
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body, b'pong!')

    def test_purchase_get(self):
        expected_result = json.loads('''
        {
            "id": 1,
            "buyr_id": 1,
            "selr_id": 6,
            "price": 1200,
            "carbon_cost": 0,
            "item_list": [
                {
                    "prch_id": 1,
                    "comp_id": 6,
                    "prod_id": 1
                },
                {
                    "prch_id": 1,
                    "comp_id": 6,
                    "prod_id": 2
                }
            ]
        }
        ''')
        response = self.fetch(
            path='/purchase/get/1',
            method='GET'
        )
        self.assertEqual(response.code, 200)
        json_body = json.loads(response.body)
        del json_body['ts']
        self.assertEqual(expected_result, json_body)

    def test_purchase_add_no_product_info(self):
        """
        tests the case where no items in the transactions were provided
        """
        query = '''
        {
            "buyr_id": 4,
            "selr_id": 6,
            "price": 123,
            "carbon_cost": 345,
            "item_list": null
        }
        '''
        # buyr_id, self_id, price, carbon_cost
        expected_purchase = (4, 6, 123, 345)

        response = self.fetch(
            path='/purchase/add',
            method='POST',
            body=query
        )
        self.assertEqual(response.code, 200)
        json_body = json.loads(response.body)
        table_purchase = self.db.metadata.tables['purchase']
        stmt = sqlalchemy\
            .select(
                table_purchase.c.buyr_id,
                table_purchase.c.selr_id,
                table_purchase.c.price,
                table_purchase.c.carbon_cost
            )\
            .select_from(table_purchase)\
            .where(table_purchase.c.id == json_body['data']['prch_id'])
        with self.db.engine.begin() as conn:
            for result in conn.execute(stmt):
                self.assertEqual(result, expected_purchase)

    def test_purchase_add_product_comp_info(self):
        """
        tests the case where some items are provided with only product
        info, and others are provided with both product info and 
        company info
        """
        query = '''
        {
            "prch_id": 1,
            "buyr_id": 4,
            "selr_id": 6,
            "price": 123,
            "carbon_cost": 234,
            "item_list": [
                {
                    "prod_id": 1,
                    "comp_id": null
                },
                {
                    "prod_id": 3,
                    "comp_id": null
                },
                {
                    "prod_id": 4,
                    "comp_id": 6
                }
            ]
        }
        '''
        # buyr_id, self_id, price, carbon_cost
        expected_purchase = (4, 6, 123, 234)
        # prod_id, comp_id
        expected_products_purchased = [
            (1, None),
            (3, None),
            (4, 6)
        ]

        response = self.fetch(
            path='/purchase/add',
            method='POST',
            body=query
        )
        self.assertEqual(response.code, 200)
        json_body = json.loads(response.body)
        prch_id = json_body['data']['prch_id']
        table_purchase = self.db.metadata.tables['purchase']
        stmt = sqlalchemy\
            .select(
                table_purchase.c.buyr_id,
                table_purchase.c.selr_id,
                table_purchase.c.price,
                table_purchase.c.carbon_cost
            )\
            .select_from(table_purchase)\
            .where(table_purchase.c.id == prch_id)
        with self.db.engine.begin() as conn:
            for result in conn.execute(stmt):
                self.assertEqual(result, expected_purchase)

        table_products_purchased = self.db.metadata.tables['products_purchased']
        stmt2 = sqlalchemy\
            .select(
                table_products_purchased.c.prod_id,
                table_products_purchased.c.comp_id,
            )\
            .select_from(table_products_purchased)\
            .where(table_products_purchased.c.prch_id == prch_id)
        with self.db.engine.begin() as conn:
            result = conn.execute(stmt2)
            result = sorted(list(map(tuple, result)))
            self.assertEqual(expected_products_purchased, result)

    def test_purchase_update_missing(self):
        """
        test that purchase update fails when prch_id not in table
        """
        query = '''
        {
            "prch_id": 11,
            "buyr_id": 4,
            "selr_id": 6,
            "price": 123,
            "carbon_cost": null,
            "item_list": null
        } 
        '''

        response = self.fetch(
            path='/purchase/update',
            method='POST',
            body=query
        )
        self.assertEqual(response.code, 500)

    def test_purchase_update_no_product_info(self):
        """
        tests if purchase table is modified correctly,
        and products_purchased entries are deleted.
        """
        query = '''
        {
            "prch_id": 1,
            "buyr_id": 4,
            "selr_id": 6,
            "price": 123,
            "carbon_cost": null,
            "item_list": null
        } 
        '''
        # buyr_id, self_id, price, carbon_cost
        expected_purchase = (4, 6, 123, None)
        expected_products_purchased = []

        response = self.fetch(
            path='/purchase/update',
            method='POST',
            body=query
        )
        self.assertEqual(response.code, 200)
        json_body = json.loads(response.body)
        prch_id = json_body['data']['prch_id']
        table_purchase = self.db.metadata.tables['purchase']
        stmt = sqlalchemy\
            .select(
                table_purchase.c.buyr_id,
                table_purchase.c.selr_id,
                table_purchase.c.price,
                table_purchase.c.carbon_cost
            )\
            .select_from(table_purchase)\
            .where(table_purchase.c.id == json_body['data']['prch_id'])
        with self.db.engine.begin() as conn:
            for result in conn.execute(stmt):
                self.assertEqual(result, expected_purchase)

        table_products_purchased = self.db.metadata.tables['products_purchased']
        stmt2 = sqlalchemy\
            .select(
                table_products_purchased.c.prod_id,
                table_products_purchased.c.comp_id,
            )\
            .select_from(table_products_purchased)\
            .where(table_products_purchased.c.prch_id == prch_id)
        with self.db.engine.begin() as conn:
            result = conn.execute(stmt2)
            result = sorted(list(map(tuple, result)))
            self.assertEqual(expected_products_purchased, result)

    def test_purchase_update_product_info(self):
        """
        tests if purchase table is modified correctly,
        and products_purchased entries are updated.
        """
        query = '''
        {
            "prch_id": 1,
            "buyr_id": 4,
            "selr_id": 6,
            "price": 123,
            "carbon_cost": 1000,
            "item_list": [
                {
                    "prod_id": 1,
                    "comp_id": 6
                },
                {
                    "prod_id": 3,
                    "comp_id": 6
                },
                {
                    "prod_id": 4,
                    "comp_id": 6
                }
            ]
        } 
        '''
        # buyr_id, self_id, price, carbon_cost
        expected_purchase = (4, 6, 123, 1000)
        expected_products_purchased = [
            (1, 6), (3, 6), (4, 6)
        ]

        response = self.fetch(
            path='/purchase/update',
            method='POST',
            body=query
        )
        self.assertEqual(response.code, 200)
        json_body = json.loads(response.body)
        prch_id = json_body['data']['prch_id']
        table_purchase = self.db.metadata.tables['purchase']
        stmt = sqlalchemy\
            .select(
                table_purchase.c.buyr_id,
                table_purchase.c.selr_id,
                table_purchase.c.price,
                table_purchase.c.carbon_cost
            )\
            .select_from(table_purchase)\
            .where(table_purchase.c.id == json_body['data']['prch_id'])
        with self.db.engine.begin() as conn:
            for result in conn.execute(stmt):
                self.assertEqual(result, expected_purchase)

        table_products_purchased = self.db.metadata.tables['products_purchased']
        stmt2 = sqlalchemy\
            .select(
                table_products_purchased.c.prod_id,
                table_products_purchased.c.comp_id,
            )\
            .select_from(table_products_purchased)\
            .where(table_products_purchased.c.prch_id == prch_id)
        with self.db.engine.begin() as conn:
            result = conn.execute(stmt2)
            result = sorted(list(map(tuple, result)))
            self.assertEqual(expected_products_purchased, result)

    def test_product_get_not_in_comp_prod(self):
        expected_result = json.loads('''
        {
            "prod_id": 1,
            "carbon_cost": 3300,
            "comp_id": null
        }        
        ''')
        response = self.fetch(
            path='/product/get/7/1',
            method='GET'
        )
        self.assertEqual(response.code, 200)
        json_body = json.loads(response.body)
        self.assertEqual(expected_result, json_body)

    def test_product_get_in_comp_prod(self):
        expected_result = json.loads('''
        {
            "prod_id": 1,
            "carbon_cost": 2300,
            "comp_id": 6
        }        
        ''')
        response = self.fetch(
            path='/product/get/6/1',
            method='GET'
        )
        self.assertEqual(response.code, 200)
        json_body = json.loads(response.body)
        self.assertEqual(expected_result, json_body)

    def test_product_add(self):
        query = '''
        {
            "prod_id": 2,
            "comp_id": 6,
            "carbon_cost": 1000
        }        
        '''
        # comp_id, prod_id, carbon_cost
        expected_company_product = (6, 2, 1000)
        response = self.fetch(
            path='/product/add',
            method='POST',
            body=query
        )
        self.assertEqual(response.code, 200)
        json_body = json.loads(response.body)
        t_company_product = self.db.metadata.tables['company_product']
        stmt = sqlalchemy\
            .select(t_company_product)
        with self.db.engine.begin() as conn:
            result = conn.execute(stmt)
            self.assertIn(expected_company_product, result)

    def test_product_update_prod_id_none(self):
        query = '''
        {
            "prod_id": null,
            "comp_id": 6,
            "carbon_cost": 1000
        }        
        '''
        # id, display_name, carbon_offset, carbon_cost
        expected_entity = (6, 'Sainsburrows', 0, 1000)
        response = self.fetch(
            path='/product/update',
            method='POST',
            body=query
        )
        self.assertEqual(response.code, 200)
        json_body = json.loads(response.body)
        t_entity = self.db.metadata.tables['entity']
        stmt = sqlalchemy\
            .select(t_entity)\
            .where(t_entity.c.id == expected_entity[0])
        with self.db.engine.begin() as conn:
            for result in conn.execute(stmt):
                self.assertEqual(expected_entity, result)

    def test_product_update_comp_id_none(self):
        query = '''
        {
            "prod_id": 2,
            "comp_id": null,
            "carbon_cost": 1000
        }        
        '''
        # id, item_name, carbon_cost
        expected_product = (2, 'cheese', 1000)
        response = self.fetch(
            path='/product/update',
            method='POST',
            body=query
        )
        self.assertEqual(response.code, 200)
        json_body = json.loads(response.body)
        t_product = self.db.metadata.tables['product']
        stmt = sqlalchemy\
            .select(t_product)\
            .where(t_product.c.id == expected_product[0])
        with self.db.engine.begin() as conn:
            for result in conn.execute(stmt):
                self.assertEqual(expected_product, result)

    def test_product_update_both_valid(self):
        query = '''
        {
            "prod_id": 1,
            "comp_id": 6,
            "carbon_cost": 1000
        }        
        '''
        # comp_id, prod_id, carbon_cost
        expected_company_product = (6, 1, 1000)
        response = self.fetch(
            path='/product/update',
            method='POST',
            body=query
        )
        self.assertEqual(response.code, 200)
        json_body = json.loads(response.body)
        t_company_product = self.db.metadata.tables['company_product']
        stmt = sqlalchemy\
            .select(t_company_product)
        with self.db.engine.begin() as conn:
            result = conn.execute(stmt)
            self.assertIn(expected_company_product, result)

    def test_entity_get(self):
        expected = json.loads('''
        {
            "id": 1,
            "display_name": "Albert",
            "carbon_offset": 0,
            "carbon_cost": 0
        }
        ''')
        response = self.fetch(
            path='/entity/get/1',
            method='GET'
        )
        self.assertEqual(response.code, 200)
        json_body = json.loads(response.body)
        self.assertEqual(expected, json_body)

    def test_entity_purchases_get(self):
        expected = json.loads('''
        {
            "user_id": 2,
            "purchase_list": [
                {
                    "id": 2,
                    "buyr_id": 2,
                    "selr_id": 8,
                    "price": 200000,
                    "carbon_cost": 0
                }
            ]
        }
        ''')

        response = self.fetch(
            path='/entity/purchases/get/2?start_ts=145435764&end_ts=2645435774',
            method='GET'
        )
        self.assertEqual(response.code, 200)
        json_body = json.loads(response.body)
        for purchase in json_body['purchase_list']:
            purchase.pop('ts')
        self.assertEqual(expected, json_body)

    def test_entity_update_missing(self):
        """
        test update fails when entity id not in table
        """
        query = '''
        {
            "id": 69,
            "carbon_offset": 10,
            "carbon_cost": 10
        }
        '''

        response = self.fetch(
            path='/entity/update',
            method='POST',
            body=query
        )

        self.assertEqual(response.code, 500)

    def test_entity_update_normal(self):
        """
        test that entity updates correctly
        """
        query = '''
        {
            "id": 1,
            "carbon_offset": 10,
            "carbon_cost": 10
        }
        '''
        # id, display_name, carbon_offset, carbon_cost
        expected_result = (1, 'Albert', 10, 10)

        response = self.fetch(
            path='/entity/update',
            method='POST',
            body=query
        )

        self.assertEqual(response.code, 200)
        json_body = json.loads(response.body)
        id = json_body['data']['id']

        t_entity = self.db.metadata.tables['entity']
        stmt = sqlalchemy\
            .select(t_entity)\
            .where(t_entity.c.id == id)

        with self.db.engine.begin() as conn:
            for row in conn.execute(stmt):
                self.assertEqual(expected_result, row)
