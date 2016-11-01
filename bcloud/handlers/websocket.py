# -*- coding:utf-8-*-

import paramiko
from tornado.websocket import WebSocketHandler

from plugins.log import logger


class BCloudSocketHandler(WebSocketHandler):
    waiters = set()
    cache = []
    cache_size = 200

    buf = ''

    _ssh = paramiko.SSHClient()
    _ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # tran = paramiko.Transport(('192.168.101.237', 22,))
    # tran.start_client()
    # tran.auth_password('barry', '123456')
    #
    # 打开一个通道
    # chan = tran.open_session()
    # 获取一个终端
    # chan.get_pty()
    # 激活器
    # chan.invoke_shell('xterm')

    def get_compression_options(self):
        return {}

    def open(self):
        print "链接成功"
        self._ssh.connect("192.168.101.237", 22, "barry", "123456", timeout=3)
        self.channel = self._ssh.invoke_shell('xterm')
        self.channel.setblocking(False)
        self.channel.settimeout(0.0)

    def on_close(self):
        pass

    @classmethod
    def update_cache(cls, chat):
        cls.cache.append(chat)
        if len(cls.cache) > cls.cache_size:
            cls.cache = cls.cache[-cls.cache_size:]

    @classmethod
    def send_updates(cls, chat):
        logger.info("sending message to %d waiters", len(cls.waiters))
        for waiter in cls.waiters:
            try:
                waiter.write_message(chat)
            except:
                logger.error("Error sending message", exc_info=True)

    def on_message(self, message):
        print repr(message)

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
