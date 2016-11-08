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


class TasksHandler(web.RequestHandler):
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

    def get(self):

        data_type = self.get_argument("type", "")
        with db_session:
            data = tablib.Dataset(
                headers=["id", "name", "content", "project"]
            )
            map(data.append, select((t.id, t.name, t.content, t.project) for t in Task)[:])

            if data_type == "json":
                self.write(data.json)
            else:
                data = self._data(data.dict)
                self.render("task/index.html", tasks=data)

    @web.asynchronous
    def post(self):
        _name = self.get_body_argument("name", "")
        _content = self.get_body_argument("content", "")
        _project = self.get_body_argument("project", "")

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

    def delete(self):
        ids = self.get_argument("ids", "")
        with db_session:
            [Task[_id].delete() for _id in ids.strip(",")]
            self.write("ok")
            # self.write(json_encode({"result": "ok"}))


class TaskHandler(web.RequestHandler):
    def get(self, tid=None):
        data_type = self.get_argument("data_type", "")
        with db_session:
            t = Task[tid]
            self.write({
                "id": t.id,
                "name": t.name,
                "content": t.content,
                "project": t.project,
            })

    def delete(self, tid=None):
        with db_session:
            Task[tid].delete()
            self.write("ok")
            # self.write(json_encode({"result": "ok"}))

    @web.asynchronous
    def put(self, tid=None):
        with db_session:
            t = Task.get(id=tid)
            Task(
                id=str(uuid.uuid4()),
                name=t.name,
                content=t.content,
                project=t.project,
                group="host",
            )
            commit()
            self.write("ok")

        self.finish()

    def patch(self, tid=None):
        _name = self.get_argument("name", "")
        _content = self.get_argument("content", "")
        _project = self.get_argument("project", "")

        with db_session:
            task = Task.get(id=tid)
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
