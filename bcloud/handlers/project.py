# -*- coding:utf-8 -*-
import uuid

import tablib
from pony.orm import db_session, select, commit
from tornado import web

from bcloud.model import Project


class ProjectHandler(web.RequestHandler):
    def get(self, *args):

        data_type = self.get_argument("data_type", "")

        if args:
            _id = args[0]

            with db_session:
                p = Project.get(id=_id)
                if data_type == "json":
                    self.write({
                        "id": p.id,
                        "name": p.name,
                        "description": p.description,
                        "host_names": p.host_names,
                        "tasks": p.tasks,
                        "host_group": p.host_group,
                    })
                else:
                    self.render("project/project.html", project=p)

        else:
            with db_session:
                data = tablib.Dataset(
                    headers=["name", "id", 'host_group']
                )
                s = select((h.name, h.id, h.host_group) for h in Project)[:]
                map(data.append, s)

                # print data.dict

                if data_type == "json":
                    self.write(data.json)
                else:
                    self.render("project/index.html", projects=data.dict)

    @web.asynchronous
    def patch(self, _id):
        _name = self.get_argument("name", "")
        _sub_name = self.get_argument("sub_name", "")
        _host_group = self.get_argument("host_group", "")
        _host_names = self.get_argument("host_names", "")
        _description = self.get_argument("description", "")
        _tasks = self.get_argument("tasks", "")

        with db_session:
            p = Project.get(id=_id)
            p.name = _name
            p.host_group = _host_group
            p.description = _description
            p.sub_name = _sub_name
            p.host_names = _host_names
            p.tasks = _tasks
            commit()
            # self.write(json_encode({"result": "ok"}))
            self.write("ok")
        self.finish()

    @web.asynchronous
    def delete(self, _id):
        with db_session:
            Project[_id].delete()

        self.write("ok")
        self.finish()

    @web.asynchronous
    def post(self):
        name = self.get_body_argument("name", "")
        host_group = self.get_body_argument("host_group", "")
        description = self.get_body_argument("description", "")
        host_names = self.get_body_argument("host_names", "")
        tasks = self.get_body_argument("tasks", "")

        with db_session:
            a = Project(
                id=str(uuid.uuid4()),
                name=name,
                host_group=host_group,
                description=description,
                host_names=host_names,
                tasks=tasks,
            )
            commit()
            self.redirect("/project/{}".format(a.id))

        self.finish()

    @web.asynchronous
    def put(self, _id):
        print _id
        with db_session:
            t = Project.get(id=_id)
            Project(
                id=str(uuid.uuid4()),
                name=t.name,
                host_group=t.host_group,
                description=t.description,
                host_names=t.host_names,
                tasks=t.tasks,
            )
            commit()
            self.write("ok")

        self.finish()


if __name__ == '__main__':
    with db_session:

        data = tablib.Dataset(
            headers=["name", 'ip', 'id']
        )

        s = select((h.name, h.ip, h.id) for h in Project)[:]
        map(data.append, s)
        print data.json

        for h in select(h for h in Project):
            print h.name
            print h.id
