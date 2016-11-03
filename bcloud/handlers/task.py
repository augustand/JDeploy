# -*- coding:utf-8 -*-
import uuid

import tablib
from pony.orm import db_session, select, commit
from tornado import web

from bcloud.model import Task

'''
pwd;

echo 123456 | sudo -S ls > /dev/null

sudo ls



sudo ls -al


ls /;
rm -rf fabric;
rm -rf fabricd;
rm -rf tests;
ls

pwd;
sudo touch kkkk;
ls | grep kkkk;

# sudo -k

echo 123456 | sudo -S ls > /dev/null

sudo ps
'''


class TaskHandler(web.RequestHandler):
    def _data(self, __data):
        __d = {}
        for _d in __data:
            _n = _d["project"]
            if not __d.get(_n):
                __d[_n] = (_d,)
            else:
                __d[_n] += (_d,)

            del _d["project"]

        return __d.items()

    def get(self, *args):

        data_type = self.get_argument("type", "")

        if args:
            _id = args[0]
            with db_session:
                t = Task[_id]
                self.write({
                    "id": t.id,
                    "name": t.name,
                    "content": t.content,
                    "project": t.project,
                })
        else:
            with db_session:
                data = tablib.Dataset(
                    headers=["id", "name", "content", "project"]
                )
                map(data.append, select((t.id, t.name, t.content, t.project) for t in Task)[:])

                print data.dict

                if data_type == "json":
                    self.write(data.json)
                else:
                    data = self._data(data.dict)
                    self.render("task/index.html", tasks=data)

    @web.asynchronous
    def post(self):
        _name = self.get_body_argument("name", "")
        _content = self.get_body_argument("content", "")

        _content = _content.strip()

        _project = self.get_body_argument("project", "")

        print _content
        print repr(_content)

        with db_session:
            Task(
                id=str(uuid.uuid4()),
                name=_name,
                content=_content,
                project=_project,
                group="host",
            )
            commit()
            self.redirect("/task")
        self.finish()

    def delete(self, _id):
        with db_session:
            Task[_id].delete()

        self.write("ok")
        # self.write(json_encode({"result": "ok"}))

    @web.asynchronous
    def put(self, _id):
        print _id
        with db_session:
            t = Task.get(id=_id)
            Task(
                id=str(uuid.uuid4()),
                name=t.name,
                content=t.content,
                project=t.project,
            )
            commit()
            self.write("ok")

        self.finish()

    def patch(self, _id):
        _name = self.get_argument("name", "")
        _content = self.get_argument("content", "")
        _project = self.get_argument("project", "")

        with db_session:
            task = Task.get(id=_id)
            task.name = _name
            task.content = _content
            task.project = _project
            commit()

        self.write("ok")


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
