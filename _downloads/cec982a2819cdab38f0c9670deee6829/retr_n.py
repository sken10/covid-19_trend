# -*- encoding: utf-8 -*-
"""retr_n.py

川崎市リアルタイムサーベイランスからデータ(*.csv) を取得する。
    
    疾患選択:
        新型コロナウィルス感染症(COVID-19)
    
    取得ファイル名 (集計方法):
        data/kw_sex_YYMMDD_hhmmss.csv (男女別集計表)
        data/kw_age_YYMMDD_hhmmss.csv (年齢階級別集計)
        data/kw_reg_YYMMDD_hhmmss.csv (区別集計)
    
    データの種類:
        日別データ
    
    期間:
        2023年4月13日～実行日当日

注意
   - 取得したデータのレコード数を確認している。上の取得期間を変更する場合には、
     そちらも変更する必要がある。
    
   - 取得データの文字コードは SHIFT_JIS。年齢階級に「～」波ダッシュが使われている。
     SHIFT_JIS の波ダッシュは、問題を起こしやすい。

動作環境
    Python 3.11
    Windows11 (10 でも大丈夫と思う)
    コマンドプロンプトから python retr_n.py で実行
    
依存関係 (実行に必要なもの)
    
    1. Chrome (google の WEB browser)
        
    2. selenium 
        > pip install slenium
        
    3. webdriver-manager
        > pip install webdriver-manager
        selenium が要求する chrome-driver は chrome のバージョンに依存するが、
        chrome は勝手にバージョンアップすることがあるため、あらかじめ用意した
        chrome-driver で突然エラーが発生することになる。
        webdriver-manager は、適切な chrome-driver を動的に割り当ててくれる。

"""
import sys
import os
import time
import shutil
import csv
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

from webdriver_manager.chrome import ChromeDriverManager

cfg = {
    'dn_tmp': os.path.abspath(r'.\temp'),
    'fn_tmp': 'download.csv', # WEB SITE 側で決められている
}

T_WAIT = 0.2

def build_driver(url, dn_tmp):
    """
    ドライバーの生成して url で指定されたページを get する
    
    Parameters
    ----------
    url, str : WEB Page の URL
    dn_tmp, str : ファイルのダウンロード先のディレクトリ名(絶対パス)
    
    Returns
    -------
    driver, : Chrome ドライバー
    
    Notes
    -----
    ChromeDriverManager() を使って、使用している Chrome のバージョンに合った
    ドライバーを割り当てる。
    
    """
    srv = Service(ChromeDriverManager().install())
    
    opt = webdriver.ChromeOptions()
    opt.add_experimental_option("prefs", {"download.default_directory" : dn_tmp})
    opt.add_experimental_option('excludeSwitches', ['enable-logging']) # エラー出力抑止
    opt.use_chromium = True # エラー出力抑止
    
    driver = webdriver.Chrome(service=srv, options=opt)
    driver.get(url)
    driver.implicitly_wait(20) # find_element で要素が見つかるまで、最大20秒待つ
    
    return driver

def clear_temp():
    """一時ファイルの消去
    """
    file_tmp = os.path.join(cfg['dn_tmp'], cfg['fn_tmp'])
    if os.path.exists(file_tmp):
        os.remove(file_tmp)
        while os.path.exists(file_tmp):
            time.sleep(T_WAIT)
    
def retr_core(driver, sumtype, date):
    """データ取得コア
    web-page のデータ種別と日付を指定して、ダウンロードボタンを click する。
    
    Parameters
    ----------
    driver, : web-driver
    sumtype, int : 1)男女 2)年齢階級 3)区
    date, datetime : 取得日付
    
    """
    x = driver.find_element(By.ID, "diseasesCode")
    Select(x).select_by_value('23') # 新型コロナウイルス感染症（COVID-19）
    
    x = driver.find_element(By.ID, "year-from")
    Select(x).select_by_value('2023')
    x = driver.find_element(By.ID, "month-from")
    Select(x).select_by_value('4')
    x = driver.find_element(By.ID, "day-from")
    Select(x).select_by_value('13')
    
    x = driver.find_element(By.ID, "year-to")
    Select(x).select_by_value('%s' % date.year)
    x = driver.find_element(By.ID, "month-to")
    Select(x).select_by_value('%s' % date.month)
    x = driver.find_element(By.ID, "day-to")
    Select(x).select_by_value('%s' % date.day)
    
    # 集計方法(男女, 年齢階級, 区) の指定
    #   (xx の長さが 3 になるまで待つ)
    #
    while 1:
        xx = driver.find_elements(By.NAME, "sumtype")
        if len(xx) >= 3:
            break
        time.sleep(T_WAIT)
        
    for x in xx:
        if x.get_attribute("value") == "%d" % (sumtype):
            x.click()
    
    # データの種類(累計 or 日別) の指定
    #   (xx の長さが 2 になるまで待つ)
    #
    while 1:
        xx = driver.find_elements(By.NAME, "spantype")
        if len(xx) >= 2:
            break
        time.sleep(T_WAIT)
    
    x_target = False
    for x in xx:
        if x.get_attribute("value") == "2": # 日別
            x_target = x # 次の click 応答待ちでクリックした要素を参照する
            x_target.click()
            break
    
    # click 応答待ち
    #
    wait = WebDriverWait(driver, 10)
    result = wait.until(expected_conditions.element_selection_state_to_be(x_target, True))
    
    # ダウンロード click
    #
    x = driver.find_element(By.ID, "downloadcsv")
    x.click()
    
