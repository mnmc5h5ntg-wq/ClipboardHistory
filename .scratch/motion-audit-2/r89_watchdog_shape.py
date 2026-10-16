#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R89 的机制对照：为什么 R88 的"组杀"在 runner 上没够到 xctest，以及补哪一刀才够。

R88 的读数（CI run 38825657419，红）：
    UI_PROBE_START_LINES_LOST=1        ← 收掉那一刻 xctest 还活着（这一格第一次在 runner 上说话）
    PROBE_FLOOR_WATCHDOG_MISSED=1 收掉之后仍有 1 个 xctest 在跑   ← 组杀没够到它

本机把 pid / ppid / **pgid** 一起量出来（`.scratch/motion-audit-2/spike_r89_group_kill.sh`）：
    swift-test  pid=24524  ppid=24520  pgid=24524   ← `set -m` 生效了，$! 就是组长
    xctest      pid=24581  ppid=24524  pgid=24581   ← 它自己 setpgid 成了**另一个组的组长**
⇒ 杀 `-24524` 只能杀到驱动。R88 的修法不是错，是**不完整**：它假设"孩子都在父亲的组里"，
   而 SwiftPM 恰恰不这么干。

这一支因此要三格，而不是两格：
    旧形状（单杀 pid）        ⇒ 必须留孤儿
    R88 形状（只杀驱动组）    ⇒ **仍然必须留孤儿**（这一格就是 R88 在 runner 上红的那件事）
    R89 形状（再杀残留孩子的组）⇒ 必须干净
中间那一格如果"干净"，就说明这条对照没在测真正的机制（它测的是 bash 的默认行为，不是 SwiftPM 的）。

用法：python3 .scratch/motion-audit-2/r89_watchdog_shape.py
"""
import os
import re
import subprocess
import sys
import time

MARK = 'xctest -XCTest R89ProbeMarker'
REPO = '/Users/wangziyi/Codex_Project0'
HELPER = '/tmp/r89_driver.sh'


def write_helper():
    """驱动脚本：孩子先 `setpgrp()` 再 exec 成带标记的 sleep —— 复刻 SwiftPM 生 xctest 的行为。"""
    body = ('#!/bin/bash\n'
            'python3 -c "import os\n'
            'os.setpgrp()\n'
            'os.execvp(\'sleep\', [\'%s\', \'60\'])" &\n'
            'wait\n' % MARK)
    with open(HELPER, 'w') as handle:
        handle.write(body)
    os.chmod(HELPER, 0o755)


def pgrep_count():
    out = subprocess.Popen(['pgrep', '-f', 'R89ProbeMarker'],
                           stdout=subprocess.PIPE).communicate()[0]
    return len([l for l in out.splitlines() if l.strip()])


def kill_everyone():
    subprocess.call('pkill -9 -f R89ProbeMarker 2>/dev/null; true', shell=True)


def run_shape(name, body):
    script = 'set -eo pipefail\n' + body
    proc = subprocess.Popen(['bash', '-c', script], stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    deadline = time.time() + 20
    while time.time() < deadline and pgrep_count() == 0:
        time.sleep(0.2)
    before = pgrep_count()
    out = proc.communicate()[0].decode('utf-8', 'replace')
    time.sleep(1.0)
    print('%-34s 收掉前=%d 退出码=%s' % (name, before, proc.returncode))
    for line in out.splitlines():
        print('    | %s' % line)
    leftover = [l for l in out.splitlines() if l.strip().startswith(u'残留>') and u'(无)' not in l]
    kill_everyone()
    return before, leftover, out


KILL_CHILDREN = '''
for child in $(pgrep -f "R89ProbeMarker" 2>/dev/null || true); do
  cpgid=$(ps -o pgid= -p "$child" 2>/dev/null | tr -d ' ' || true)
  if [ -n "$cpgid" ]; then kill -9 -"$cpgid" 2>/dev/null || true; fi
done
'''

OLD = """
bash %s &
pid=$!
( sleep 1; kill -9 "$pid" 2>/dev/null ) &
killer=$!
wait "$pid" && status=0 || status=$?
kill "$killer" 2>/dev/null || true
sleep 1
ps -eo pid,ppid,pgid,command | grep R89ProbeMarker | grep -v grep | sed 's/^/  残留> /' || echo "  残留> (无)"
""" % HELPER

R88 = """
set -m
bash %s &
pid=$!
( sleep 1; kill -9 -"$pid" 2>/dev/null || true; kill -9 "$pid" 2>/dev/null || true ) &
killer=$!
wait "$pid" && status=0 || status=$?
kill "$killer" 2>/dev/null || true
sleep 1
ps -eo pid,ppid,pgid,command | grep R89ProbeMarker | grep -v grep | sed 's/^/  残留> /' || echo "  残留> (无)"
""" % HELPER

R89 = """
set -m
bash %s &
pid=$!
( sleep 1
  alive=$(pgrep -f "R89ProbeMarker" 2>/dev/null | wc -l | tr -d " " || true)
  echo "${alive:-0}" > /tmp/r89_alive
  kill -9 -"$pid" 2>/dev/null || true
  kill -9 "$pid" 2>/dev/null || true ) &
