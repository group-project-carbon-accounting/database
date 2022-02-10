import tornado


class PingHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("pong!")
