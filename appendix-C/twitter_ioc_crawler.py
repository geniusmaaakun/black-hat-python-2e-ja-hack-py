#メイン機能

# -*- config:utf-8 -*-
__author__ = 'Hiroyuki Kakara'

from datetime import datetime, timedelta
import get_from_web
import os
from pytz import timezone
import re
import requests
from slack_sdk import WebClient
import sys
 
os.chdir(os.path.dirname(os.path.abspath(__file__)))

SLACK_BOT_TOKEN = "!!自身のSlackボットトークンを入力!!"
TWITTER_BEARER_TOKEN = '!!自身のTwitter Bearerトークンを入力!!'
#認証情報を添付
headers = {'Authorization': f'Bearer {TWITTER_BEARER_TOKEN}'}

base_twitter_url = 'https://api.twitter.com/2'

#Tweetを取得 user_idと期間を渡す。対象期間のツイートを全て取得する
def get_tweets(user_id, interval):
    #期間を作成
    start_time = (datetime.now(timezone('UTC')) - \
        timedelta(minutes=interval)).strftime('%Y-%m-%dT%H:%M:%SZ')
    tweets = list()
    api_url  = f'{base_twitter_url}/users/{user_id}/tweets'
    #100件が最大値
    params  = {'start_time':  start_time, 'max_results': 100}

    while True:
        response = requests.get(api_url,params=params,headers=headers)
        if response.status_code == 200:
            tweets.extend(response.json()['data'])
            #次のページがある場合
            if 'next_token' in response.json()['meta']:
                #リクエストを続行。ループに戻る
                params['pagination_token'] = \
                    response.json()['meta']['next_token']
            else:
                return tweets
        else:
            #
            return tweets

#各種パース用の関数
#正規表現によりハッシュ値をすべて抽出
def extract_hash( tweet ):
    hashes = list()
    pattern = re.compile(r'\b[0-9a-fA-F]{40}\b')
    result = re.findall(pattern, str(tweet))
    for sha1 in result:
        if sha1 not in hashes:
            hashes.append(sha1)
    
    pattern = re.compile(r'\b[0-9a-fA-F]{64}\b')
    result = re.findall(pattern, str(tweet))
    for sha256 in result:
        if sha256 not in hashes:
            hashes.append(sha256)

    pattern = re.compile(r'\b[0-9a-fA-F]{32}\b')
    result = re.findall(pattern, str(tweet))
    for md5 in result:
        if md5 not in hashes:
            hashes.append(md5)

    return hashes

#正規表現によりＵＲＬ全てを抽出
def extract_url( tweet ):
    pattern = re.compile(r'https?://[\w/:%#\$&\?\(\)~\.=\+\-]+')
    result = re.findall(pattern, tweet)

    return result

def extract_hash_from_url(url):
    web = get_from_web.get_from_web()
    #Ｗｅｂのコンテンツをテキストで取得
    web_text =  web.get_web_content( url )
    if web_text == None:
        return []
    else:
        #コンテンツの結果からハッシュ値を抽出し、リストを返す
        hashes = extract_hash( web_text )
        return hashes


#Twitterのユーザー名とユーザーIDを変換する関数
#引数で受け取ったTwitterのユーザー名をURLに組み込み、リクエストすることでユーザーIDを取得
def convert_screenname_userid(username):
    api_url  = f'{base_twitter_url}/users/by/username/{username}'
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        return response.json()['data']['id']
    else:
        False

if __name__ == '__main__':
    #slackトークンを用いてSlackクライアントのインスタンスを作成
    client = WebClient(token=SLACK_BOT_TOKEN)
    client.chat_postMessage(channel="#general", text="Start processing...")
    interval = int(sys.argv[1])
    
    try:
        #クロールする対象のTwitterアカウントのリストが記載されたaccountlist.txtを読み込む
        usernames = open('accountlist.txt', 'r').readlines()
        for username in usernames:
            client.chat_postMessage(channel="#general", \
                text=f"Checking {username}...")
            username = username.replace('\r', '').replace('\n', '')
            user_id = convert_screenname_userid(username)
            if user_id:
                #アカウント毎のツイートを取得し
                tweets = get_tweets(user_id, interval)
                for tweet in tweets:
                    #各ツイートからハッシュ値、
                    hashes = extract_hash(tweet['text'])
                    #URLを取得
                    urls = extract_url(tweet['text'])
                    for url in urls:
                        #URLについては、さらにそのコンテンツからハッシュ値を抽出
                        hashes.extend(extract_hash_from_url(url))
                    if len(hashes)>0:
                        client.chat_postMessage(channel="#general", \
                            text=f"from https://twitter.com/\
                            {username}/status/{tweet['id']}")
                        client.chat_postMessage(channel="#general", \
                            text=f"```{tweet['text']}```")
                        client.chat_postMessage(channel="#general", \
                            text='Hashes: \r\n'+'\r\n'.join(hashes))
                        client.chat_postMessage(channel="#general", \
                            text="==============")
            #プログラムの結果はSlackのgeneralに投稿
            client.chat_postMessage(channel="#general", text="Finished.")
    except Exception as e:
        print(e)

       