import configparser
import logging
import tornado.ioloop
import tornado.web
import sqlalchemy
from handlers.ping import PingHandler
from handlers.purchase_info import PurchaseUpdateHandler, PurchaseAddHandler
from tornado.log import enable_pretty_logging


def initialise_database(config):
    mode = config['MODE']['mode']
    engine = sqlalchemy.create_engine(
        config[mode]['database_url'], echo=True, future=True)
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
    return config, metadata


def make_app(config):
    mode = config['MODE']['mode']
    config, metadata = initialise_database(config)
    return tornado.web.Application([
        (r'/ping', PingHandler),
        (r'/purchase/update', PurchaseUpdateHandler,
         dict(config=config, metadata=metadata)),
        (r'/purchase/add', PurchaseAddHandler,
         dict(config=config, metadata=metadata)),
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
