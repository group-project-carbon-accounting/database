import configparser
import logging
from types import SimpleNamespace
import tornado.ioloop
import tornado.web
import sqlalchemy
from handlers.entity import EntityGetHandler
from handlers.ping import PingHandler
from handlers.product import ProductAddHandler, ProductGetHandler, ProductUpdateHandler
from handlers.purchase import PurchaseGetHandler, PurchaseUpdateHandler, PurchaseAddHandler
from tornado.log import enable_pretty_logging
from sqlalchemy.ext.asyncio import create_async_engine


def initialise_database(config):
    mode = config['MODE']['mode']
    engine = sqlalchemy.create_engine(
        config[mode]['database_url'], echo=True, future=True)
    metadata = sqlalchemy.MetaData()
    sqlalchemy.Table(
        'entity', metadata, autoload=True, autoload_with=engine)
    sqlalchemy.Table(
        'product', metadata, autoload=True, autoload_with=engine)
    sqlalchemy.Table(
        'company_product', metadata, autoload=True, autoload_with=engine)
    sqlalchemy.Table(
        'purchase', metadata, autoload=True, autoload_with=engine)
    sqlalchemy.Table(
        'products_purchased', metadata, autoload=True, autoload_with=engine)
    async_engine = create_async_engine(
        config[mode]['database_url_async'], echo=True, future=True)
    return SimpleNamespace(engine=engine, async_engine=async_engine, metadata=metadata)


def make_app(config):
    mode = config['MODE']['mode']
    db = initialise_database(config)
    d = dict(db=db)

    return tornado.web.Application([
        (r'/ping', PingHandler),
        (r'/purchase/get/(?P<prch_id>[0-9]*)', PurchaseGetHandler, d),
        (r'/purchase/add', PurchaseAddHandler, d),
        (r'/purchase/update', PurchaseUpdateHandler, d),
        (r'/product/get/(?P<comp_id>[0-9]*)/(?P<prod_id>[0-9]*)',
         ProductGetHandler, d),
        (r'/product/add', ProductAddHandler, d),
        (r'/product/update', ProductUpdateHandler, d),
        (r'/entity/get/(?P<user_id>[0-9]*)', EntityGetHandler, d)
    ],
        debug=config[mode].getboolean('debug')
    )


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')

    logger = logging.getLogger('tornado.application')
    enable_pretty_logging()
    logger.addHandler(logging.StreamHandler())
    logger.addHandler(logging.FileHandler('database.log'))

    app = make_app(config)
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
