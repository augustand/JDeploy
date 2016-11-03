# -*- coding:utf-8-*-

import paramiko
from tornado.escape import json_encode
from tornado.websocket import WebSocketHandler

from bcloud.handlers.sockjsExt import BaseSockJSConnection, event


class WSocketHandler(BaseSockJSConnection):
    @event
    def open(self, info):
        print info.path
        print info.path.split("/", 3)[1]

        print self._events

    @event
    def close(self):
        print self._events
        print "close"

    @event
    def hello(self, msg):
        self.emit("hello", "kokokok")
        print msg
        return msg

    @event
    def echo(self, msg):
        print msg


class BCloudSocketHandler(WebSocketHandler):
    waiters = set()
    cache = []
    cache_size = 200

    buf = ''

    _ssh = paramiko.SSHClient()
    _ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def get_compression_options(self):
        return {}

    def open(self):
        print "链接成功"
        self._ssh.connect("192.168.101.237", 22, "barry", "123456", timeout=3)
        self.channel = self._ssh.invoke_shell('xterm')
        self.channel.setblocking(False)
        self.channel.settimeout(0.0)

        self.write_message("client open ok....")

    def on_close(self):
        pass

    def hello(self):
        pass

    def on_message(self, message):
        print message

        name = message.get("name", "")

        if not name:
            self.write_message(json_encode({
                "name": "error",
                "data": {
                    "msg": "name is null"
                }
            }))
        else:
            print self.__dict__
            data = message.get("data", "")

        if message == u'0\r':
            print "sent"

            # stdin, stdout, stderr = self._ssh.exec_command("ls")
            print self.buf
            stdin, stdout, stderr = self._ssh.exec_command(self.buf)

            o = stdout.read()
            r = stderr.read()
            print r
            print o
            print repr(o).encode()
            ''.decode()

            o = o.replace('\n', '\r\n')

            self.write_message("0\r\n" + o + "\r\nbash>>$")
            self.buf = ''
        else:
            self.buf += message[1:]
            print self.buf
            self.write_message(message)

            # 监视用户输入和服务器返回数据
            # sys.stdin 处理用户输入
            # chan 是之前创建的通道，用于接收服务器返回信息
