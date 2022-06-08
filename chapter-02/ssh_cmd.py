#!/usr/bin/env python
import paramiko

#SSHサーバーへの接続を行い、単一のコマンドを実行する
def ssh_command(ip, port, user, passwd, cmd):
    client = paramiko.SSHClient()
    #接続先のSSHサーバーのSSH鍵を受け入れるようにポリシーを設定
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, port=port, username=user, password=passwd)

    #コマンド実行
    _, stdout, stderr = client.exec_command(cmd)
    output = stdout.readlines() + stderr.readlines()
    if output:
        print('--- Output ---')
        for line in output:
            print(line.strip())

if __name__ == '__main__':
    import getpass

    #現在の環境からユーザー名を取得する
    # user = getpass.getuser()
    user = input('Username: ')
    password = getpass.getpass()

    ip = input('Enter server IP: ') or '192.168.1.203'
    port = input('Enter port or <CR>: ') or 2222
    cmd = input('Enter command or <CR>: ') or 'id'
    ssh_command(ip, port, user, password, cmd)
