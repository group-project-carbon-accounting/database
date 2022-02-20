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

    def test_add_purchase_no_product_info(self):
        """
        tests the case where no items in the transactions were provided
        """
        query = '''
        {
            "buyr_id": 4,
            "selr_id": 6,
            "price": 123,
            "item_list": null
        }
        '''
        # buyr_id, self_id, price, carbon_cost
        expected_purchase = (4, 6, 123, 0)

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
        """
        test all 3 cases:
        only buyer and seller
        buyer, seller and some items with only product
        buyer, seller, items with both product and company
        """

    def test_add_purchase_product_comp_info(self):
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
        expected_purchase = (4, 6, 123, 0)
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
