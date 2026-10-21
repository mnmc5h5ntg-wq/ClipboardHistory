#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R268 的变异表：三把刀，三张轴（D-244 一把只钉一件事）。

M826（产品轴）把 `DailyCopyLedger.syncWriteFailure` 里那句「只在值变了才同步」的比较换成恒真 ⇒
      成功写盘也会发布一次。这一刀钉的是 R268 新加的**正面证人**有没有用：
      以前那格 `pumpMain(seconds: 0.8)` 之后直接断言「没多发」，负载高的时候它可能是假绿；
      现在先等文件出现再问那一句，所以这把刀必须 CAUGHT。
M827（尺轴 / 等待形状）把 `pollUntil` 的轮询循环改空转（一次都不等）⇒ `hit` 恒 false ⇒
      「等到」直接进断言那一格必须红。这一刀钉的是"改成等条件"没退化成"永远绿"。
M828（工具轴）把 `wait_scan.py` 的注释剥离换成朴素 `split('//')` ⇒
      含 URL 字符串的那行会被截断 ⇒ 人造正对照必须点名（尺坏 = 红，不是静默给 0）。

两张 Swift 侧的表**不需要重捕帧**：量的都是对象发布次数与盒子值，产物不在磁盘上（D-240 的分界）。
「跑起来了没」按结论行形状认；没有结论行一律 NOT_RUN（编译红不算 CAUGHT = D-243）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = '/Users/wangziyi/Codex_Project0'
LEDGER = 'ClipboardHistory/Sources/ClipboardHistoryApp/Managers/DailyCopyLedger.swift'
HEATMAP = 'ClipboardHistory/Tests/ClipboardHistoryAppTests/DailyCopyHeatmapTests.swift'
SCANNER = 'scripts/wait_scan.py'

ARMS = [
    ('M826', u'「只在值变了才同步」的比较被拿掉 = 产品轴', LEDGER,
     '        if message != lastWriteError {', '        if true {',
     'DailyCopyHeatmapTests/testASuccessfulWriteDoesNotRepublish', 'swift'),
    ('M827', u'pollUntil 不再轮询（一次都不等）= 等待形状轴', HEATMAP,
     '        while !hit && Date() < deadline {', '        while false && Date() < deadline {',
     'DailyCopyHeatmapTests/testASuccessfulWriteDoesNotRepublish', 'swift'),
    ('M828', u'剥注释改成朴素 split(双斜杠)，URL 那行被截断 = 工具轴', SCANNER,
     "        elif not in_string and line[i:i + 2] == '//':",
     "        elif line[i:i + 2] == '//':",
     'test_wait_scan', 'python'),
]


def read(p):
    return io.open(os.path.join(ROOT, p), encoding='utf-8').read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), 'w', encoding='utf-8') as h:
        h.write(t)


def run_swift(filter_name):
    env = dict(os.environ)
    env.pop('SDKROOT', None)
    proc = subprocess.run(['swift', 'test', '--filter', filter_name],
                          cwd=os.path.join(ROOT, 'ClipboardHistory'),
                          env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode('utf-8', 'replace')
    names = sorted(set(re.findall(r"Test Case '-\[[\w.]+ (\w+)\]' failed", text)))
    executed = re.findall(r'Executed (\d+) tests?, with (\d+) failures?', text)
    n_ran = int(executed[-1][0]) if executed else 0
    waited = re.findall(r'WAIT_POLL 格子=[\w-]+ waited_ms=(\d+) 等到=(\w+)', text)
    detail = ' 等待读数=' + ('/'.join('%s ms/等到 %s' % w for w in waited) if waited else '无')
    return n_ran, bool(names), names, text, detail


def run_python(test_name):
    proc = subprocess.run([sys.executable, '-m', 'unittest', '-v', test_name],
                          cwd=os.path.join(ROOT, 'scripts'),
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode('utf-8', 'replace')
    ran = 'Ran ' in text
    failed = ('FAILED' in text) or (not ran)
    names = sorted(set(re.findall(r'^(test_\w+) ', text, re.M)))
    detail = ' 结论行=' + (text.strip().splitlines()[-1] if ran else '无')
    return (1 if ran else 0), failed, names, text, detail


def main():
    caught = escaped = not_run = 0
    for arm_id, why, target, needle, repl, filter_name, kind in ARMS:
        original = read(target)
        hits = original.count(needle)
        if hits != 1:
            not_run += 1
            print('%s NOT_RUN needle 命中 %d 次（要 1）' % (arm_id, hits), flush=True)
            continue
        try:
            write(target, original.replace(needle, repl, 1))
            if kind == 'swift':
                n_ran, failed, names, text, detail = run_swift(filter_name)
            else:
                n_ran, failed, names, text, detail = run_python(filter_name)
        finally:
            write(target, original)
            if read(target) != original:
                print('%s RESTORE_FAILED ⇒ 立刻停表' % arm_id, flush=True)
                return 2
        if not n_ran:
            not_run += 1
            print('%s NOT_RUN 没有结论行（编译红不算 CAUGHT = D-243）：%s' % (arm_id, why), flush=True)
            tail = text.strip().splitlines()[-3:] if text.strip() else []
            print('   ' + ' | '.join(t.strip()[:160] for t in tail), flush=True)
            continue
        if failed:
            caught += 1
            print('%s CAUGHT  %s ｜ 红在 %s（跑=%d）%s'
                  % (arm_id, why, ', '.join(names) or '仅 exit 非 0', n_ran, detail), flush=True)
        else:
            escaped += 1
            print('%s ESCAPED %s%s' % (arm_id, why, detail), flush=True)
    print('R268_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=yes'
          % (len(ARMS), caught, escaped, not_run), flush=True)
    return 0 if (escaped == 0 and not_run == 0 and caught == len(ARMS)) else 1


if __name__ == '__main__':
    sys.exit(main())
