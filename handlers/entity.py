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

        async with self.db.async_engine.begin() as conn:
            cursor = await conn.execute(stmt)
            for row in cursor:
                result = row._asdict()

        self.write(json.dumps(result))
