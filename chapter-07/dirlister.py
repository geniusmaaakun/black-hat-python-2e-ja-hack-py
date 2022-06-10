import os

#カレントディレクトリにある全てのファイルのリストを文字列で返す
#開発する各モジュールは可変個の引数を受け取るrun関数を定義する必要がある
#これによって各モジュールを同じ方法でインポートでき、必要なら異なる引数を渡すことが出来る
def run(**args):
    print("[*] In dirlister module.")
    files = os.listdir(".")
    return str(files)

