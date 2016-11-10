# -*- coding:utf-8-*-
import json

import docker

if __name__ == '__main__':
    c = docker.Client(base_url='localhost:2375')
    print json.dumps(c.images())
    print c.containers()
    print c.services()
    print c.nodes()
