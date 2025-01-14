#競合状態に勝つ
#よくある問題はスクリプトファイルに対して、適切なアクセス制限が行われていない事。
#定期的に実行されているファイルとの競合状態に勝つ必要がある。ソフトウェアやタスクがファイルを作成する時、プロセスが実行、削除する前に、独自のコードをインジェクション出来るようにしておく
#先に自分のコードが実行されるようにする

#ファイル監視ツールを作成

# Modified example that is originally given here:
# http://timgolden.me.uk/python/win32_how_do_i/watch_directory_for_changes.html

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
#監視したいディレクトリのリスト
PATHS = ['c:\\WINDOWS\\Temp', tempfile.gettempdir()]


#監視したいリストに対して呼び出す監視スレッド関数
def monitor(path_to_watch):
    #監視したいディレクトリへのハンドルを入手
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
            #変更があったときに通知を受け取る
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
            #受け取る情報は、変更された対象ファイルのファイル名と、発生したイベントの種類
            for action, file_name in results:
                full_filename = os.path.join(path_to_watch, file_name)
                if action == FILE_CREATED:
                    print(f'[+] Created {full_filename}')

                elif action == FILE_DELETED:
                    print(f'[-] Deleted {full_filename}')

                elif action == FILE_MODIFIED:
                    print(f'[*] Modified {full_filename}')
                    try:
                        print('[vvv] Dumping contents ... ')
                        #対象のファイルに何が起こったのかを出力し、ファイルが変更されている事を検知した場合は、その内容を出力
                        with open(full_filename) as f:
                            contents = f.read()
                        print(contents)
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
