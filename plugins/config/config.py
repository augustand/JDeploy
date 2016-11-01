# -*- coding:utf-8 -*-


from os.path import join as pathjoin, dirname

import settings

BASEPATH = dirname(dirname(dirname(__file__)))

DBFILE = pathjoin(BASEPATH, "files", "bcloud.db")

if __name__ == '__main__':
    print BASEPATH


def get_settings(name, default=None):
    return settings.__dict__.get(name, default)





def deco(f):
    a = 0
    f("hhhh")
    print "deco"


def deco1(f):
    def hh(*k, **kk):
        f("kk")
        print k, kk

    return hh


@deco1
def hello(hh='123'):
    b = 0
    print "hello"
    print hh


print [x for x in [1,2,3]]

if __name__ == '__main__':
    hello()
    # deco(hello)
    # deco1(hello)
