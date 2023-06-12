# -*- encoding: utf-8 -*-
import sys
import time
from datetime import datetime
import random

import retr_n

def count_down(t_wait):
    while t_wait:
        t_wait = t_wait - 1
        sys.stderr.write('count %d\r' % (t_wait))
        sys.stderr.flush()
        time.sleep(1)
    
def main():
    # 毎日 18 時に実行
    #
    # 0分0秒にサーバーにアクセスが集中するのを避けるために、
    # 1～2分待ってからスタートする
    #
    h_target = 18
    sys.stderr.write('retrieve data from the server every day at %dh. \n' % (h_target))
    
    h_prev = -1
    while 1:
        t = datetime.now()
        h = t.hour
        if (h_prev, h) == ((h_target - 1) % 24, h_target)):
            t_wait = random.randint(60, 120) # 1～2分待ってスタート
            count_down(t_wait)
            sys.stderr.write('JOB at %s\n' % t.strftime('%Y/%m/%d %H:%m'))
            retr_n.one_shot()
            
        h_prev = h
        time.sleep(1)
    
if __name__ == '__main__':
    main()
    
