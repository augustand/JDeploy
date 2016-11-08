# -*- coding:utf-8-*-


import json
import socket
from StringIO import StringIO

import gevent
import paramiko
import tablib
from paramiko import DSSKey
from paramiko import PasswordRequiredException
from paramiko import RSAKey
from paramiko import SSHException
from pony.orm import db_session, select
from tornado.escape import json_encode

from bcloud.handlers.sockjsExt import BaseSockJSConnection, event
from bcloud.model import Host, Project, Task


class RemoteTask(object):
    def __init__(self, ws):
        self.sshs = []
        self.ws = ws

    def add_hosts(self, hosts=[]):
        print hosts
        _s = [
            gevent.spawn(
                self.__add_hosts,
                h.get("ip"),
                int(h.get("port")),
                h.get("username"),
                h.get("password"),
            ) for h in hosts
            ]
        gevent.joinall(_s)
        return self

    def __add_hosts(self, host=None, port=None, username=None, password=None):

        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(host, port, username, password, timeout=3)

        # self.ssh.set_log_channel("jjjji")
        # self.ssh.get_transport()

        self.sshs.append((host, self.ssh))

    def e(self, cmd):
        try:
            for ip, ssh in self.sshs:
                stdin, stdout, stderr = ssh.exec_command(cmd)
                self.ws.emit("task_return", json_encode({
                    "name": ip,
                    "data": "error:\r\n" + stderr.read() + "\r\nstdout:\n" + stdout.read()
                }))

        except Exception, e:
            print e


class WSocketHandler(BaseSockJSConnection):
    @event
    def open(self, info):
        print info.path
        print info.path.split("/", 3)[1]

        print dir(info)
        print info.arguments
        print info.headers

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

    @event
    def task(self, msg):
        _d = json.loads(msg)
        print _d

        with db_session:
            data = tablib.Dataset(
                headers=["username", 'ip', 'port', "password", "id"]
            )
            hosts = select(
                (h.name, h.ip, h.port, h.password, h.id)
                for p in Project
                for h in Host
                if p.name == _d.get("project") and p.host_group == h.group
            )[:]
            map(data.append, hosts)

            task = select(
                t.content
                for t in Task
                if t.name == _d.get("task") and t.project == _d.get("project")
            ).first()

            print data.json

            rt = RemoteTask(self)
            rt.add_hosts(data.dict).e(task.replace("\r", ""))





            # a = select(
            #     h for h in Host for p in Project if h.group == p.host_group or h.name in p.host_names.split(","))
            # print a.show()
            # print list(a)


