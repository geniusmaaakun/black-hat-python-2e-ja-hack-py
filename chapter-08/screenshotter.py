#スクリーンショットの取得

import ctypes
import win32api
import win32con
import win32gui
import win32ui

#マルチモニターを含めたデスクトップ画面全体へのハンドルを取得する
def get_dimensions():
    #4Kモニターのような高解像度の環境でスケーリングを使用して表示を拡大している場合に正しく画面全体のスクリーンショットを取得する為に必要
    PROCESS_PER_MONITOR_DPI_AWARE = 2
    ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)
    width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
    height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
    left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
    top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
    return (width, height, left, top)

#
def screenshot(name='screenshot'):
    #画面の大きさを特定し、スクリーンショットの取得に必要な寸法を得る
    hdesktop = win32gui.GetDesktopWindow()
    width, height, left, top = get_dimensions()

    #デスクトップ画面へのバンドルを渡し、デバイスコンテキストを作成
    desktop_dc = win32gui.GetWindowDC(hdesktop)
    img_dc = win32ui.CreateDCFromHandle(desktop_dc)
    #ビットマップをファイルに書き込むまでの間、イメージキャプチャを保持しておくメモリデバイスコンテキストを作成
    mem_dc = img_dc.CreateCompatibleDC()

    #デスクトップ画面のデバイスコンテキストに設定されるビットオブジェクトを作成
    screenshot = win32ui.CreateBitmap()
    screenshot.CreateCompatibleBitmap(img_dc, width, height)
    #作成済みのメモリデバイスコンテキストに、キャプチャ使用としているデスクトップ画面のビットマップを設定
    mem_dc.SelectObject(screenshot)
    #デスクトップ画面のビット単位のコピーを実行。メモリデバイスコンテキストに保存
    mem_dc.BitBlt((0,0), (width, height), img_dc, (left, top), win32con.SRCCOPY)
    #イメージファイルを出力
    screenshot.SaveBitmapFile(mem_dc, f'{name}.bmp')

    mem_dc.DeleteDC()
    win32gui.DeleteObject(screenshot.GetHandle())

#
def run():
    screenshot()
    with open('screenshot.bmp') as f:
        img = f.read()
    return img


if __name__ == '__main__':
    screenshot()