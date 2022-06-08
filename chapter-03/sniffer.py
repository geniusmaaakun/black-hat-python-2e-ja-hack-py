#パケット盗聴

import socket
import os

# リッスンするホストのIPアドレス
#自分のIP
HOST = '192.168.1.203'

def main():
    # rawソケットを作成しパブリックなインタフェースにバインド
    #WindowsとLinuxで受信パケットを選択する
    if os.name == 'nt':
        socket_protocol = socket.IPPROTO_IP
    else:
        socket_protocol = socket.IPPROTO_ICMP

    #パケットを盗聴するために必要なパラメータを持つソケットを作成
    sniffer = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket_protocol)
    sniffer.bind((HOST, 0))
    # キャプチャー結果にIPヘッダーを含めるように指定
    #
    sniffer.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

    #実行環境がWindowsの場合、ネットワークインターフェースのドライバに対してioctlを用いてプロミスキャストモードを有効にする
    if os.name == 'nt':
        sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)
    
    # 単一パケットの読み込み
    #生パケットのまま出力。今回はパースしない
    print(sniffer.recvfrom(65565))

    #  Windowsの場合はプロミスキャスモードを無効化。状態を戻す
    if os.name == 'nt':
        sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
    

if __name__ == '__main__':
    main()