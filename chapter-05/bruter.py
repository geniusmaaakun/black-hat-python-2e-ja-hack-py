#ディレクトリとファイルの辞書攻撃
#よく使われる辞書をダウンロードしておき、それを基に攻撃する
#このようなスキャンでは開発者が消し忘れたファイルやコードスニペットを発見できる

#wget https://www.netsparker.com/s/research/SVNDigger.zip
#unzip ZVNDigger.zip

import queue
import requests
import sys
import threading

AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:19.0) Gecko/20100101 Firefox/19.0"
EXTENSIONS = ['.php', '.bak', '.orig', '.inc']
TARGET = "http://testphp.vulnweb.com"
THREADS = 50
WORDLIST = "/home/kali/Downloads/all.txt"

#ターげっちで試す単語のキューオブジェクトを作成
def get_words(resume=None):
    #.が付くファイル名の場合は追加で拡張した拡張子も単語群に追加する
    def extend_words(word):
        if "." in word:
            words.put(f'/{word}')
        else:
            #
            words.put(f'/{word}/')

        for extension in EXTENSIONS:
            words.put(f'/{word}{extension}')

    #辞書を読み取り、各行を反復処理
    with open(WORDLIST) as f:
        raw_words = f.read()
    found_resume = False
    words = queue.Queue()
    for word in raw_words.split():
        #前回の辞書攻撃で試した最後のパスをresumeとして引数で受けとる
        if resume is not None:
            if found_resume:
                extend_words(word)
            elif word == resume:
                found_resume = True
                print(f'Resuming wordlist from: {resume}')
        else:
            print(word)
            extend_words(word)
    #辞書攻撃で使用される単語群が格納されたQueueを返す
    return words


#攻撃コード
def dir_bruter(words):
    #一般ユーザーに見えるように偽装
    headers = {'User-Agent': AGENT}
    while not words.empty():
        #キューが空になるまで
        url = f'{TARGET}{words.get()}'
        try:
            r = requests.get(url, headers=headers)
        except requests.exceptions.ConnectionError:
            #接続エラー時はxを表示
            sys.stderr.write('x')
            sys.stderr.flush()
            continue

        #成功時
        if r.status_code == 200:
            print(f'\nSuccess ({r.status_code}: {url})')
        #NotFound
        elif r.status_code == 404:
            sys.stderr.write('.');sys.stderr.flush()
        else:
            print(f'{r.status_code} => {url}')


if __name__ == '__main__':
    #単語リストを取得し、並行で攻撃
    words = get_words()
    print('Press return to continue.')
    sys.stdin.readline()
    for _ in range(THREADS):
        t = threading.Thread(target=dir_bruter, args=(words,))
        t.start()
