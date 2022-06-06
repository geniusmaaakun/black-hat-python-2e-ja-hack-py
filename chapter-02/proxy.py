#TCPプロキシ
#ローカルとリモートの間に入るサーバー

import sys
import socket
import threading

#ASCIIに印字可能ならそのまま、それ以外は.にする変換テーブル
HEX_FILTER = ''.join(
    [(len(repr(chr(i))) == 3) and chr(i) or '.' for i in range(256)])

#16進数にダンプする
def hexdump(src, length=16, show=True):
    #バイトデータの場合は文字列にデコード
    if isinstance(src, bytes):
        src = src.decode()
    results = list()
    for i in range(0, len(src), length):
        #ダンプするデータの一部(length)を取り出す。
        word = str(src[i:i+length])
        #対応文字に変換
        printable = word.translate(HEX_FILTER)
        #生データを16進数に変換
        hexa = ' '.join([f'{ord(c):02X}' for c in word])
        #文字埋め
        hexwidth = length*3
        results.append(f'{i:04x}  {hexa:<{hexwidth}}  {printable}')
    if show:
        for line in results:
            print(line)
    else:
        return results


#プロキシがデータを受信するための関数
def receive_from(connection):
    buffer = b""
    #タイムアウト
    connection.settimeout(5)
    try:
        while True:
            #タイムアウトまでデータを読み込む
            data = connection.recv(4096)
            if not data:
                break

            buffer += data
    except:
        pass

    return buffer


#リクエスト、レスポンスの改変、修正
def request_handler(buffer):
    # パケットの改変をここで行うことができる
    return buffer


def response_handler(buffer):
    # パケットの改変をここで行うことができる
    return buffer


def proxy_handler(client_socket, remote_host, remote_port, receive_first):
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #リモートホストに接続
    remote_socket.connect((remote_host, remote_port))

    #最初にリモート側へデータを要求する必要がないことを確認する。サーバーデーモンの中には要求するものがあるため
    if receive_first:
        #データ読み込み
        remote_buffer = receive_from(remote_socket)
        if len(remote_buffer):
            print("[<==] Received %d bytes from remote." % len(remote_buffer))
            hexdump(remote_buffer)

            #受信したバッファをクライアントに送信
            remote_buffer = response_handler(remote_buffer)
            client_socket.send(remote_buffer)
            print("[==>] Sent to local.")

    #ローカルクライアントからのからのデータが検出されなくなるまで繰り返し処理
    while True:
        local_buffer = receive_from(client_socket)
        if len(local_buffer):
            print("[<==] Received %d bytes from local." % len(local_buffer))
            hexdump(local_buffer)

            local_buffer = request_handler(local_buffer)
            remote_socket.send(local_buffer)
            print("[==>] Sent to remote.")

        remote_buffer = receive_from(remote_socket)
        if len(remote_buffer):
            print("[<==] Received %d bytes from remote." % len(remote_buffer))
            hexdump(remote_buffer)

            remote_buffer = response_handler(remote_buffer)
            client_socket.send(remote_buffer)
            print("[==>] Sent to local.")

        #リモートとローカルのどちらかに送信するデータがなくなると終了。ソケットを閉じる
        if not len(local_buffer) or not len(remote_buffer):
            client_socket.close()
            remote_socket.close()
            print("[*] No more data. Closing connections.")
            break


#接続を設定、管理
def server_loop(local_host, local_port, remote_host, remote_port, receive_first):
    #ソケット作成
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        #ローカルホストにバインドして接続を待ち受ける
        server.bind((local_host, local_port))
    except Exception as e:
        print('problem on bind: %r' % e)
        print("[!!] Failed to listen on %s:%d" % (local_host, local_port))
        print("[!!] Check for other listening sockets or correct permissions.")
        sys.exit(0)

    print("[*] Listening on %s:%d" % (local_host, local_port))
    server.listen(5)
    #新しい接続要求を受け取ると新しいスレッドを起動して、双方向からのデータの送受信をproxy_handlerで全て担当する
    while True:
        client_socket, addr = server.accept()
        # 接続情報の出力
        line = "> Received incoming connection from %s:%d" % (addr[0], addr[1])
        print(line)
        # リモートホストとの接続を行うスレッドの開始
        proxy_thread = threading.Thread(
            target=proxy_handler,
            args=(client_socket, remote_host,
                  remote_port, receive_first))
        proxy_thread.start()


def main():
    if len(sys.argv[1:]) != 5:
        print("Usage: ./proxy.py [localhost] [localport]", end='')
        print("[remotehost] [remoteport] [receive_first]")
        print("Example: ./proxy.py 127.0.0.1 9000 10.12.132.1 9000 True")
        sys.exit(0)
    
    local_host = sys.argv[1]
    local_port = int(sys.argv[2])

    remote_host = sys.argv[3]
    remote_port = int(sys.argv[4])

    receive_first = sys.argv[5]

    if "True" in receive_first:
        receive_first = True
    else:
        receive_first = False

    server_loop(local_host, local_port,
                remote_host, remote_port, receive_first)


if __name__ == '__main__':
    main()
