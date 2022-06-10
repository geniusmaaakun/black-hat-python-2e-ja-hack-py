#BurpSuiteを使ったファジング
#パラメータが多すぎたりして、攻撃が困難な場合に、お手軽にファザーでリクエストのHTTPリクエストを操作する。ファジングして攻撃
#パラメータを無数にテストして脆弱性を見つける

# -*- coding: utf-8 -*-
#burpを拡張する為のクラスなど
from burp import IBurpExtender
from burp import IIntruderPayloadGeneratorFactory
from burp import IIntruderPayloadGenerator
from java.util import List, ArrayList

import random

#拡張するために必要なインターフェース
class BurpExtender(IBurpExtender, IIntruderPayloadGeneratorFactory):
    #クラスを登録し、自作のペイロードを登録
    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()

        #
        callbacks.registerIntruderPayloadGeneratorFactory(self)
        return
    
    #ペイロードジェネレーターの名前を返す
    def getGeneratorName(self):
        return "BHP Payload Generator"

    #攻撃パラメータを受け取り、IIntruderPayloadGeneratorインスタンスを返す
    def createNewInstance(self, attack):
        return BHPFuzzer(self, attack)

#
class BHPFuzzer(IIntruderPayloadGenerator):
    def __init__(self, extender, attack):
        self._extender = extender
        self._helpers = extender._helpers
        self._attack = attack
        #ファジングの終了判定
        self.max_payloads = 10
        self.num_iterations = 0

        return
    
    #改変したリクエストをBurpに送り返し続けるかを決めたもの。カウンタを使って判定
    def hasMorePayloads(self):
        if self.num_iterations == self.max_payloads:
            return False
        else:
            return True
    
    #補足したHTTPリクエストからオリジナルのペイロードを受け取る。ファイジングしたい部分からファジングケースを生成する
    def getNextPayload(self, current_payload):
        # byteで受け取るため、文字列に変換する
        payload = ''.join(chr(x) for x in current_payload)

        # POSTメソッドで送信されるペイロードに単純な改変を加えるメソッドを呼び出す
        payload = self.mutate_payload(payload)

        # ファジングの回数のカウンターをインクリメントする
        self.num_iterations += 1

        return payload
    
    #同じファジングセットを使う場合、ポジションごとにファジングケースの先頭から反復処理を行う。
    def reset(self):
        #イテレーションをリセット
        self.num_iterations = 0
        return
    
    def mutate_payload(self, original_payload):
        # ファジングの方法をひとつ選ぶ、もしくは外部スクリプトを呼び出す
        picker = random.randint(1, 3)

        # ペイロードからランダムな箇所を選ぶ
        offset = random.randint(0, len(original_payload) - 1)
        #2つのランダムなチャンクに分割する
        front, back = original_payload[:offset], original_payload[offset:]

        # 先ほど選んだ箇所でSQLインジェクションを試す
        if picker == 1:
            #ランダムな位置にシングルクォートを入れる
            front += "'"
        
        # クロスサイトスクリプティングの脆弱性がないか試す
        elif picker == 2:
            #ランダムな位置にＪＳを入れる
            front += "<script>alert('BHP!');</script>"
        
        # オリジナルのペイロードのランダムな箇所で、選択した部分を繰り返す
        elif picker == 3:
            #
            chunk_length = random.randint(0, len(back)-1)
            repeater = random.randint(1, 10)
            for _ in range(repeater):
                front += original_payload[:offset + chunk_length]

        #backを追加し、返す
        return front + back
