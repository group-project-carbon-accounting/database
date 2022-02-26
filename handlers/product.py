from re import S
import tornado.web
import json
import sqlalchemy


class ProductCompanyGetHandler(tornado.web.RequestHandler):
    def initialize(self, db):
        self.db = db

    async def get(self, comp_id, prod_id):
        comp_id, prod_id = map(int, (comp_id, prod_id))
        """
        Return all product details as in 
        {
            comp_id: 1,
            prod_id: 2,
            carbon_cost: 3
        }
        """
        t_product = self.db.metadata.tables['product']
        t_company_product = self.db.metadata.tables['company_product']
        stmt = sqlalchemy\
            .select(t_company_product)\
            .where(
                t_company_product.c.comp_id == comp_id,
                t_company_product.c.prod_id == prod_id
            )

        result = None
        async with self.db.async_engine.begin() as conn:
            cursor = await conn.execute(stmt)
            for row in cursor:
                result = row._asdict()
        if result is None:
            raise tornado.web.HTTPError(
                status_code=400, reason='comp_id, prod_id not in database')
        self.write(json.dumps(result))


class ProductGetHandler(tornado.web.RequestHandler):
    def initialize(self, db):
        self.db = db

    async def get(self, prod_id):
        prod_id = int(prod_id)
        t_product = self.db.metadata.tables['product']
        stmt = sqlalchemy\
            .select(t_product)\
            .where(t_product.c.id == prod_id)
        result = None
        async with self.db.async_engine.begin() as conn:
            for row in await conn.execute(stmt):
                result = row._asdict()
        if result is None:
            raise tornado.web.HTTPError(
                status_code=400, reason='product id not in database')
        self.write(json.dumps(result))


class ProductAddHandler(tornado.web.RequestHandler):
    def initialize(self, db):
        self.db = db

    async def post(self):
        """
        Add to company_product table
        """
        data = json.loads(self.request.body)
        result = {
            'status': 'success',
        }
        t_company_product = self.db.metadata.tables['company_product']

        stmt = sqlalchemy\
            .insert(t_company_product)\
            .values(
                comp_id=data['comp_id'],
                prod_id=data['prod_id'],
                carbon_cost=data['carbon_cost']
            )
        async with self.db.async_engine.begin() as conn:
            await conn.execute(stmt)

        self.write(json.dumps(result))


class ProductUpdateHandler(tornado.web.RequestHandler):
    def initialize(self, db):
        self.db = db

    async def post(self):
        """
        If prod_id is None, update entity table
        Else if comp_id is None, update product table
        Else, update company_product table
        """
        data = json.loads(self.request.body)
        result = {
            'status': 'success',
        }
        t_product = self.db.metadata.tables['product']
        t_entity = self.db.metadata.tables['entity']
        t_company_product = self.db.metadata.tables['company_product']

        if data['prod_id'] is None:
            stmt = sqlalchemy\
                .update(t_entity)\
                .where(t_entity.c.id == data['comp_id'])\
                .values(carbon_cost=data['carbon_cost'])
        elif data['comp_id'] is None:
            stmt = sqlalchemy\
                .update(t_product)\
                .where(t_product.c.id == data['prod_id'])\
                .values(carbon_cost=data['carbon_cost'])
        else:
            stmt = sqlalchemy\
                .update(t_company_product)\
                .where(
                    t_company_product.c.comp_id == data['comp_id'],
                    t_company_product.c.prod_id == data['prod_id']
                )\
                .values(carbon_cost=data['carbon_cost'])

        async with self.db.async_engine.begin() as conn:
            await conn.execute(stmt)

        self.write(json.dumps(result))
