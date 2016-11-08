# -*- coding:utf-8 -*-
import uuid

import tablib
from pony.orm import db_session, select, commit
from tornado import web

from bcloud.model import Project, Task, Host


class ProjectsHandler(web.RequestHandler):
    def get(self):

        data_type = self.get_argument("data_type", "")
        with db_session:
            data = tablib.Dataset(
                headers=["name", "id", 'description']
            )
            s = select((h.name, h.id, h.description) for h in Project)[:]
            print s.show()
            map(data.append, s)

            if data_type == "json":
                self.write(data.json)
            else:
                self.render("project/index.html", projects=data.dict)

    @web.asynchronous
    def delete(self):
        ids = self.get_argument("ids", "")
        with db_session:
            [Project[_id].delete() for _id in ids.strip(",")]
            self.write("ok")
        self.finish()

    @web.asynchronous
    def post(self):
        name = self.get_body_argument("name", "")
        host_group = self.get_body_argument("host_group", "")
        description = self.get_body_argument("description", "")
        host_names = self.get_body_argument("host_names", "")

        with db_session:
            if host_group:
                h = select(h for h in Host if h.group == host_group).first()
                if not h:
                    self.render("error.html", message="host_group:{}不正确".format(host_group))
                    return

            if host_names:
                h = select(h for h in Host if h.name in host_names.strip().split(",")).first()
                if not h:
                    self.render("error.html", message="host_names:{}不正确".format(host_names))
                    return

            a = Project(
                id=str(uuid.uuid4()),
                name=name,
                host_group=host_group,
                description=description,
                host_names=host_names,
            )
            commit()
            self.redirect("/project/{}".format(a.id))

        self.finish()


class ProjectHandler(web.RequestHandler):
    def get(self, pid=None):

        data_type = self.get_argument("data_type", "")
        with db_session:
            p = Project.get(id=pid)
            tasks = select(t.name for t in Task if t.project == p.name)[:]
            p.tasks = ",".join(tasks)

            if data_type == "json":
                self.write({
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "host_names": p.host_names,
                    "host_group": p.host_group,
                    "tasks": p.tasks
                })
            else:
                self.render("project/project.html", project=p)

    @web.asynchronous
    def patch(self, pid=None):
        _name = self.get_argument("name", "")
        _sub_name = self.get_argument("sub_name", "")
        _host_group = self.get_argument("host_group", "")
        _host_names = self.get_argument("host_names", "")
        _description = self.get_argument("description", "")

        with db_session:
            p = Project.get(id=pid)
            p.name = _name
            p.host_group = _host_group
            p.description = _description
            p.sub_name = _sub_name
            p.host_names = _host_names
            commit()
            # self.write(json_encode({"result": "ok"}))
            self.write("ok")
        self.finish()

    @web.asynchronous
    def delete(self, pid=None):
        with db_session:
            Project[pid].delete()

        self.write("ok")
        self.finish()

    @web.asynchronous
    def put(self, pid=None):
        with db_session:
            t = Project.get(id=pid)
            Project(
                id=str(uuid.uuid4()),
                name=t.name,
                host_group=t.host_group,
                description=t.description,
                host_names=t.host_names,
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
