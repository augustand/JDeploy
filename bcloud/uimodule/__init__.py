# -*- coding:utf-8 -*-
import tablib
from pony.orm import db_session, select
from tornado import web

from bcloud.model import Project


class EntryModule(web.UIModule):
    def render(self, entry):
        return self.render_string("modules/entry.html", entry=entry)


class SidebarModule(web.UIModule):
    def render(self):
        with db_session:
            data = tablib.Dataset(headers=["name", "id", 'host_group'])
            s = select((h.name, h.id, h.host_group) for h in Project)[:]
            map(data.append, s)
            return self.render_string("modules/sidebar.html", names=data.dict)

    def css_files(self):
        return "modules/sidebar/index.css"

    def javascript_files(self):
        return "modules/sidebar/index.js"


class MenubarModule(web.UIModule):
    def render(self):
        _data = [
            {"name": "Home", "url": "/"},
            {"name": "Project", "url": "/project"},
            {"name": "Host", "url": "/host"},
            {"name": "Env", "url": "/host/env"},
            {"name": "Task", "url": "/task"},
        ]

        return self.render_string("modules/menubar.html", menus=_data)

    def css_files(self):
        return "modules/menubar/index.css"


class FooterModule(web.UIModule):
    def render(self):
        return self.render_string("modules/footer.html")

    def css_files(self):
        return "modules/footer/index.css"


class EntryModule1(web.UIModule):
    def render(self, entry, show_comments=False):
        if show_comments:
            self.show_comments = True
        else:
            self.show_count = True
        return self.render_string("modules/entry.html", entry=entry,
                                  show_comments=show_comments)

    def embedded_javascript(self):
        if getattr(self, "show_count", False):
            return self.render_string("disquscount.js")
        return None

    def javascript_files(self):
        if getattr(self, "show_comments", False):
            return ["http://disqus.com/forums/brettaylor/embed.js"]
        return None
