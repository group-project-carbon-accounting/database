import tornado.web
import json
import sqlalchemy


class PurchaseAddHandler(tornado.web.RequestHandler):
    def initialize(self, db):
        self.db = db

    def post(self):
        data = json.loads(self.request.body)
        result = {
            'status': 'success',
            'data': None
        }
        table_purchase = self.db['metadata'].tables['purchase']
        table_products_purchased = self.db['metadata'].tables['products_purchased']

        stmt_purchase = sqlalchemy\
            .insert(table_purchase)\
            .values(
                buyr_id=data['buyr_id'],
                selr_id=data['selr_id'],
                price=data['price'],
                carbon_cost=0
            )

        with self.db['engine'].begin() as conn:
            cursor = conn.execute(stmt_purchase)
            prch_id = cursor.inserted_primary_key[0]

            # if product info is provided, add them
            if data['item_list']:
                item_list = list(map(
                    lambda x: dict(
                        prod_id=x['prod_id'], comp_id=x['comp_id'], prch_id=prch_id),
                    data['item_list']
                ))
                conn.execute(
                    sqlalchemy.insert(table_products_purchased),
                    item_list
                )

            result['data'] = dict(prch_id=prch_id)
            self.write(json.dumps(result))


class PurchaseUpdateHandler(tornado.web.RequestHandler):
    def initialize(self, db):
        self.db = db

    def post(self):
        data = json.loads(self.request.body)
