#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R375 / BACKLOG 433：刀的崩溃安全还原 + 硬超时。

两个现场（R374）：
  ① `mutate_r56_readings_channel.py M278` 让 `CaptureReadings.emit` 提前 return，守卫本应 0.029 秒内红，
     实际 xctest 跑到 6:29 仍未结束；第二次还叠了「管道读者先死 ⇒ xctest 写 stdout 阻塞」。
  ② 强杀绕过 `finally`，`CaptureReadings.swift` 两次留下 `return   // MUTANT`。

这一支只负责两件事：落刀前**备份**、表启动时**校验并恢复**未完成的落刀；跑腿加**硬超时**
（POSIX 进程组，超时即 KILL 整组，不留孤儿）。

R376 补三格（M278 的挂点已经抓到了，不是产品、也不是守卫，是**刀文自己**）：
  ③ `swallowed_return_lines`：`return` 独占一行、下一非空行是调用表达式时，Swift 把它解析成
     `return expr` —— M278 的 `return\n    lock.lock()` 真的把 NSLock 拿走了，然后直接返回；
     后面那句 `defer { lock.unlock() }` 永远不会执行 ⇒ 同一进程第二次 `emit` 死等。
     `sample` 连跑三次都停在 `CaptureReadings.swift:76 lock.lock()`，编译器另外给一条
     warning（expression following 'return' is treated as an argument of the 'return'）——
     **刀坏，不是判据没牙**。现在落刀之前就把这种文本拦下。
  ④ 超时不再只杀进程组：R375 那一刀超时后，`xctest` 被 launchd 收养、又活了 9 分钟
     （`ps` 现读 ppid=1）——它显然不在 `swift-test` 的进程组里。现在先快照整棵子孙树，
     杀完进程组再逐个 SIGKILL，杀死后复查。
"""
import os
import re
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
    u"""跑一条命令；超时杀掉整个进程组**以及当时快照到的整棵子孙树**，返回 timed_out=True。"""
    proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, start_new_session=True)
    try:
        out, _ = proc.communicate(timeout=timeout_seconds)
        return proc.returncode, out.decode(u"utf-8", u"replace"), False
    except subprocess.TimeoutExpired:
        # 快照必须在杀之前：杀完进程组，子孙会被 launchd 收养（ppid 变 1），那条链就断了。
        kids = descendants(proc.pid)
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except OSError:
            pass
        for pid in kids:
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
        out, _ = proc.communicate()
        return None, out.decode(u"utf-8", u"replace"), True


# `return` 后面这些话不是表达式：下一行以它们开头时，`return` 不会被吞成返回值。
RETURN_NEXT_KEYWORDS = (u"case ", u"default:", u"let ", u"var ", u"if ", u"guard ",
                        u"for ", u"while ", u"switch ", u"do ", u"defer ", u"}",
                        u")", u"@", u"#")


def swallowed_return_lines(text):
    u"""找「`return` 吞掉下一行表达式」的写法，返回 [(行号, return 行, 下一行)]。

    为什么这不是风格问题：Swift 把 `return` 换行后的**调用**当作返回值
    （编译器自己会说 expression following 'return' is treated as an argument of the 'return'）。
    M278 因此不是「emit 提前返回」，而是「emit 拿走 NSLock 再返回」——
    第一刀留下的锁没人解，第二次 emit 在这把锁上死等（R376 `sample` 三跑同栈）。
    变异文里出现这种文本 ⇒ 刀下的不是它声称的那一刀，必须在落盘之前拦下。
    """
    lines = text.split(u"\n")
    hits = []
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not (stripped == u"return" or re.match(r"^return\s*//", stripped)):
            continue
        nxt = index + 1
        while nxt < len(lines) and not lines[nxt].strip():
            nxt += 1
        if nxt >= len(lines):
            continue
        following = lines[nxt].strip()
        if following.startswith(RETURN_NEXT_KEYWORDS):
            continue
        if re.match(r"^[A-Za-z_][\w.]*\s*\(", following):
            hits.append((index + 1, stripped, following[:80]))
    return hits


def _process_children():
    out = subprocess.check_output([u"/bin/ps", u"-axo", u"pid=,ppid="], text=True)
    children = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        try:
            pid, ppid = int(parts[0]), int(parts[1])
        except ValueError:
            continue
        children.setdefault(ppid, []).append(pid)
    return children


def descendants(pid):
    u"""按当前进程表快照 `pid` 的整棵子孙树（深度优先，去重，不含自己）。"""
    children = _process_children()
    seen = []
    stack = [pid]
    while stack:
        current = stack.pop()
        for kid in children.get(current, []):
            if kid in seen or kid == pid:
                continue
            seen.append(kid)
            stack.append(kid)
    return seen
