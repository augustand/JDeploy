# coding:utf-8
import os
import traceback

from tornado import web
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.options import define, parse_command_line
from tornado.web import TemplateModule

from bcloud.handlers.index import TermHandler
from bcloud.handlers.task import TaskHandler, TasksHandler
from bcloud.uimodule import EntryModule, SidebarModule, MenubarModule, FooterModule
from plugins.config import config
from plugins.db import db

define("port", default=8888, help="run on the given port", type=int)
define("mysql_host", default="127.0.0.1:3306", help="blog database host")
define("mysql_database", default="blog", help="blog database name")
define("mysql_user", default="blog", help="blog database user")
define("mysql_password", default="blog", help="blog database password")


class Application(web.Application):
    def __init__(self):
        self.db = db
        self.config = config

        from bcloud.handlers.host import HostHandler, HostsHandler
        from bcloud.handlers.index import MainHandler

        from bcloud.handlers.websocket import BCloudSocketHandler
        from bcloud.handlers.project import ProjectHandler

        from bcloud.handlers.websocket import WSocketHandler
        from sockjs.tornado import SockJSRouter

        from bcloud.handlers.project import ProjectsHandler
        handlers = [
            (r"/", MainHandler),
            (r"/term1/(?P<tid>.*)", TermHandler),
            (r"/host", HostsHandler),
            (r"/host/(?P<hid>.*)", HostHandler),
            (r"/project", ProjectsHandler),
            (r"/project/(?P<pid>.*)", ProjectHandler),
            (r"/task", TasksHandler),
            (r"/task/(?P<tid>.*)", TaskHandler),
        ]
        handlers += SockJSRouter(WSocketHandler, '/ws').urls
        handlers += SockJSRouter(BCloudSocketHandler, '/term').urls

        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            ui_modules={
                "Entry": EntryModule,
                "Sidebar": SidebarModule,
                "Menubar": MenubarModule,
                "Footer": FooterModule,
                'include': TemplateModule,
            },
            xsrf_cookies=False,
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            # login_url="/auth/login",
            debug=True,
        )
        super(Application, self).__init__(handlers, **settings)


if __name__ == "__main__":
    parse_command_line()

    app = Application()
    # wsgi_app = wsgi.WSGIAdapter(app)

    loop = IOLoop.instance()

    print "http://{}:{}".format("localhost", 8888)

    HTTPServer(app).listen(8888)
    try:
        # server = gevent.wsgi.WSGIServer(('', 8888), wsgi_app, debug=True)
        # server.serve_forever()
        # loop.add_callback(webbrowser.open, url)
        loop.start()
    except KeyboardInterrupt:
        print(" Shutting down on SIGINT!")
        loop.stop()
        traceback.format_exc()
    finally:
        pass


# loop.close()
# IOLoop.current().start()
# IOLoop.current().start()