killer=$!
wait "$pid" && status=0 || status=$?
kill "$killer" 2>/dev/null || true
for child in $(pgrep -f "R89ProbeMarker" 2>/dev/null || true); do
  cpgid=$(ps -o pgid= -p "$child" 2>/dev/null | tr -d ' ' || true)
  if [ -n "$cpgid" ]; then kill -9 -"$cpgid" 2>/dev/null || true; fi
done
sleep 1
orphans=$(pgrep -f "R89ProbeMarker" 2>/dev/null | wc -l | tr -d " " || true)
echo "UI_PROBE_ORPHAN_XCTEST=${orphans:-?}"
echo "UI_PROBE_RUNNER_ALIVE=$(cat /tmp/r89_alive 2>/dev/null || echo 未量到)"
ps -eo pid,ppid,pgid,command | grep R89ProbeMarker | grep -v grep | sed 's/^/  残留> /' || echo "  残留> (无)"
""" % HELPER


WAIT_LINE = u'          wait "$pid" && status=0 || status=$?\n'
ORPHANS_LINE = (u'          orphans=$(pgrep -f "xctest -XCTest ClipboardHistoryAppTests.UIInteractionProbeTests"'
                u" 2>/dev/null | wc -l | tr -d ' ' || true)\n")


def all_gates_have_always(text):
    """四道硬门**每一道**都要有 `if: always()`。

    第一版写的是 `text.count('if: always()') >= 4`，而文件里本来就有六处
    （两张帧基线、启动冒烟…）⇒ 删掉某一门的那一刀照样绿（M492 现场）。
    按总量数是个假尺：要按**每一个门各自**查。
    """
    gates = [u'Swift tests (executed-count gate)',
             u'Capture gate (unregistered reds must be zero)',
             u'On-screen probe coverage floor',
             u'Motion coverage floor']
    lines = text.split('\n')
    bad = []
    for name in gates:
        at = None
        for i, l in enumerate(lines):
            if l.strip() in (u'- name: ' + name, u'- name: "%s"' % name):
                at = i
                break
        if at is None:
            bad.append(name + u'（找不到这一步）')
            continue
        if not any(l.strip() == 'if: always()' for l in lines[at + 1:at + 8]):
            bad.append(name)
    if bad:
        print(u'  缺 if: always() 的门：%s' % u'、'.join(bad))
    return not bad


def io_read(path):
    with open(path, encoding='utf-8') as handle:
        return handle.read()


def ci_is_wired():
    text = io_read(os.path.join(REPO, '.github/workflows/ci.yml'))
    lines = [l.strip() for l in text.split('\n')]
    checks = [
        (lines.count(u'set -m') == 1, u'CI 少了真正的 `set -m` 那一行'),
        (text.count(u'kill -9 -"$pid"') == 1, u'CI 少了组杀那一行（或被复制成两处）'),
        (text.count(u'--runner-alive') == 2, u'两步里有一步没传分诊读数'),
        (u'for child in $(pgrep -f "xctest -XCTest ClipboardHistoryAppTests.UIInteractionProbeTests"' in text,
         u'CI 没补"再杀残留孩子的组"那一刀 ⇒ R88 的形状原样留在树上'),
        (u'PROBE_FLOOR_WATCHDOG_MISSED' in text, u'硬门没有孤儿那一格'),
        (u'PROBE_FLOOR_ORPHAN_UNMEASURED' in text, u'硬门没有"没量到就红"那一格'),
        (all_gates_have_always(text),
         u'有一道硬门没挂 `if: always()` ⇒ 它红了会把后面的证据整段 skip 掉'),
    ]
    # 位置-sensitive 的两条：同一段代码放在 `wait` 之前是**有竞态的**（R89 本机对照抓到的那件事），
    # 放在之后才是修好的。只查"有没有这段循环"会被"塞回 killer 子壳"那版喂饱。
    step = text[text.index(u'On-screen interaction probes'):text.index(u'Motion filmstrip')]
    # 锚点必须是**整行字面**（含缩进与结尾换行），不能用裸子串：
    # M490 现场 —— 裸的 `wait "$pid"` 在上文那两行注释里也出现（"bash -e 下 `wait` 拿到 137…"），
    # 于是"循环在 wait 之后"这一格读到的 index 是**注释里那一个**，刀把循环搬到真 wait 之前
    # 仍然"在它之后" ⇒ 假 OK（harness 绿，M490 逃掉）。
    checks.append((step.count(u'for child in $(pgrep') == 1
                   and step.count(WAIT_LINE) == 1
                   and step.index(u'for child in $(pgrep') > step.index(WAIT_LINE),
                   u'残留收杀不在 `wait` 那一行之后 ⇒ 它会被父壳的 `kill "$killer"` 中途掐掉（竞态）'))
    checks.append((step.count(ORPHANS_LINE) == 1
                   and step.index(ORPHANS_LINE) > step.index(u'for child in $(pgrep'),
                   u'孤儿数在残留收杀**之前**量 ⇒ 那一格永远读到 1 以上，红得没有意义'))
    checks.append((u'echo "${alive:-0}" > /tmp/ui-runner-alive' in step
                   and u'echo "${orphans:-0}" > /tmp/ui-orphans' in step,
                   u'两份读数没落盘 ⇒ 下一步（另一个 shell）拿不到分诊依据'))
    bad = [msg for ok, msg in checks if not ok]
    print(u'接线检查 %s' % (u'OK（%d 项都在）' % len(checks) if not bad else u'缺：%s' % u'；'.join(bad)))
    return not bad


def gates_come_after_evidence():
    """结构判据：四道硬门必须排在所有产证据的步骤**之后**。"""
    text = io_read(os.path.join(REPO, '.github/workflows/ci.yml'))
    names = re.findall(r'^      - name: "?([^\n"]+)"?$', text, re.M)
    # 名单**写死**，不按"名字里有没有 gate"猜：`Offscreen frame capture (report-only, gated below)`
    # 里有 "gated" 却没有门的行为，第一版按子串分类就被它判成"门在证据之前"（对照自己也会错）。
    gates = [u'Swift tests (executed-count gate)',
             u'Capture gate (unregistered reds must be zero)',
             u'On-screen probe coverage floor',
             u'Motion coverage floor']
    evidence = [u'Offscreen frame capture (report-only, gated below)',
                u'On-screen interaction probes (report-only)',
                u'Motion filmstrip (report-only)',
                u'Release script tests',
                u'Info.plist gate',
                u'Frame baseline vs working manifest (fixture-set gate)',
                u'Frame baseline vs previous release (change report, report-only)',
                u'Runtime launch smoke (report-only)']
    order = list(names)
    missing = [n for n in gates + evidence if n not in order]
    if missing:
        return False, order
    last_evidence = max(order.index(n) for n in evidence)
    first_gate = min(order.index(n) for n in gates)
    return first_gate > last_evidence, order


def main():
    write_helper()
    kill_everyone()
    print(u'=== 1. 旧形状（R86–R87：只杀驱动 pid）===')
    old_before, old_left, _ = run_shape(u'旧形状', OLD)
    print(u'=== 2. R88 形状（杀驱动进程组 —— 孩子自己 setpgid 时够不到）===')
    r88_before, r88_left, _ = run_shape(u'R88 形状（只组杀）', R88)
    print(u'=== 3. R89 形状（组杀 + 再杀残留孩子的组）===')
    r89_before, r89_left, r89_out = run_shape(u'R89 形状', R89)
    wired = ci_is_wired()
    ordered, names = gates_come_after_evidence()
    print(u'步骤顺序：%s' % (' '.join(names[-6:])))
    print(u'=== 判定 ===')
    verdicts = [
        (u'旧形状留下孤儿（对照有内容）', len(old_left) >= 1),
        (u'R88 形状**仍然**留下孤儿（这条对照测的是 SwiftPM 的 setpgid，不是 bash 默认）', len(r88_left) >= 1),
        (u'R89 形状收干净（残留=0）', len(r89_left) == 0),
        (u'R89 形状在收掉前量到"还在跑"', r89_before >= 1 and 'UI_PROBE_RUNNER_ALIVE=1' in r89_out),
        (u'CI 两步都写了（含"再杀残留孩子的组"那一刀）', wired),
        (u'四道硬门都排在产证据的步骤之后', ordered),
    ]
    bad = 0
    for label, ok in verdicts:
        print('  %s %s' % ('CAUGHT' if ok else 'ESCAPED', label))
        bad += 0 if ok else 1
    print(u'R89 对照 %d/%d 通过' % (len(verdicts) - bad, len(verdicts)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
