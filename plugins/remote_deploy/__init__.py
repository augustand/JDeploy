# -*- coding:utf-8-*-

ips = ['192.168.101.237']

import paramiko


def ssh_cmd(ip, port, cmd, user, passwd):
    try:
        ssh = paramiko.SSHClient()

        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh.connect(ip, port, user, passwd, timeout=3)

        stdin, stdout, stderr = ssh.exec_command(cmd)

        print stderr.read()
        print stdout.read()

        ssh.close()

    except:

        print("ssh_cmd err.")


if __name__ == '__main__':
    ssh_cmd(
        "192.168.101.237",
        22,
        '''
        echo 123456 | sudo -S ls > /dev/null
        sudo ls
        sudo ls
        ''',
        'barry',
        '123456'
    )
