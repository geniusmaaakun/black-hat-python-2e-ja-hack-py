import os

#環境変数を取得する

def run(**args):
    print("[*] In environment module.")
    return os.environ
    