#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -------------------------------
# 进程锁
# -------------------------------

import os
LOCK_FILE = "./locker.dat"

def islocked():
    '''
    检查当前脚本是否已有进程在运行
    :return: 是否存在激活进程
    '''
    is_lock = False
    if os.path.exists(LOCK_FILE):
        with open(LOCK_FILE, "r") as file:
            pid = file.read().strip()

            # 尝试发出信号 0 到 pid 进程
            try:
                os.kill(int(pid), 0)
            except:
                is_lock = False  # 若进程不存在，则会抛出异常
            else:
                is_lock = True  # 若进程存在，则不会执行任何操作
    return is_lock


def lock():
    '''
    把当前脚本的进程号写入锁文件
    :return: None
    '''
    with open(LOCK_FILE, "w+") as file:
        file.write(str(os.getpid()))
