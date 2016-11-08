# -*- coding:utf-8 -*-

import re
import sys
from os import listdir
from os.path import exists as path_exists, join as path_join, abspath, isdir


class singleton(object):
    """
        decorator: design patter - singleton
    """

    def __init__(self, cls):
        self.cls = cls
        self.inst = None

    def __call__(self, *args, **kwargs):
        if not self.inst: self.inst = self.cls(*args, **kwargs)
        return self.inst

    def __getattr__(self, name):
        return getattr(self.inst, name)


def read_all_text(path):
    """
        read all text from the file

        return: text or None
    """
    if not path_exists(path): return None
    with open(path, "r") as file: return file.read()


def subdirs(path):
    """
        get all the sub-directories

        return: [(basename, fullname), ...]
    """
    path = abspath(path)
    return filter(
        lambda (b, p): isdir(p),
        [(p, path_join(path, p)) for p in listdir(path) if "." not in p])


_PLATFORM = sys.platform


def check_ip(ip):
    pattern = re.compile(
        '^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')
    return True if pattern.match(ip) else False


def check_port(port):
    if port and port.isdigit():
        iport = int(port)
        return 0 < iport < 65536
    return False


class Platform(object):
    @staticmethod
    def detail():
        return _PLATFORM

    @staticmethod
    def is_win():
        return _PLATFORM.startswith('win')

    @staticmethod
    def is_linux():
        return _PLATFORM.startswith('linux')

    @staticmethod
    def is_mac():
        return _PLATFORM.startswith('darwin')
