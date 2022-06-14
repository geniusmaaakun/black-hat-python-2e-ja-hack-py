#pcapファイルの処理　２
#画像に対して、人の貌の検出。貌の周りに四角形を表示

import cv2
import os

ROOT = '/home/kali/pictures'
FACES = '/home/kali/faces'
TRAIN = '/home/kali/training'


#入力元、出力先、分類器が置かれたディレクトリを指定
def detect(srcdir=ROOT, tgtdir=FACES, train_dir=TRAIN):
    for fname in os.listdir(srcdir):  
        #JPEG
        if not fname.upper().endswith('.JPEG'):
            continue
        fullname = os.path.join(srcdir, fname)
        newname = os.path.join(tgtdir, fname)
        #openCVで画像読み取り
        img = cv2.imread(fullname)
        if img is None:
            continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        training = os.path.join(train_dir, 'haarcascade_frontalface_alt.xml')
        #分類器を使って顔の検出
        cascade = cv2.CascadeClassifier(training)
        rects = cascade.detectMultiScale(gray, 1.3, 5)
        try:
            #
            if rects.any():
                print('got a face')
                #
                rects[:, 2:] += rects[:, :2]
        except AttributeError:
            print(f'No faces found in {fname}.')
            continue
         
        # 座標の戻り値を得た場合、画像内の顔の周りに四角形を描画
        for x1, y1, x2, y2 in rects:
            cv2.rectangle(img, (x1, y1), (x2, y2), (127, 255, 0), 2)
        #書き出し
        cv2.imwrite(newname, img)

if __name__ == '__main__':
    detect()
