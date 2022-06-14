#pcapファイルの処理　１
#pcapファイルを読み取り、転送されたあらゆる画像を再構築し、ディスクに書き出す

#arper.pyでパケットを取得。画像があるページなどを見る

from scapy.all import TCP, rdpcap
import collections
import os
import re
import sys
import zlib

#読み取り、書き出しディレクトリの指定
OUTDIR = '/home/kali/pictures'
PCAPS = '/home/kali/Downloads'

#パケットのeaderとpayloadの属性を持つように定義
Response = collections.namedtuple('Response', ['header', 'payload'])

#ヘッダーを取得
def get_header(payload):
    try:
        #生パケットの先頭からＣＲ、ＬＦのセットが連続で表れるまで抽出
        header_raw = payload[:payload.index(b'\r\n\r\n')+2]
    except ValueError:
        sys.stdout.write('-')
        sys.stdout.flush()
        return None
    
    #デコードされたpayloadからheaderを作成
    try:
        #key value
        header = dict(re.findall(r'(?P<name>.*?): (?P<value>.*?)\r\n', header_raw.decode()))
        if 'Content-Type' not in header:
            return None
    except:
        return None

    return header


#コンテンツを取得
#HTTPレスポンスと抽出したいコンテンツタイプを受け取る
def extract_content(Response, content_name='image'):
    try:
        content, content_type = None, None
        #
        if content_name in Response.header['Content-Type']:
            #画像を含む場合content-typeにimageを含む
            #コンテンツタイプを取得
            content_type = Response.header['Content-Type'].split('/')[1]
            #コンテンツを取得
            content = Response.payload[Response.payload.index(b'\r\n\r\n')+4:]

            if 'Content-Encoding' in Response.header:
                #gzipなら解凍
                if Response.header['Content-Encoding'] == "gzip":
                    content = zlib.decompress(Response.payload, zlib.MAX_WBITS | 16)
                elif Response.header['Content-Encoding'] == "deflate":
                    content = zlib.decompress(Response.payload)
    except:
        pass

    #中身と種類を返す
    return content, content_type


class Recapper:
    def __init__(self, fname):
        pcap = rdpcap(fname)
        #TCPセッションをそれぞれに完全なTCPストリームが格納された辞書に自動的に分ける
        self.sessions = pcap.sessions()
        #pcapファイルから抽出されたレスポンスを格納する空のリスト
        self.responses = list()

    #レスポンスをpcapファイルから読み取る
    #上記の空のリストに追加
    def get_responses(self):
        #session辞書に含まれる複数のセッションを処理
        for session in self.sessions:
            payloads = list()
            #各セッションに含まれる複数のパケットを処理
            for packet in self.sessions[session]:
                try:
                    #送信元、送信先ポート80
                    if packet[TCP].dport == 80 or packet[TCP].sport == 80:
                        #ペイロードを再構築
                        if b'\r\n\r\n' in bytes(packet[TCP].payload):
                            payloads.append(b'')
                        payloads[-1] += bytes(packet[TCP].payload)
                except IndexError:
                    #追加失敗の場合の出力
                    sys.stdout.write('x')
                    sys.stdout.flush()
            #HTTPデータを再構築した後、payloadsについて処理
            for payload in payloads:
                if payload:
                    #各要素のバイト列が空でない場合、payloadをHTTPヘッダーのパース関数であり、個々のHTTPヘッダーのフィールドを辞書形式で抽出
                    header = get_header(payload)
                    if header is None:
                        continue
                    #リストに追加
                    self.responses.append(Response(header=header, payload=payload))
        print('')

    #レスポンスに含まれる画像ファイルをファイルとして書き出す
    def write(self, content_name):
        #抽出が終了したらレスポンスを処理
        for i, response in enumerate(self.responses):
            #コンテンツを抽出
            content, content_type = extract_content(response, content_name)
            if content and content_type:
                #content-typeにより拡張子を決める
                fname = os.path.join(OUTDIR, f'ex_{i}.{content_type}')
                print(f'Writing {fname}')
                #ファイルに書き出す
                with open(fname, 'wb') as f:
                    f.write(content)


if __name__ == '__main__':
    pfile = os.path.join(PCAPS, 'pcap.pcap')
    recapper = Recapper(pfile)
    #全てのレスポンスから、画像を抽出し書き出す
    recapper.get_responses()
    recapper.write('image')