def wait_download(sumtype, date):
    """一時ファイルのダウンロード完了待ち
    ファイル生成待ち (sumtype と date を使ってデータ行数を確認する)
    """
    time.sleep(T_WAIT)
    time.sleep(T_WAIT)
    file_tmp = os.path.join(cfg['dn_tmp'], cfg['fn_tmp'])
    while not os.path.exists(file_tmp):
        print('wait %f (file gen)' % (T_WAIT))
        time.sleep(T_WAIT)
    
    # ファイル書き込み終了待ち (完了を行数で判定)
    # (書き込みが完了するまで、臨時のユニークなファイル名が使われているなら、
    #  行数参照による書き込み待ちは無意味)
    #
    time.sleep(T_WAIT)
    while 1:
        n = (date - datetime(2023, 4, 13)).days + 1 + 3
        xx = [a for a in csv.reader(open(file_tmp, encoding='sjis'))]
        if len(xx) >= n:
            break
        print('wait %f (file update)' % (T_WAIT))
        time.sleep(T_WAIT)
    
    if 1:
        # 最終的な確認
        # フィールド数
        # 最終レコードの日 (年月も確認すると丁寧か)
        reclen_spec = {1:8, 2:24, 3:26}
        assert(len(xx[-1]) == reclen_spec[sumtype])
        assert(int(xx[-1][2]) == datetime.now().day) # 最終レコードの '日'
    
def save_data(file_new, date):
    """ ファイル移動 & 日時付きファイル生成
    一時ファイル temp/download.csv を data/kw_sex.csv などに移動
    日時付きファイルも生成する(data/kw_sex_20230612_180000.csv など).
    """
    
    # 移動先ディレクトリ(正式な保存場所)の作成。通常 ./data。
    #
    dn_new, fn_new = os.path.split(file_new)
    os.makedirs(dn_new, exist_ok=True)
    
    # 一時ファイルを正式な場所/ファイル名に移動
    #
    file_tmp = os.path.join(cfg['dn_tmp'], cfg['fn_tmp'])
    shutil.move(file_tmp, file_new)
    
    # 日時情報を付加した版も保存
    #
    fb, fe = os.path.splitext(fn_new)
    ts = date.strftime('%Y%m%d_%H%M%S')
    file_save = os.path.join(dn_new, '%s_%s%s' % (fb, ts, fe))
    shutil.copy(file_new, file_save)
    
def retr(driver, sumtype, file_new):
    """データ取得
    
    sumtype で指定したデータを取得して、file_new で指定したファイル名で保存する。
    それと同時に、ファイル名に取得日時を付加したファイルも生成する。
    
    Parameters
    ----------
    driver, : web-driver
    sumtype, int : 1)男女 2)年齢階級 3)区
    file_new, str : ファイル名
    
    """
    
    date = datetime.now()
    
    # 一時ファイルの消去
    # 前のファイルが残っていると file(1).csv などの名前になってしまうので
    # 事前に一時ファイル(temp/download.csv) を消しておく。
    clear_temp()
    
    # データ種別, データ期間の指定, & ダウンロードボタン click
    #
    retr_core(driver, sumtype, date)
    
    # 一時ファイルのダウンロード完了待ち
    # ファイル生成待ち (sumtype と date を使ってデータ行数を確認する)
    #
    wait_download(sumtype, date)
    
    # ファイル移動 & 日時付きファイル生成
    # 一時ファイル temp/download.csv を data/kw_sex.csv などに移動
    # 日時付きファイルも生成する(data/kw_sex_20230612_180000.csv など).
    #
    save_data(file_new, date)
    
def one_shot():
    """
    """
    # WEB DRIVER 生成
    # ダウンロード先フォルダを用意しておく
    #
    url = 'https://kidss.city.kawasaki.jp/ja/realsurveillance/opendata'
    os.makedirs(cfg['dn_tmp'], exist_ok=True)
    driver = build_driver(url, cfg['dn_tmp'])
    
    # 男女別
    #
    retr(driver, 1, 'data/kw_sex.csv')
    time.sleep(1)
    
    # 年齢階級別
    #
    retr(driver, 2, 'data/kw_age.csv')
    time.sleep(1)
    
    # 区別
    #
    retr(driver, 3, 'data/kw_reg.csv')
    time.sleep(1)
    
    # DRIVER close
    #
    driver.close()
    
if __name__ == '__main__':
    one_shot()
    
