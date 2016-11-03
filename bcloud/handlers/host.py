# -*- coding:utf-8 -*-
import uuid

import tablib
from pony.orm import db_session, commit, select
from tornado import web

from bcloud.model import Host


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

    def get(self, *args):

        data_type = self.get_argument("type", "")

        if args:
            _id = args[0]
            if _id == 'env':
                self.render("host/env.html")
            else:
                with db_session:
                    h = Host[_id]
                    self.write({
                        "id": h.id,
                        "name": h.name,
                        "ip": h.ip,
                        "port": h.port,
                        "group": h.group,
                        "password": h.password,
                    })
        else:
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
                    self.render("host/index.html", hosts=data, hostss=data)

    def patch(self, _id):
        _name = self.get_argument("name", "")
        _ip = self.get_argument("ip", "")
        _password = self.get_argument("password", "")
        _port = self.get_argument("port", "")
        _group = self.get_argument("group", "")

        with db_session:
            host = Host.get(id=_id)
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
    def put(self, _id):
        with db_session:
            host = Host.get(id=_id)
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

            # data = tablib.Dataset(
            #     headers=["name", 'ip', 'id']
            # )
            # map(data.append, select((h.name, h.ip, h.id) for h in Host)[:])
            # self.write(data.json)
            self.redirect("/host")

        self.finish()

    def delete(self, _id=None):

        if _id:
            with db_session:
                Host[_id].delete()
                return self.write("success")

        return self.write("fail")


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
