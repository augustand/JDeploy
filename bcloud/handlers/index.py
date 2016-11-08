# coding:utf-8
# -*- coding:utf-8 -*-

import tornado.gen
import tornado.web
from pony.orm import db_session
from tornado.escape import json_encode

from bcloud.model import Host


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("homepage.html")

    @tornado.web.asynchronous
    def post(self):
        name = self.get_secure_cookie('name')
        msg = self.get_argument('msg', '')

        if name == '':
            name = 'Anonymous'

        print name, msg

        data = json_encode({'name': name, 'msg': msg})
        self.write(json_encode({'result': True}))
        self.finish()


class TermHandler(tornado.web.RequestHandler):
    def get(self, tid=None):
        with db_session:
            h = Host[tid]
            print h
            self.render("term/index.html", h=h)