class BCloudSocketHandler(BaseSockJSConnection):
    channel = None

    @event
    def open(self, request):
        # self._ssh = paramiko.SSHCl ient()
        # self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print "open"
        _ssh = paramiko.SSHClient()
        _ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._ssh = _ssh

    def _load_private_key(self, private_key, passphrase=None):
        """ Load a SSH private key (DSA or RSA) from a string

        The private key may be encrypted. In that case, a passphrase
        must be supplied.
        """
        key = None
        last_exception = None
        for pkey_class in (RSAKey, DSSKey):
            try:
                key = pkey_class.from_private_key(StringIO(private_key),
                                                  passphrase)
            except PasswordRequiredException as e:
                # The key file is encrypted and no passphrase was provided.
                # There's no point to continue trying
                raise
            except SSHException as e:
                last_exception = e
                continue
            else:
                break
        if key is None and last_exception:
            raise last_exception
        return key

    @event
    def close(self):
        """ Terminate a bridge session """

        print "close\n\n"
        self._ssh.close()
        self.channel.close()

    @event
    def conn(self, msg):
        print msg

        data = json.loads(msg)
        self._ssh.connect(
            hostname=data.get("hostname", ""),
            port=int(data.get("port", "")),
            username=data.get("username", ""),
            password=data.get("password", ""),
            pkey=None,
            timeout=None,
            allow_agent=None,
            look_for_keys=False
        )

        channel = self._ssh.invoke_shell('xterm')
        channel.resize_pty(80, 60)
        channel.setblocking(False)
        channel.settimeout(0.0)

        channel.send("\r\n")

        self.channel = channel
        gevent.spawn(self._forward_outbound, self.channel).start()

    @event
    def data(self, msg):

        data = json.loads(str(msg))
        if 'data' in data:
            _d = data['data']
            self.channel.send(_d)
            gevent.spawn(self._forward_outbound, self.channel).join()

            # gevent.spawn(self._forward_outbound, self.channel).join()

            # print data['data']

            # print self.channel.send_ready()
            # print self.channel.fileno()
            # print self.channel.recv_ready()
            # print self.channel.exit_status_ready()

            # while self.channel.recv_ready():
            #     a = self.channel.recv(1024)
            #     self._a += a
            #     # self.emit("data", self._a)
            #     # print a
            #     # print self.channel.recv_ready(), '\n\n'
            # else:
            #     a = self.channel.recv(1024)
            #     self._a += a
            #     print repr(self._a)
            #
            #     # if self._a == "\r\n":
            #     #     self.channel.send(data['data'])
            #     # self.emit("data", self._a)
            #     # self.emit("data", self._a)
            #
            #     self.emit("data", self._a)
            #     self._a = ''
            # print a
            # print self.channel.recv_ready(), '\n\n'

    def execute(self, command, term='xterm'):
        """ Execute a command on the remote server

        This method will forward traffic from the websocket to the SSH server
        and the other way around.

        You must connect to a SSH server using ssh_connect()
        prior to starting the session.
        """
        transport = self._ssh.get_transport()
        channel = transport.open_session()
        channel.get_pty(term)
        channel.exec_command(command)
        self._bridge(channel)
        channel.close()

    def shell(self, term='xterm'):
        """ Start an interactive shell session

        This method invokes a shell on the remote SSH server and proxies
        traffic to/from both peers.

        You must connect to a SSH server using ssh_connect()
        prior to starting the session.
        """
        self.channel = self._ssh.invoke_shell(term)
        self._bridge(self.channel)
        self.channel.close()

    def _bridge(self, channel):
        """ Full-duplex bridge between a websocket and a SSH channel """
        channel.setblocking(False)
        channel.settimeout(0.0)
        gevent.spawn(self._forward_outbound, channel)

        # self.channel

    def _forward_inbound(self, channel):
        """ Forward inbound traffic (websockets -> ssh) """
        try:
            while not self.tasks.empty():
                task = self.tasks.get()
                gevent.sleep(0)
                channel.send(task)
        finally:
            self.close()

    def _forward_outbound(self, channel):

        while True:
            from gevent import select
            readable, writeable, error = select.select([channel, ], [], [], 0)
            if self.channel in readable:
                try:
                    x = self.channel.recv(1024)
                    print repr(x)
                    if len(x) == 0:
                        print('\r\n*** EOF\r\n')
                        break
                    self.emit("data", x)

                except socket.timeout as e:
                    print e.message
            else:
                print "接收完毕"
                break


                # self.close()

        """ Forward outbound traffic (ssh -> websockets) """

        # while True:
        #     from gevent import select
        #
        #     print channel
        #     readable, writeable, error = select.select([channel], [], [], 1)
        #
        #     print channel
        #
        #     if channel in readable:
        #         try:
        #             from paramiko.py3compat import u
        #             x = u(channel.recv(1024))
        #             if len(x) == 0:
        #                 print('\r\n*** EOF\r\n')
        #                 break
        #             self.emit("data", x)
        #         except socket.timeout:
        #             print "timeout"
        #             # if sys.stdin in readable:
        #             #     inp = sys.stdin.readline()
        #             #     chan.sendall(inp)
        # data = ''
        # try:
        #     while True:
        #         print channel
        #         print channel.in_buffer
        #         print channel.in_buffer._buffer
        #         print "recv_ready", channel.recv_ready()
        #
        #         # if not channel.recv_ready():
        #         #     raise
        #
        #         # data = channel.recv(1024)
        #         wait_read(channel.fileno())
        #         data = channel.recv(1024)
        #         # data = channel.in_buffer.read(1024, 0)
        #         print "recv success----------"
        #         self.send("data," + data)
        #
        #         # if not channel.recv_ready():
        #         #     break
        #
        #         # self.emit("data", data)
        # except Exception as e:
        #     print 'error', e.message, '\n\n'
        #     # self._forward_outbound(self.channel)
        #     # self._forward_outbound(self.channel)
        #     # gevent.spawn(self._forward_outbound, self.channel).start()
        # finally:
        #     print repr(data)
        #     print "recv ok\n\n"

    def open_ws(self,
                hostname,
                port=22,
                username=None,
                password=None,
                private_key=None,
                key_passphrase=None,
                allow_agent=False,
                timeout=None):
        """ Open a connection to a remote SSH server

        In order to connect, either one of these credentials must be
        supplied:
            * Password
                Password-based authentication
            * Private Key
                Authenticate using SSH Keys.
                If the private key is encrypted, it will attempt to
                load it using the passphrase
            * Agent
                Authenticate using the *local* SSH agent. This is the
                one running alongside wsshd on the server side.
        """
        try:
            pkey = None
            if private_key:
                pkey = self._load_private_key(private_key, key_passphrase)
            self._ssh.connect(
                hostname=hostname,
                port=port,
                username=username,
                password=password,
                pkey=pkey,
                timeout=timeout,
                allow_agent=allow_agent,
                look_for_keys=False)

            # print self._ssh
        except socket.gaierror as e:
            self.emit("error", 'Could not resolve hostname {0}: {1}'.format(
                hostname, e.args[1]))
            raise
        except Exception as e:
            self.emit("error", e.message or str(e))
            raise
