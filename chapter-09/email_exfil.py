#電子メールによる送信
#暗号化された情報をメールで送信する

import smtplib
import time
import win32com.client

#メールクライアント
smtp_server = 'smtp.example.com'
smtp_port = 587
smtp_acct = 'tim@example.com'
smtp_password = 'seKret'
tgt_accts = ['tim@elsewhere.com']


#暗号メールを作成
def plain_email(subject, contents):
    #subjectとcontentsを受け取りSMTPサーバーのデータとメッセージの内容を合体させたメッセージを形成
    message = f'Subject: {subject}\nFrom: {smtp_acct}\n'
    message += f'To: {", ".join(tgt_accts)}\n\n{contents.decode()}'
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    #サーバーに接続してログイン
    server.login(smtp_acct, smtp_password)

    # server.set_debuglevel(1)

    #メールを送信
    server.sendmail(smtp_acct, tgt_accts, message)
    time.sleep(1)
    server.quit()


def outlook(subject, contents):
    outlook = win32com.client.Dispatch("Outlook.Application")
    message = outlook.CreateItem(0)
    #OutLookアプリケーションのインスタンスを作成。メッセージ送信後削除
    message.DeleteAfterSubmit = True
    message.Subject = subject
    message.Body = contents.decode()
    message.To = tgt_accts[0]
    #メールを送信
    message.Send()


if __name__ == '__main__':
    plain_email('test2 message', b'attack at dawn.')
