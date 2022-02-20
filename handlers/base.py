from types import SimpleNamespace
import tornado
from sqlalchemy.ext.asyncio import create_async_engine


class BaseHandler(tornado.web.RequestHandler):
    def initialize(self, config, metadata):
        mode = config['MODE']['mode']
        async_engine = create_async_engine(
            config[mode]['database_url_async'], echo=True, future=True)
        self.db = SimpleNamespace(
            config=config, async_engine=async_engine, metadata=metadata)
