#BurpでBingを使う
#1台のサーバー上で複数のWebアプリが稼働しており、いくつかの存在を把握できていない事もある。
#ターゲットマシン上の脆弱なリソースを見つける

# -*- coding: utf-8 -*-
from burp import IBurpExtender
from burp import IContextMenuFactory

from java.net import URL
from java.util import ArrayList
from javax.swing import JMenuItem
from thread import start_new_thread

import json
import socket
import urllib

#API Keyを入手しておく
API_KEY = "YOURKEY"
API_HOST = 'api.bing.microsoft.com'

#
class BurpExtender(IBurpExtender, IContextMenuFactory):
    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        self.context = None

        # 作成した拡張機能をセットする
        callbacks.setExtensionName("BHP Bing")
        #コンテキストメニューを登録。Bingクエリの実行が可能になる
        callbacks.registerContextMenuFactory(self)
        return

    #ユーザーがどのHTTPリクエストを選択したかを判断する
    def createMenuItems(self, context_menu):
        self.context = context_menu
        menu_list = ArrayList()
        #クリックイベントを処理
        menu_list.add(JMenuItem('Send to Bing', actionPerformed=self.bing_menu))
        return menu_list

    def bing_menu(self, event):
        # ユーザーがクリックした部分を取得する
        #ハイライトされたHTTPリクエストを取得
        http_traffic = self.context.getSelectedMessages()
        print('%d requests highlighted' % len(http_traffic))

        for traffic in http_traffic:
            http_service = traffic.getHttpService()
            host = http_service.getHost()
            print("User selected host: %s" % host)
            self.bing_search(host)
        return
    
    def bing_search(self, host):
        # IPアドレスかホスト名かを判断する
        try:
            #
            is_ip = bool(socket.inet_aton(host))
        except socket.error:
            is_ip = False
        
        if is_ip:
            ip_address = host
            domain = False
        else:
            ip_address = socket.gethostbyname(host)
            domain = True
        #ホストと同じIPアドレスを持つ全てのバーチャルホストをBingに照会する
        start_new_thread(self.bing_query, ('ip:%s' % ip_address,))
        if domain:
            #Bingがインデックスしている全てのサブドメインの検索も行う
            start_new_thread(self.bing_query, ('domain:%s' % host,))

    #
    def bing_query(self, bing_query_string):
        print('Performing Bing search: %s' % bing_query_string)
        http_request = 'GET https://%s/v7.0/search?' % API_HOST
        # クエリをエンコードする
        http_request += 'q=%s HTTP/1.1\r\n' % urllib.quote(bing_query_string) 
        http_request += 'Host: %s\r\n' % API_HOST
        http_request += 'Connection:close\r\n'
        #APIキーを追加
        http_request += 'Ocp-Apim-Subscription-Key: %s\r\n' % API_KEY
        http_request += 'User-Agent: Black Hat Python\r\n\r\n'
    
        #HTTPリクエストをＭｉｃｒｏｓｏｆｔサーバーに送信
        json_body = self._callbacks.makeHttpRequest(API_HOST, 443, True,
                                                    http_request).tostring()
        #レスポンスを分割し
        json_body = json_body.split('\r\n\r\n', 1)[1]
        try:
            #jsonパーサーへ渡す
            response = json.loads(json_body)
        except (TypeError, ValueError) as err:
            print('No results from Bing: %s' % err)
        else:
            sites = list()
            if response.get('webPages'):
                sites = response['webPages']['value']
            if len(sites):
                for site in sites:
                    #サイトの情報を表示
                    print('*'*100)
                    print('Name: %s       ' % site['name'])
                    print('URL: %s        ' % site['url'])
                    print('Description: %r' % site['snippet'])
                    print('*'*100)

                    java_url = URL(site['url'])
                    #発見されたサイトがBurpのターゲットとして登録されていない場合は、自動的に追加する
                    if not self._callbacks.isInScope(java_url):
                        print('Adding %s to Burp scope' % site['url'])
                        self._callbacks.includeInScope(java_url)
            else:
                print('Empty response from Bing.: %s' % bing_query_string)
        return