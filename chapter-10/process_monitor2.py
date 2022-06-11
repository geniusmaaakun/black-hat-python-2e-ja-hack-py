#プロセスで有効化されている権限を記録できる。
#非特権か強い権限が有効化されているかを記録し、スクリプトになんらかの工夫をする事も簡単にできる。
#プロセス監視を利用することで、外部のファイルに危険な状態で依存しているプロセスを発見できる

import os
import sys

import win32api
import win32con
import win32security

import wmi

#監視対象のプロセスで有効化されている権限を自動的に取得
def get_process_privileges(pid):
    try:
        #プロセスＩＤを使って対象プロセスのハンドルを取得
        hproc = win32api.OpenProcess(
            win32con.PROCESS_QUERY_INFORMATION, False, pid)
        #プロセストークンを開く
        htok = win32security.OpenProcessToken(
            hproc, win32con.TOKEN_QUERY)
        #プロセスのトークン情報を要求
        privs = win32security.GetTokenInformation(
            htok, win32security.TokenPrivileges)
        privileges = ''
        for priv_id, flags in privs:
            #有効化されている権限のみを対象としているので、有効化の有無を確認
            if flags == win32security.SE_PRIVILEGE_ENABLED | win32security.SE_PRIVILEGE_ENABLED_BY_DEFAULT:
                #権限の名syぷを可読形式に変換
                privileges += f'{win32security.LookupPrivilegeName(None, priv_id)}|'
    except Exception:
        #privileges = 'N/A'

        #情報を適切に出力、記録する
        privileges = get_process_privileges(pid)

    return privileges


#proccess_monitor1のコード

def log_to_file(message):
    with open('process_monitor_log.csv', 'a') as fd:
        fd.write(f'{message}\r\n')


def monitor():
    log_to_file(
        'CommandLine, Time, Executable, Parent PID, PID, User, Privileges')
    c = wmi.WMI()
    process_watcher = c.Win32_Process.watch_for('creation')
    while True:
        try:
            new_process = process_watcher()
            cmdline = new_process.CommandLine
            create_date = new_process.CreationDate
            executable = new_process.ExecutablePath
            parent_pid = new_process.ParentProcessId
            pid = new_process.ProcessId
            proc_owner = new_process.GetOwner()

            privileges = get_process_privileges(pid)
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
