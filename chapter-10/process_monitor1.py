#プロセス監視ツール
#SYSTEMとして実行されるプロセスを監視する。システム侵入への鍵となる

#WMIを使用したプロセス監視ツール
#WMIは特定のイベントについてシステムを監視し、イベントが発生した時にコールバックを受け取る機能
#プロセスが生成された時刻、起動したユーザー、起動された実行ファイルとコマンドライン引数、プロセスＩＤ，親プロセスＩＤなど。
#有効化されている権限を特定する

import win32api
import win32con
import win32security
import wmi


def log_to_file(message):
    with open('process_monitor_log.csv', 'a') as fd:
        fd.write(f'{message}\r\n')


def monitor():
    head = ('CommandLine, Time, Executable, Parent PID, PID, User, '
    'Privileges')
    log_to_file(head)
    #WMIをインスタンス化
    c = wmi.WMI()
    #プロセスの生成イベントを監視
    process_watcher = c.Win32_Process.watch_for('creation')
    while True:
        try:
            #新しいプロセスイベントを取得
            new_process = process_watcher()
            cmdline = new_process.CommandLine
            create_date = new_process.CreationDate
            executable = new_process.ExecutablePath
            parent_pid = new_process.ParentProcessId
            pid = new_process.ProcessId
            #誰が親プロセスを生成したかを特定
            proc_owner = new_process.GetOwner()

            privileges = 'N/A'
            process_log_message = (
                f'{cmdline} , {create_date} , {executable},'
                f'{parent_pid} , {pid} , {proc_owner} , {privileges}'
            )
            print(process_log_message)
            print()
            log_to_file(process_log_message)
        except Exception:
            pass


if __name__ == '__main__':
    monitor()