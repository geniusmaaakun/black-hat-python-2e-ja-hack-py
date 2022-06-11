#サンドボックス検知
#最近のウイルス対策ソフトは、疑わしいファイルの振る舞いのチェックに、ある種のサンドボックス技術を取り入れている
#サンドボックス上で実行されているかを検知する。サンドボックスの場合は継続しない。

from ctypes import byref, c_uint, c_ulong, sizeof, Structure, windll
import random
import sys
import time
import win32api

#最後の入力イベントが発生した時間を保持する
class LASTINPUTINFO(Structure):
    _fields_ = [
        ('cbSize', c_uint),
        ('dwTime', c_ulong)
    ]


#最後に入力イベントが発生した時刻を特定
def get_last_input():
    struct_lastinputinfo = LASTINPUTINFO()
    struct_lastinputinfo.cbSize = sizeof(LASTINPUTINFO)
    windll.user32.GetLastInputInfo(byref(struct_lastinputinfo))
    #マシンが起動してからどれだけの時間が経過したかを取得。最後の入力との差分
    run_time = windll.kernel32.GetTickCount()
    #タイムスタンプを格納
    elapsed = run_time - struct_lastinputinfo.dwTime
    print(
        f"[*] It's been {elapsed} milliseconds since the last event.")
    return elapsed

#実行後にキー入力などをして出力するテスト用
# while True:
#     get_last_input()
#     time.sleep(1)


#キー入力回数などを初期化
class Detector:
    def __init__(self):
        self.double_clicks = 0
        self.keystrokes = 0
        self.mouse_clicks = 0

    #用的マシン上で行われたマウスクリックの回数と発生日時、回数を取得
    def get_key_press(self):
        #妥当な入力回数の範囲でイベントの有無を繰り返し確認
        for i in range(0, 0xff):
            #イベントがキー入力化を確認
            state = win32api.GetAsyncKeyState(i)
            if state & 0x0001:
                #マウスクリックの場合はインクリメント
                if i == 0x1:
                    self.mouse_clicks += 1
                    return time.time()
                #ASCIIコードの入力の場合
                elif i > 32 and i < 127:
                    self.keystrokes += 1
        return None

    def detect(self):
        previous_timestamp = None
        first_double_click = None
        double_click_threshold = 0.35

        #マウスクリックのタイミングを補足する変数や、サンドボックスでない環境で動作していると判断するための、キー入力の回数やマウスクリックの回数のチェックに使用
        max_double_clicks = 10
        max_keystrokes = random.randint(10, 25)
        max_mouse_clicks = random.randint(5, 25)
        max_input_threshold = 30000

        #マシン上で利用者による何らかの入力が発生してからの時間を測定。最後の入力からあまりににも時間が経過してる場合は不信と判断
        last_input = get_last_input()
        if last_input >= max_input_threshold:
            sys.exit(0)

        detection_complete = False
        while not detection_complete:
            #キー押下やマウスクリックをチェックする為、キー押下やマウスクリックが発生していればそのタイムスタンプを返す
            keypress_time = self.get_key_press()
            if keypress_time is not None and previous_timestamp is not None:
                #二回のマウスクリックの時間間隔を算出
                elapsed = keypress_time - previous_timestamp
                
                #ダブルクリックだったかを判定
                if elapsed <= double_click_threshold:
                    self.mouse_clicks -= 2
                    self.double_clicks += 1
                    if first_double_click is None:
                        first_double_click = time.time()
                    else:
                        #連続的にマウスクリックをしていないかを確認
                        if self.double_clicks >= max_double_clicks:
                            #クリック回数が上限に達した場合は不信のため終了
                            if (keypress_time - first_double_click <=
                                    (max_double_clicks*double_click_threshold)):
                                sys.exit(0)
                #キー入力、シングルクリック、ダブルクリックのすべてが上限に達した場合、サンドボックス検知から抜ける
                if (self.keystrokes >= max_keystrokes and
                    self.double_clicks >= max_double_clicks and
                        self.mouse_clicks >= max_mouse_clicks):
                    detection_complete = True

                previous_timestamp = keypress_time
            elif keypress_time is not None:
                previous_timestamp = keypress_time


if __name__ == '__main__':
    d = Detector()
    d.detect()
    print('okay.')