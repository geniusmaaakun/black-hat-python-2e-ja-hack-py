#ディレクトリファイルをマッピングする
#標的のサービスがOSSとして、自分の環境にインストールしておいて、ファイル構成をマッピングして、アクセスを試みる

import contextlib
import os
import queue
import requests
import sys
import threading
import time

#対象の拡張子
FILTERED = [".jpg", ".gif", ".png", ".css"]
#標的URL
TARGET = "http://127.0.0.1:31337"
THREADS = 10

answers = queue.Queue()
#マッピングしたパス
web_paths = queue.Queue()

def gather_paths():
    #アクセスを試行するファイルのリストを溜める。自分の環境にダウンロードしたファイル構成を元に辞書を作成。再帰的に
    for root, _, files in os.walk('.'):
        for fname in files:
            if os.path.splitext(fname)[1] in FILTERED:
                continue
            path = os.path.join(root, fname)
            if path.startswith('.'):
                path = path[1:]
            print(path)
            web_paths.put(path)

#context 処理の後に実行される。ワーキングディレクトリを元に戻す
@contextlib.contextmanager
def chdir(path):
    """
    On enter, change directory to specified path.
    On exit, change directory back to original.
    """
    this_dir = os.getcwd()
    os.chdir(path)
    try:
        #実行後に
        yield
    finally:
        #元のディレクトリに戻す
        os.chdir(this_dir)

#辞書を使ってターゲットに対してスキャンをする
def test_remote():
    #queueが空になるまで
    while not web_paths.empty():
        #パスを取り出す
        path = web_paths.get()
        url = f'{TARGET}{path}'
        #ロックアウト回避
        time.sleep(2)
        r = requests.get(url)
        if r.status_code == 200:
            #成功時は追加
            answers.put(url)
            sys.stdout.write('+')
        else:
            sys.stdout.write('x')
        sys.stdout.flush()

#エントリーポイント  
def run():
    mythreads = list()
    #並行処理
    for i in range(THREADS):
        print(f'Spawning thread {i}')
        t = threading.Thread(target=test_remote)
        mythreads.append(t)
        t.start()

    #完了まで待つ
    for thread in mythreads:
        thread.join()
        

if __name__ == '__main__':
    #gather_pathsの後に、ディレクトリを戻す
    with chdir("/home/kali/Downloads/wordpress/"):
        gather_paths()
    input('Press return to continue.')
    run()
    with open('myanswers.txt', 'w') as f:
        while not answers.empty():
            f.write(f'{answers.get()}\n')
    print('done')