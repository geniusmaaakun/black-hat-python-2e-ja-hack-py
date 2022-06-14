#LANに侵入している前提

#電子メールの認証情報の窃取

from scapy.all import sniff

#コールバック関数。パケットごとに実行される
def packet_callback(packet):
    #パケットを表示
    print(packet.show())

def main():
    #パケットを監視する　単一
    #使い方 P68
    sniff(prn=packet_callback, count=1)


if __name__ == '__main__':
    main()