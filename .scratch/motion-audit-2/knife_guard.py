#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R375 / BACKLOG 433：刀的崩溃安全还原 + 硬超时。

两个现场（R374）：
  ① `mutate_r56_readings_channel.py M278` 让 `CaptureReadings.emit` 提前 return，守卫本应 0.029 秒内红，
     实际 xctest 跑到 6:29 仍未结束；第二次还叠了「管道读者先死 ⇒ xctest 写 stdout 阻塞」。
  ② 强杀绕过 `finally`，`CaptureReadings.swift` 两次留下 `return   // MUTANT`。

这一支只负责两件事：落刀前**备份**、表启动时**校验并恢复**未完成的落刀；跑腿加**硬超时**
（POSIX 进程组，超时即 KILL 整组，不留孤儿）。它不猜 M278 为什么挂 —— 那是下一格。
"""
import os
import shutil
import signal
import subprocess

BACKUP_SUFFIX = u".knife-backup"


def backup_path(path, tag):
    directory = os.path.join(os.path.dirname(os.path.abspath(path)), BACKUP_SUFFIX)
    return os.path.join(directory, tag + u"__" + os.path.basename(path))


def backup(path, tag):
    target = backup_path(path, tag)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    shutil.copyfile(path, target)
    return target


def restore_if_stale(path, tag):
    u"""备份在盘上且与当前文件不同 ⇒ 说明上一次落刀没被还原（进程被杀）。恢复并返回 True。"""
    target = backup_path(path, tag)
    if not os.path.exists(target):
        return False
    with open(path, encoding=u"utf-8") as handle:
        current = handle.read()
    with open(target, encoding=u"utf-8") as handle:
        saved = handle.read()
    if current == saved:
        return False
    with open(path, u"w", encoding=u"utf-8") as handle:
        handle.write(saved)
    return True


def clear_backup(path, tag):
    target = backup_path(path, tag)
    if os.path.exists(target):
        os.remove(target)


def run(cmd, cwd=None, env=None, timeout_seconds=180):
    u"""跑一条命令；超时只杀**进程组**并返回 timed_out=True（不留孤儿）。"""
    proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, start_new_session=True)
    try:
        out, _ = proc.communicate(timeout=timeout_seconds)
        return proc.returncode, out.decode(u"utf-8", u"replace"), False
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except OSError:
            pass
        out, _ = proc.communicate()
        return None, out.decode(u"utf-8", u"replace"), True
