# -*- coding:utf-8 -*-
import uuid

import tablib
from pony.orm import db_session, commit, select
from tornado import web

from bcloud.model import Host


class DockerHandle(web.RequestHandler):
    def get(self, *args, **kwargs):
        self.render("docker/index.html")


class HostsHandler(web.RequestHandler):
    def _data(self, __data):
        __d = {}
        for _d in __data:
            _n = _d["group"]
            if not __d.get(_n):
                __d[_n] = (_d,)
            else:
                __d[_n] += (_d,)

            del _d["group"]

        return __d.items()

    def get(self):
        # print self.application.handlers

        data_type = self.get_argument("data_type", "")
        with db_session:
            data = tablib.Dataset(
                headers=["name", 'ip', 'port', "id", "group"]
            )
            s = select((h.name, h.ip, h.port, h.id, h.group) for h in Host)[:]
            map(data.append, s)

            if data_type == "json":
                self.write(data.json)
            else:
                data = self._data(data.dict)
                self.render("host/index.html", hosts=data)

    @web.asynchronous
    def post(self):

        name = self.get_body_argument("name", "")
        ip = self.get_body_argument("ip", "")
        password = self.get_body_argument("password", "")
        port = self.get_body_argument("port", "")
        group = self.get_body_argument("group", "")

        with db_session:
            a = Host(
                id=str(uuid.uuid4()),
                name=name,
                ip=ip,
                port=int(port),
                password=password,
                group=group
            )
            commit()
            self.redirect("/host")
        return

    @web.asynchronous
    def delete(self):
        ids = self.get_argument("ids", "")
        with db_session:
            [Host[_id].delete() for _id in ids.strip(",")]
            self.write("success")
        return


class HostHandler(web.RequestHandler):
    def _data(self, __data):
        __d = {}
        for _d in __data:
            _n = _d["group"]
            if not __d.get(_n):
                __d[_n] = (_d,)
            else:
                __d[_n] += (_d,)

            del _d["group"]

        return __d.items()

    def get(self, hid=None):

        with db_session:
            h = Host[hid]
            self.write({
                "id": h.id,
                "name": h.name,
                "ip": h.ip,
                "port": h.port,
                "group": h.group,
                "password": h.password,
            })

    def patch(self, hid=None):
        _name = self.get_argument("name", "")
        _ip = self.get_argument("ip", "")
        _password = self.get_argument("password", "")
        _port = self.get_argument("port", "")
        _group = self.get_argument("group", "")

        with db_session:
            host = Host.get(id=hid)
            host.name = _name
            host.ip = _ip
            host.password = _password
            host.port = _port
            host.group = _group
            commit()
        # self.write(json_encode({"result": "ok"}))

        self.write("Ok")

        # self.redirect("/host")

    @web.asynchronous
    def put(self, hid=None):
        with db_session:
            host = Host.get(id=hid)
            Host(
                id=str(uuid.uuid4()),
                name=host.name,
                ip=host.ip,
                port=host.port,
                password=host.password,
                group=host.group
            )
            commit()

            self.write("ok")

        self.finish()

    def delete(self, hid=None):
        with db_session:
            Host[hid].delete()
            return self.write("success")


if __name__ == '__main__':
    with db_session:

        data = tablib.Dataset(
            headers=["name", 'ip', 'id']
        )

        s = select((h.name, h.ip, h.id) for h in Host)[:]
        map(data.append, s)
        print data.json

        for h in select(h for h in Host):
            print h.name
            print h.id
