#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R88 的机制对照：看门狗那两行（`set -m` + `kill -- -$pid`）到底够不够到跑用例的进程。

为什么不是"读一眼 YAML 就算过"：这一步的产物是一段 **shell 逻辑**，
而它的正确性只有一个读法 —— 造一个和 CI 同形的多层进程（驱动 → 跑用例的 → 干活），
按旧形状与新形状各收一次，看**最里层那个还活着吗**。
旧形状必须"活着"（否则这条对照什么都没测），新形状必须"不活着"。

形状对齐 CI：
  * `swift test` 是三层（`swift` → `swift-test` → `xctest`），这里用
    `bash 驱动脚本` → 带标记串的子进程，标记串可 pgrep
    （CI 里那个串是 `xctest -XCTest ClipboardHistoryAppTests.UIInteractionProbeTests`）；
  * `set -o pipefail` 与 `bash -e` 同形（GitHub 每步都是 `bash -e`）；
  * 抽取行一律 `|| true`（R86 踩过两次的坑：非零会把汇报行整段掐掉）。

⚠ 第一版把标记串放在了**驱动自己**身上（`exec -a` 直接把后台任务变成叶子进程），
于是"旧形状留下孤儿"那一格报了 ESCAPED —— 那条对照当时什么都没测（杀父与杀组没有区别）。
三层必须是"驱动 + 另一个带标记的孩子"。这条本身记进台账。

用法：python3 .scratch/motion-audit-2/r88_watchdog_shape.py
"""
import os
import re
import subprocess
import sys
import time

MARK = 'xctest -XCTest R88ProbeMarker'
REPO = '/Users/wangziyi/Codex_Project0'
HELPER = '/tmp/r88_driver.sh'


def write_helper():
    """驱动脚本：生一个带标记的孩子，然后 `wait` —— 与 `swift-test` 生 `xctest` 同形。"""
    body = ('#!/bin/bash\n'
            'bash -c "exec -a \'' + MARK + '\' sleep 60" &\n'
            'wait\n')
    with open(HELPER, 'w') as handle:
        handle.write(body)
    os.chmod(HELPER, 0o755)


def pgrep_count():
    out = subprocess.Popen(['pgrep', '-f', 'R88ProbeMarker'],
                           stdout=subprocess.PIPE).communicate()[0]
    return len([line for line in out.splitlines() if line.strip()])


def kill_everyone():
    subprocess.call('pkill -9 -f R88ProbeMarker 2>/dev/null; true', shell=True)


def run_shape(name, body):
    """跑一段 shell（`bash -e` + pipefail，与 CI 同形），返回 (收掉前的数, 收掉后的数, 输出)。"""
    script = 'set -eo pipefail\n' + body
    proc = subprocess.Popen(['bash', '-c', script], stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    deadline = time.time() + 20
    while time.time() < deadline and pgrep_count() == 0:
        time.sleep(0.2)
    alive_at_kill = pgrep_count()
    out = proc.communicate()[0].decode('utf-8', 'replace')
    time.sleep(0.8)                      # 给 reparent 一点时间
    orphans = pgrep_count()
    print('%-26s 收掉前=%d 收掉后=%d 退出码=%s' % (name, alive_at_kill, orphans, proc.returncode))
    for line in out.splitlines():
        print('    | %s' % line)
    return alive_at_kill, orphans, out


OLD = """
bash %s &
pid=$!
( sleep 1
  ps -eo pid,ppid,pgid,command | grep R88ProbeMarker | grep -v grep | sed 's/^/  收掉前> /' || true
  kill -9 "$pid" 2>/dev/null ) &
killer=$!
wait "$pid" && status=0 || status=$?
kill "$killer" 2>/dev/null || true
sleep 2
ps -eo pid,ppid,pgid,command | grep R88ProbeMarker | grep -v grep | sed 's/^/  残留> /' || echo "  残留> (无)"
echo "旧形状 suite exit: $status"
""" % HELPER

NEW = """
set -m
bash %s &
pid=$!
( sleep 1
  alive=$(pgrep -f "R88ProbeMarker" 2>/dev/null | wc -l | tr -d " " || true)
  echo "${alive:-0}" > /tmp/r88_alive
  kill -9 -"$pid" 2>/dev/null || true
  kill -9 "$pid" 2>/dev/null || true ) &
