#ファイルの暗号と複合
#標的のネットワークにアクセスしたら、文書ファイルや表計算データ、その他データを標的のシステムから盗み出すことが必要
#最初にファイルの暗号化、複合を実装する

#共通鍵
from Cryptodome.Cipher import AES, PKCS1_OAEP

#公開鍵、秘密鍵
from Cryptodome.PublicKey import RSA

from Cryptodome.Random import get_random_bytes
from io import BytesIO

import base64
import zlib

#RSA鍵の生成
def generate():
    new_key = RSA.generate(2048)
    private_key = new_key.exportKey()
    public_key = new_key.publickey().exportKey()

    with open('key.pri', 'wb') as f:
        f.write(private_key)

    with open('key.pub', 'wb') as f:
        f.write(public_key)

#鍵を取得
def get_rsa_cipher(keytype):
    with open(f'key.{keytype}') as f:
        key = f.read()
    rsakey = RSA.importKey(key)
    return (PKCS1_OAEP.new(rsakey), rsakey.size_in_bytes())


#暗号化
def encrypt(plaintext):
    #平分をバイト列として渡し、圧縮
    compressed_text = zlib.compress(plaintext)

    #AES暗号で使用する、ランダムなセッションキーを生成
    session_key = get_random_bytes(16)
    cipher_aes = AES.new(session_key, AES.MODE_EAX)

    #圧縮された平分を暗号化
    ciphertext, tag = cipher_aes.encrypt_and_digest(compressed_text)

    cipher_rsa, _ = get_rsa_cipher('pub')
    #相手側で複合できるように、セッションキーを暗号文自体に付加して返す。
    #セッションキーを追加するために公開鍵から生成されたRSA鍵で暗号化
    encrypted_session_key = cipher_rsa.encrypt(session_key)

    #複合に必要な情報を一つのデータにまとめ
    msg_payload = encrypted_session_key + \
        cipher_aes.nonce + tag + ciphertext
    #base63エンコードし、結果の文字列を返す
    encrypted = base64.encodebytes(msg_payload)
    return(encrypted)


#複合化。暗号化の逆順
def decrypt(encrypted):
    #base64 デコード
    encrypted_bytes = BytesIO(base64.decodebytes(encrypted))
    cipher_rsa, keysize_in_bytes = get_rsa_cipher('pri')

    #暗号化されたバイト文字列から暗号化されたセッションキーと複合する必要のあるその他のパラメータを読み取る
    encrypted_session_key = encrypted_bytes.read(keysize_in_bytes)
    nonce = encrypted_bytes.read(16)
    tag = encrypted_bytes.read(16)
    ciphertext = encrypted_bytes.read()

    #RSA秘密鍵でセッションキーを取得
    session_key = cipher_rsa.decrypt(encrypted_session_key)
    cipher_aes = AES.new(session_key, AES.MODE_EAX, nonce)
    #その鍵を使ってAES暗号でメッセージを複合
    decrypted = cipher_aes.decrypt_and_verify(ciphertext, tag)

    #平分のバイト文字列に展開して返す
    plaintext = zlib.decompress(decrypted)
    return plaintext


if __name__ == '__main__':
    generate()
    plaintext = b'hey there you.'
    print(decrypt(encrypt(plaintext)))