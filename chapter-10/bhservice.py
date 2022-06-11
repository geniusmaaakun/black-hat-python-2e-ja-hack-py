#脆弱性が存在するサービスを作成
#このサービスは定期的にスクリプトを一時ディレクトリにコピーし、そのディレクトリから実行する

#bhservice_task.vbsは　実行したいスクリプトの例

import os
import servicemanager
import shutil
import subprocess
import sys

import win32event
import win32service
import win32serviceutil

SRCDIR = 'C:\\Users\\IEUser'
TGTDIR = 'C:\\Windows\\TEMP'

#サービスのクラス
class BHServerSvc(win32serviceutil.ServiceFramework):
    _svc_name_ = "BlackHatService"
    _svc_display_name_ = "Black Hat Service"
    _svc_description_ = ("Executes VBScripts at regular intervals." +
                        " What could possibly go wrong?")

    #タイムアウトを一分にし、イベントオブジェクトを作成
    def __init__(self, args):
        self.vbs = os.path.join(TGTDIR, 'bhservice_task.vbs')
        self.timeout = 1000 * 60

        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    #サービスのステータスを設定し、サービスを停止
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    #サービスを開始し、タスクを実行するmainメソッドを呼び出す
    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        self.main()

    #
    def main(self):
        #サービスが停止のシグナルを受け取るまで
        while True:
            ret_code = win32event.WaitForSingleObject(self.hWaitStop, self.timeout)
            #タイムアウトまでの時間の間実行
            if ret_code == win32event.WAIT_OBJECT_0:
                servicemanager.LogInfoMsg("Service is stopping")
                break
            
            #スクリプトファイルを対象のディレクトリにコピーし、実行、削除を行う
            src = os.path.join(SRCDIR, 'bhservice_task.vbs')
            shutil.copy(src, self.vbs)
            subprocess.call("cscript.exe %s" % self.vbs, shell=False)
            os.unlink(self.vbs)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(BHServerSvc)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(BHServerSvc)
