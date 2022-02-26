import datetime
from re import S
import tornado.web
import json
import sqlalchemy


class PurchaseGetHandler(tornado.web.RequestHandler):
    def initialize(self, db):
        self.db = db

    async def get(self, prch_id):
        """
        Return all details of purchase
        """
        prch_id = int(prch_id)
        t_purchase = self.db.metadata.tables['purchase']
        t_products_purchased = self.db.metadata.tables['products_purchased']
        stmt_purchase = sqlalchemy\
            .select(t_purchase)\
            .where(t_purchase.c.id == prch_id)
        stmt_products_purchased = sqlalchemy\
            .select(t_products_purchased)\
            .where(t_products_purchased.c.prch_id == prch_id)
        result = None
        async with self.db.async_engine.begin() as conn:
            cursor = await conn.execute(stmt_purchase)
            for row in cursor:
                result = row._asdict()

            if result is None:
                raise tornado.web.HTTPError(
                    status_code=400, reason='purchase id not in database')

            cursor2 = await conn.execute(stmt_products_purchased)
            result['item_list'] = []
            for row in cursor2:
                result['item_list'].append(row._asdict())
        result['ts'] = datetime.datetime.timestamp(result['ts'])
        self.write(json.dumps(result))


class PurchaseAddHandler(tornado.web.RequestHandler):
    def initialize(self, db):
        self.db = db

    async def post(self):
        """
        If item_list is not provided, just update purchase table
        Otherwise, update products_purchased table as well
        """
        data = json.loads(self.request.body)
        result = {
            'status': 'success',
            'data': None
        }
        t_purchase = self.db.metadata.tables['purchase']
        t_products_purchased = self.db.metadata.tables['products_purchased']

        stmt_purchase = sqlalchemy\
            .insert(t_purchase)\
            .values(
                buyr_id=data['buyr_id'],
                selr_id=data['selr_id'],
                price=data['price'],
                carbon_cost=data['carbon_cost']
            )

        async with self.db.async_engine.begin() as conn:
            cursor = await conn.execute(stmt_purchase)
            prch_id = cursor.inserted_primary_key[0]

            # if product info is provided, add them
            if data['item_list']:
                item_list = list(map(
                    lambda x: dict(
                        prod_id=x['prod_id'], comp_id=x['comp_id'], prch_id=prch_id),
                    data['item_list']
                ))
                await conn.execute(
                    sqlalchemy.insert(t_products_purchased),
                    item_list
                )

            result['data'] = dict(prch_id=prch_id)
            self.write(json.dumps(result))


class PurchaseUpdateHandler(tornado.web.RequestHandler):
    def initialize(self, db):
        self.db = db

    async def post(self):
        """
        if item_list is empty, delete everything in products purchased
        otherwise just add to the tables
        """
        data = json.loads(self.request.body)
        prch_id = data['prch_id']
        result = {
            'status': 'success',
            'data': None
        }
        table_purchase = self.db.metadata.tables['purchase']
        table_products_purchased = self.db.metadata.tables['products_purchased']

        # check prch_id in purchase table
        stmt_check = sqlalchemy\
            .select(table_purchase)\
            .where(table_purchase.c.id == prch_id)

        # updates purchase table
        stmt_purchase = sqlalchemy\
            .update(table_purchase)\
            .where(table_purchase.c.id == prch_id)\
            .values(
                buyr_id=data['buyr_id'],
                selr_id=data['selr_id'],
                price=data['price'],
                carbon_cost=data['carbon_cost']
            )

        # remove all old records from products_purchased table
        stmt_products_purchased_1 = sqlalchemy\
            .delete(table_products_purchased)\
            .where(table_products_purchased.c.prch_id == prch_id)

        async with self.db.async_engine.begin() as conn:
            has_row = False
            for _ in await conn.execute(stmt_check):
                has_row = True
            if not has_row:
                raise tornado.web.HTTPError(
                    status_code=400, reason='purchase id not in database')
            await conn.execute(stmt_purchase)
            await conn.execute(stmt_products_purchased_1)

            # if product info is provided, add them
            if data['item_list']:
                item_list = list(map(
                    lambda x: dict(
                        prod_id=x['prod_id'], comp_id=x['comp_id'], prch_id=prch_id),
                    data['item_list']
                ))
                await conn.execute(
                    sqlalchemy.insert(table_products_purchased),
                    item_list
                )

            result['data'] = dict(prch_id=prch_id)
            self.write(json.dumps(result))
