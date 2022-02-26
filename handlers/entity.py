import datetime
import tornado.web
import json
import sqlalchemy


class EntityGetHandler(tornado.web.RequestHandler):
    def initialize(self, db):
        self.db = db

    async def get(self, user_id):
        user_id = int(user_id)

        t_entity = self.db.metadata.tables['entity']
        stmt = sqlalchemy\
            .select(t_entity)\
            .where(t_entity.c.id == user_id)

        result = None
        async with self.db.async_engine.begin() as conn:
            cursor = await conn.execute(stmt)
            for row in cursor:
                result = row._asdict()
        if result is None:
            raise tornado.web.HTTPError(
                status_code=400, reason='entity id not in database')
        self.write(json.dumps(result))


class EntityUpdateHandler(tornado.web.RequestHandler):
    def initialize(self, db):
        self.db = db

    async def post(self):
        data = json.loads(self.request.body)
        id = data['id']

        result = {
            'status': 'success',
            'data': None
        }

        t_entity = self.db.metadata.tables['entity']

        stmt_check = sqlalchemy\
            .select(t_entity)\
            .where(t_entity.c.id == id)

        stmt_update = sqlalchemy\
            .update(t_entity)\
            .where(t_entity.c.id == id)\
            .values(
                carbon_offset=data['carbon_offset'],
                carbon_cost=data['carbon_cost']
            )

        async with self.db.async_engine.begin() as conn:
            has_row = False
            for _ in await conn.execute(stmt_check):
                has_row = True
            if not has_row:
                raise tornado.web.HTTPError(
                    status_code=400, reason='entity id not in database')
            await conn.execute(stmt_update)

        result['data'] = dict(id=id)
        self.write(json.dumps(result))


class EntityPurchasesGetHandler(tornado.web.RequestHandler):
    def initialize(self, db):
        self.db = db

    async def get(self, user_id):
        user_id = int(user_id)
        start_ts = datetime.datetime.fromtimestamp(
            float(self.get_argument('start_ts')))
        end_ts = datetime.datetime.fromtimestamp(
            float(self.get_argument('end_ts')))

        result = {
            "user_id": user_id,
            "purchase_list": []
        }

        t_purchase = self.db.metadata.tables['purchase']
        stmt = sqlalchemy\
            .select(t_purchase)\
            .where(
                t_purchase.c.buyr_id == user_id,
                t_purchase.c.ts > start_ts,
                t_purchase.c.ts < end_ts
            )
        async with self.db.async_engine.begin() as conn:
            cursor = await conn.execute(stmt)
            for row in cursor:
                row = row._asdict()
                row['ts'] = datetime.datetime.timestamp(row['ts'])
                result['purchase_list'].append(row)
        self.write(json.dumps(result))
