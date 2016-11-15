# -*- coding:utf-8 -*-

from pony.orm import Required, PrimaryKey, Optional

from plugins.db import db


class Host(db.Entity):
    _table_ = 'Host'

    id = PrimaryKey(str)
    name = Required(str)
    ip = Required(str)
    port = Required(int, default=22)
    password = Required(str, default='123456')
    group = Required(str, default='test')


class Project(db.Entity):
    _table_ = 'Project'

    id = PrimaryKey(str)
    name = Required(str, unique=True)
    sub_name = Optional(str)
    description = Optional(str)
    host_group = Optional(str)
    host_names = Optional(str)
    tasks = Optional(str)


class Task(db.Entity):
    _table_ = 'Task'

    id = PrimaryKey(str)
    name = Required(str)
    content = Optional(str)
    project = Optional(str)
    group = Required(str)


db.generate_mapping(create_tables=True)