killer=$!
wait "$pid" && status=0 || status=$?
kill "$killer" 2>/dev/null || true
orphans=$(pgrep -f "R88ProbeMarker" 2>/dev/null | wc -l | tr -d " " || true)
echo "UI_PROBE_ORPHAN_XCTEST=${orphans:-?}"
echo "UI_PROBE_RUNNER_ALIVE=$(cat /tmp/r88_alive 2>/dev/null || echo 未量到)"
sleep 2
ps -eo pid,ppid,pgid,command | grep R88ProbeMarker | grep -v grep | sed 's/^/  残留> /' || echo "  残留> (无)"
echo "新形状 suite exit: $status"
""" % HELPER


def io_read(path):
    with open(path, encoding='utf-8') as handle:
        return handle.read()


def ci_step_is_wired():
    """仓库里那两步真的写了吗 —— 这条对照测的是形状，不能替"接线"作证。"""
    text = io_read(os.path.join(REPO, '.github/workflows/ci.yml'))
    # 判"用没用"要读**行**，不能读散文：注释里也写着 `set -m`，
    # 按子串查会把"删掉了那一行而注释还在"当成还在（R77 那一族：守卫被提到该词的句子喂饱）。
    lines = [l.strip() for l in text.split('\n')]
    checks = [
        (lines.count(u'set -m') == 1,
         u'CI 的在屏那一步没有真正的 `set -m` 那一行 ⇒ 进程组根本没建起来'),
        (text.count(u'kill -9 -"$pid"') == 1,
         u'CI 仍然只杀单 PID（或组杀被复制成了两处）⇒ R86–R87 的形状没换掉'),
        (text.count(u'--runner-alive') == 2,
         u'两步里有一步没把分诊读数传给报告脚本 ⇒ 那一格会永远只读成"观察"'),
        (lines.count(u'echo "${alive:-0}" > /tmp/ui-runner-alive') == 1,
         u'收掉之前没量进程表 ⇒ 93 的两种成因今天仍然分不开'),
        (u'PROBE_FLOOR_WATCHDOG_MISSED' in text,
         u'硬门没有孤儿那一格 ⇒ 看门狗失手时 CI 照样绿'),
        (u'PROBE_FLOOR_ORPHAN_UNMEASURED' in text,
         u'硬门在"没量到孤儿数"时不红 ⇒ 那道门可以整块消失而没人报'),
    ]
    bad = [msg for ok, msg in checks if not ok]
    print(u'接线检查 %s' % (u'OK（%d 项都在）' % len(checks) if not bad else u'缺：%s' % u'；'.join(bad)))
    return not bad


def bash_n():
    """把两步的 run 块原文抽出来做语法检查（没有 pyyaml，就按缩进切）。"""
    lines = io_read(os.path.join(REPO, '.github/workflows/ci.yml')).split('\n')
    blocks, cur, indent = [], None, None
    for line in lines:
        match = re.match(r'^(\s*)run: \|\s*$', line)
        if match:
            cur, indent = [], len(match.group(1)) + 2
            continue
        if cur is not None:
            if line.strip() and (len(line) - len(line.lstrip())) >= indent:
                cur.append(line[indent:])
                continue
            blocks.append('\n'.join(cur))
            cur = None
    if cur is not None:
        blocks.append('\n'.join(cur))
    targets = [b for b in blocks if 'UIInteractionProbeTests' in b]
    ok = True
    for number, block in enumerate(targets):
        proc = subprocess.run(['bash', '-n'], input=block.encode('utf-8'),
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(u'  bash -n 第 %d 块（%d 行）%s %s'
              % (number + 1, block.count('\n') + 1,
                 'OK' if proc.returncode == 0 else u'语法错',
                 proc.stdout.decode('utf-8', 'replace').strip()))
        ok = ok and proc.returncode == 0
    return ok, len(targets)


def main():
    write_helper()
    kill_everyone()
    print(u'=== 1. 旧形状（R86–R87：只杀驱动进程）—— 必须留下孤儿，否则这条对照什么都没测 ===')
    old_alive, old_orphans, old_out = run_shape(u'旧形状', OLD)
    old_leftover = [l for l in old_out.splitlines()
                    if l.strip().startswith(u'残留>') and u'(无)' not in l]
    print(u'  旧形状脚本自己 ps 到的残留：%d 行' % len(old_leftover))
    kill_everyone()
    print(u'=== 2. 新形状（R88：进程组 + 收掉前量进程表）—— 必须没有孤儿 ===')
    new_alive, new_orphans, new_out = run_shape(u'新形状', NEW)
    new_leftover = [l for l in new_out.splitlines()
                    if l.strip().startswith(u'残留>') and u'(无)' not in l]
    print(u'  新形状脚本自己 ps 到的残留：%d 行' % len(new_leftover))
    kill_everyone()
    print(u'=== 3. CI 那两步的接线与语法 ===')
    wired = ci_step_is_wired()
    syntax, nblocks = bash_n()
    print(u'=== 判定 ===')
    verdicts = [
        (u'旧形状确实留下孤儿（对照有内容，不是恒真）', old_leftover),
        (u'新形状收干净（脚本自己 ps 里没有残留）', not new_leftover),
        (u'新形状在收掉前量到"还在跑"（RUNNER_ALIVE=1）',
         new_alive >= 1 and 'UI_PROBE_RUNNER_ALIVE=1' in new_out),
        (u'CI 两步都写了（set -m / 组杀 / --runner-alive / 硬门那一格）', wired),
        (u'两步的 shell 语法过 bash -n（块数=%d）' % nblocks, syntax and nblocks >= 2),
    ]
    bad = 0
    for label, ok in verdicts:
        print('  %s %s' % ('CAUGHT' if ok else 'ESCAPED', label))
        bad += 0 if ok else 1
    print(u'R88 对照 %d/%d 通过' % (len(verdicts) - bad, len(verdicts)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
