#フォレンジック手法の攻撃への転用
#volallity　でマシンのメモリのスナップショットを取得する。独自の攻撃用のプラグインを作成し、VM上で実行されている脆弱性のあるプロセスを探す
#さまざまなフレームワークコードを取得できる

#VMの一般情報の取得
#ユーザーの取得
#バックドアの調査
#volshellでpythonのシェルを実行する

#volallityプラグインをカスタム
#プラグインのインターフェースを満たす
# すべてのプロセスを検索し、ASLRの保護を確認する
#ASLRは脆弱なプロセスのアドレス空間をランダム化し、ヒープ、スタック、その他OSの仮想メモリの割り当て位置に影響を与える
#つまり攻撃コードを書く人は、攻撃時に標的となるプロセスのアドレス空間がどのように配置されているかを特定できない

#Win10 では、ほぼ全てのプロセスがＡＳＬＲ保護されているが、XPではされていないため有効な攻撃となる。


from typing import Callable, List

from volatility3.framework import constants, exceptions, interfaces, renderers
from volatility3.framework.configuration import requirements
from volatility3.framework.renderers import format_hints
from volatility3.framework.symbols import intermed
from volatility3.framework.symbols.windows import extensions
from volatility3.plugins.windows import pslist

import io
import logging
import pefile

vollog = logging.getLogger(__name__)

IMAGE_DLL_CHARACTERISTICS_DYNAMIC_BASE = 0x0040
IMAGE_FILE_RELOCS_STRIPPED = 0x0001

#解析を行う
def check_aslr(pe):
    pe.parse_data_directories(
        [pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_LOAD_CONFIG']])
    dynamic = False
    stripped = False

    #PEファイルのオブジェクトをパースし、DYNAMICBASEオプションをつけてコンパイルされているかどうか
    if pe.OPTIONAL_HEADER.DllCharacteristics & IMAGE_DLL_CHARACTERISTICS_DYNAMIC_BASE:
        dynamic = True
    #ファイルのしあ配置データが取り除かれているかどうか
    if pe.FILE_HEADER.Characteristics & IMAGE_FILE_RELOCS_STRIPPED:
        stripped = True
    #DYNAMICBASEオプションをつけずにコンパイルされたか、あるいはDYNAMICBASEオプションは付けらていたが再配置データが取り除かれている場合は、そのPEファイルはＡＳＬＲで保護されていない事になる
    if not dynamic or (dynamic and stripped):
        aslr = False
    else:
        aslr = True
    return aslr


#PluginInterfaceを継承
class AslrCheck(interfaces.plugins.PluginInterface):
    #必要要素の定義
    @classmethod
    def get_requirements(cls):

        return [
            #メモリ層を定義
            requirements.TranslationLayerRequirement(
                name='primary', description='Memory layer for the kernel',
                architectures=["Intel32", "Intel64"]),

            #メモリ層と一緒に、シンボルテーブルも定義
            requirements.SymbolTableRequirement(
                name="nt_symbols", description="Windows kernel symbols"),

            #すべてのプロセスをメモリから取得し、プロセスからＰＥファイルを再作成するため、pslistプラグインが要素として必要
            #各プロセスから再作成されたＰＥファイルをcheck_aslrに渡し、ASLR保護の有無を調べる
            requirements.PluginRequirement(
                name='pslist', plugin=pslist.PsList, version=(2, 0, 0)),

            #プロセスＩＤを指定して単一のプロセスを確認したい場合もあるので、プロセスＩＤのリストを渡すことで、確認の対象をそれらのプロセスのみに限定できるＯＰ設定を作成した
            requirements.ListRequirement(name='pid',
                                         element_type=int,  description="Process ID to include (all other processes are excluded)",
                                         optional=True),

        ]

    #オプションのプロセスＩＤを処理するために、クラスメソッドを使用して、リスト内のすべてのプロセスIＤに対してFalseを返すフィルタリング関数
    #ＰＩＤがリストに存在しない場合のみtrueを返す
    @classmethod
    def create_pid_filter(cls, pid_list: List[int] = None) -> Callable[[interfaces.objects.ObjectInterface], bool]:
        def filter_func(_): return False
        pid_list = pid_list or []
        filter_list = [x for x in pid_list if x is not None]
        if filter_list:
            def filter_func(
                x): return x.UniqueProcessId not in filter_list
        return filter_func

    #
    def _generator(self, procs):
        #メモリ上の各プロセスをループする際に使用する、pe_table_nameという特殊なデータ構造を作成
        pe_table_name = intermed.IntermediateSymbolTable.create(
            self.context,
            self.config_path,
            "windows",
            "pe",
            class_types=extensions.pe.class_types)

        procnames = list()
        for proc in procs:
            procname = proc.ImageFileName.cast(
                "string", max_length=proc.ImageFileName.vol.count, errors='replace')
            if procname in procnames:
                continue
            procnames.append(procname)

            proc_id = "Unknown"
            try:
                proc_id = proc.UniqueProcessId
                proc_layer_name = proc.add_process_layer()
            except exceptions.InvalidAddressException as e:
                vollog.error(
                    f"Process {proc_id}: invalid address {e} in layer {e.layer_name}")
                continue

            #各プロセスに関連するPEBのメモリ領域を取得し、オブジェクトに代入
            peb = self.context.object(
                self.config['nt_symbols'] + constants.BANG + "_PEB",
                layer_name=proc_layer_name,
                offset=proc.Peb)

            try:
                dos_header = self.context.object(
                    pe_table_name + constants.BANG + "_IMAGE_DOS_HEADER",
                    offset=peb.ImageBaseAddress,
                    layer_name=proc_layer_name)
            except Exception as e:
                continue

            pe_data = io.BytesIO()
            for offset, data in dos_header.reconstruct():
                pe_data.seek(offset)
                pe_data.write(data)
            #PEBは現在のプロセス領域をファイルオブジェクト(pe_data)に書き込む
            pe_data_raw = pe_data.getvalue()
            pe_data.close()

            try:
                #pefileライブラリを使ってPEオブジェクトを作成
                pe = pefile.PE(data=pe_data_raw)
            except Exception as e:
                continue

            #check_aslrに渡す
            aslr = check_aslr(pe)

            #最終的に、プロセスＩＤ，プロセス名、プロセスのメモリアドレス、ＡＳＬＲ保護が有効かの真偽値の情報を含むタプルを取得
            yield (0, (proc_id,
                       procname,
                       format_hints.Hex(pe.OPTIONAL_HEADER.ImageBase),
                       aslr,
                       ))

    #すべての設定がconfigオブジェクトに格納されているため、引数は不要
    def run(self):
        #pslistプラグインを使ってプロセスのリストを取得
        procs = pslist.PsList.list_processes(self.context,
                                             self.config["primary"],
                                             self.config["nt_symbols"],
                                             filter_func=self.create_pid_filter(self.config.get('pid', None)))
        #TreeGridレンダリングエンジンを使ってジェネレーターからデータを返す
        return renderers.TreeGrid([
            ("PID", int),
            ("Filename", str),
            ("Base", format_hints.Hex),
            ("ASLR", bool)],
            self._generator(procs))
