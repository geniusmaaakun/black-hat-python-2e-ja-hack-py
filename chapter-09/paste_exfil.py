#Pastebinを経由しての送信。Ｗｅｂサイトに送信することでファイヤーウォールを回避する

from win32com import client

import random
import requests
import time

#認証情報
username = 'tim'
password = 'seKret'
api_dev_key = 'cd3xxx001xxxx02'


#
def plain_paste(title, contents):
    login_url = 'https://pastebin.com/api/api_login.php'
    #自分のアカウントでPastebinへコンテンツを作成するには、リクエストを二回送る。ログインと、コンテンツ作成
    login_data = {
        'api_dev_key': api_dev_key,
        'api_user_name': username,
        'api_user_password': password,
    }
    r = requests.post(login_url, data=login_data)
    #APIにＰｏｓｔした返り値をセットする必要がある
    api_user_key = r.text

    #アップロードするデータの名前とコンテンツを、Ｋｅｙとともに送信
    paste_url = 'https://pastebin.com/api/api_post.php'
    paste_data = {
        'api_paste_name': title,
        'api_paste_code': contents.decode(),
        'api_dev_key': api_dev_key,
        'api_user_key': api_user_key,
        'api_option': 'paste',
        'api_paste_private': 0,
    }
    #
    r = requests.post(paste_url, data=paste_data)
    print(r.status_code)
    print(r.text)


#ブラウザがイベントを終了したことを確認
def wait_for_browser(browser):
    while browser.ReadyState != 4 and browser.ReadyState != 'complete':
        time.sleep(0.1)

#プログラムで自動化された動作に見えないようにする
def random_sleep():
    time.sleep(random.randint(5, 10))


#pastebinへのログインとナビゲーションを処理
def login(ie):
    full_doc = ie.Document.all
    for elem in full_doc:
        if elem.id == 'loginform-username':
            elem.setAttribute('value', username)
        elif elem.id == 'loginform-password':
            elem.setAttribute('value', password)

    random_sleep()
    if ie.Document.forms[0].id == 'w0':
        ie.document.forms[0].submit()
    wait_for_browser(ie)

#ダッシュボードにログインし、情報をアップロードする準備
def submit(ie, title, contents):
    full_doc = ie.Document.all
    for elem in full_doc:
        if elem.id == 'postform-name':
            elem.setAttribute('value', title)

        elif elem.id == 'postform-text':
            elem.setAttribute('value', contents)

        #公開範囲をプライベートにする
        #elif elem.id == 'postform-status':
        #    elem.setAttribute('value', 2)

    if ie.Document.forms[0].id == 'w0':
        ie.document.forms[0].submit()
    random_sleep()
    wait_for_browser(ie)


#pastebinに保存したい全ての文章に対して呼び出される
def ie_paste(title, contents):
    #IEのＣＯＭオブジェクトの新しいインスタンスを作成
    ie = client.Dispatch('InternetExplorer.Application')
    #プロセスを表示するかの設定。デバッグ時は表示する
    ie.Visible = 1

    ie.Navigate('https://pastebin.com/login')
    wait_for_browser(ie)
    login(ie)
    random_sleep()

    ie.Navigate('https://pastebin.com/')
    wait_for_browser(ie)
    submit(ie, title, contents.decode())

    #ＩＥを終了
    ie.Quit()


if __name__ == '__main__':
    ie_paste('title', b'contents')