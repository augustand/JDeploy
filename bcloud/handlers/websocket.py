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
        self.ssh.connect(host, port, username, password, timeout=2)

        self.sshs.append((host, password, self.ssh))

    def e(self, cmd):
        try:
            for ip, password, ssh in self.sshs:
                _cmd = 'echo {} | sudo -S ls > /dev/null\n'.format(password) + cmd
                stdin, stdout, stderr = ssh.exec_command(_cmd, get_pty=True)
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

            rt = RemoteTask(self)
            rt.add_hosts(data.dict).e(task.replace("\r", ""))


class BCloudSocketHandler(BaseSockJSConnection):
    channel = None

    @event
    def open(self, request):
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
        channel.resize_pty(80, 30)
        channel.setblocking(False)
        channel.settimeout(0.0)

        self.channel = channel
        gevent.spawn(self._forward_outbound, self.channel).join()

        return "\r\n连接成功\r\n"

    @event
    def data(self, msg):
        self.channel.send(msg)
        gevent.spawn(self._forward_outbound, self.channel).join()

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

    def _forward_outbound(self, channel):

        while True:
            from gevent import select
            readable, writeable, error = select.select([channel, ], [], [], 0.1)
            if self.channel in readable:
                try:
                    x = self.channel.recv(1024)
                    if len(x) == 0:
                        break
                    self.emit("data", x)

                except socket.timeout as e:
                    print e.message
            else:
                break

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
