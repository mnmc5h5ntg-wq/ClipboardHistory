#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R91 的变异电池：新加的那条机制级守卫（探针卷不许再发拖拽事件 / 两颗读数必须在）有没有牙。

harness = `swift test --filter testProbeSuiteNeverSynthesizesAdragSession`（单条，秒级）。

一条自己的规矩（R90 的 U-200 那一族）：**"harness 退出非 0"不等于"抓到了"**。
Swift 卷退出非 0 有两种成因 —— 断言红，或者**编译不过**。刀把代码改坏了也会红，
那种红是在给刀打分，不是在给判据打分。⇒ 这里只认"跑起来了并且是那条守卫失败"，
编译错误一律记 NOT-RUN（刀坏了，修刀不修判据）。

跑法：
    python3 .scratch/motion-audit-2/mutate_r91_zombie.py --measure   # 只看基线
    python3 .scratch/motion-audit-2/mutate_r91_zombie.py             # 逐刀
"""
import os
import re
import subprocess
import sys

REPO = '/Users/wangziyi/Codex_Project0'
PROBE = os.path.join(REPO, 'ClipboardHistory/Tests/ClipboardHistoryAppTests/UIInteractionProbeTests.swift')
GUARD = os.path.join(REPO, 'ClipboardHistory/Tests/ClipboardHistoryAppTests/SidebarListSelectionTests.swift')
GUARD_TEST = 'testProbeSuiteNeverSynthesizesADragSession'


def read(path):
    with open(path, encoding='utf-8') as handle:
        return handle.read()


def write(path, text):
    with open(path, 'w', encoding='utf-8') as handle:
        handle.write(text)


def run_harness():
    proc = subprocess.Popen(['env', '-u', 'SDKROOT', 'swift', 'test', '--filter', GUARD_TEST],
                            cwd=os.path.join(REPO, 'ClipboardHistory'),
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.communicate()[0].decode('utf-8', 'replace')
    return proc.returncode, out


def verdict(out):
    """把"断言红 / 编译坏 / 真绿"分开。只有第一种算 CAUGHT。"""
    if re.search(r"error: (cannot find|no such|use of|extraneous|consecutive)", out):
        return 'COMPILE', []
    fails = [l for l in out.splitlines() if 'error:' in l and GUARD_TEST in l]
    if fails:
        return 'RED', fails[:2]
    if 'Compiling' in out and 'error:' in out:
        return 'COMPILE', [l for l in out.splitlines() if 'error:' in l][:2]
    # 注意单复数：Swift 跑一条用例时打的是 "Executed 1 test, with 0 failures"（没有 s）。
    # 第一版按 `Executed \d+ tests,` 匹配 ⇒ 基线被读成 UNKNOWN ⇒ 整支电池拒跑，
    # 而我把 `| tail` 的退出码当成了它的退出码（U-200 那一族，本轮又犯一次）。
    if re.search(r'Executed \d+ tests?, with 0 failures', out):
        return 'GREEN', []
    return 'UNKNOWN', [l for l in out.splitlines() if 'error:' in l][:2]


# ---- 刀：每刀返回 (要改的文件, 改后的全文)。改坏就抛，由主循环记 NOT-RUN。----

def k_readd_drag_event(_):
    s = read(PROBE)
    anchor = '        emit("DRAG-LIMIT '
    assert s.count(anchor) == 1, s.count(anchor)
    # 这两行一定编译得过（隐式成员查找走函数实参是标准写法），并且**非注释地**出现
    # `(.leftMouseDragged` —— 第一版写 `_ = NSEvent.EventType(.leftMouseDragged)`，
    # 编译器不认那种隐式成员位置 ⇒ 刀自己坏了（NOT-RUN），而那不该算判据有牙。
    insert = ('        func _probeUses(_ t: NSEvent.EventType) { _ = t }\n'
              '        _probeUses(.leftMouseDragged)\n')
    return PROBE, s.replace(anchor, insert + anchor, 1)


def k_drop_drag_limit_reading(_):
    s = read(PROBE)
    start = s.index('        emit("DRAG-LIMIT ')
    end = s.index('\n', s.index('手工清单第 2 节")', start)) + 1
    return PROBE, s[:start] + s[end:]


def k_drop_explanation(_):
    s = read(PROBE)
    start = s.index('    // 这里**曾经**有一条')
    end_marker = '以后谁再往探针卷里塞合成拖拽就会红'
    end = s.index('\n', s.index(end_marker, start)) + 1
    return PROBE, s[:start] + s[end:]


def k_drop_frame_witness(_):
    s = read(PROBE)
    start = s.index('        emit("FRAME_CHANNEL ')
    end = s.index('\n', start) + 1
    return PROBE, s[:start] + s[end:]


def k_guard_blind_to_rename(_):
    """把守卫从"扫事件类型"退回"扫函数名" —— 这一刀测的是**守卫自己会不会被改名绕过**：
    探针里事件类型还在、函数名没有 ⇒ 退回的守卫会绿 ⇒ 必须记 ESCAPED 才算说出真相。
    本轮把它列进来，是为了让"机制级 vs 名字级"这件事有一个可重放的读数，而不是台账里一句话。"""
    s = read(GUARD)
    assert s.count('probe.contains("(.leftMouseDragged")') == 1
    return GUARD, s.replace('probe.contains("(.leftMouseDragged")', 'probe.contains("pressNudgeRelease")', 1)


KNIVES = [
    ('M505', u'探针里再发一颗 .leftMouseDragged（守卫认不认机制）', k_readd_drag_event),
    ('M506', u'删掉 DRAG-LIMIT 那行读数（限制被悄悄抹平）', k_drop_drag_limit_reading),
    ('M507', u'删掉"为什么删掉拖选探针"的解释块（守卫失去依据）', k_drop_explanation),
    ('M508', u'删掉 FRAME_CHANNEL 那颗证人（0 样本会被读成产品红）', k_drop_frame_witness),
    ('M509', u'守卫退回"扫函数名"（改名即可绕过 ⇒ 期望 ESCAPED）', k_guard_blind_to_rename),
]


def main():
    baseline = {p: read(p) for p in (PROBE, GUARD)}
    code, out = run_harness()
    kind, lines = verdict(out)
    print('基线：harness=%d 判定=%s %s（范围 = 单条守卫 %s；不含整卷 Swift）' % (code, kind, lines[:1], GUARD_TEST))
    if '--measure' in sys.argv:
        print('EXPECTED: harness=0/GREEN（当前 %s）' % kind)
        return 0
    if kind != 'GREEN' or code != 0:
        print('基线不是"跑起来并且绿" ⇒ 拒跑\n' + out[-1200:])
        return 2
    caught = escaped = notrun = 0
    for tag, note, fn in KNIVES:
        print('%s %s' % (tag, note))
        try:
            path, mutated = fn(None)
        except Exception as error:
            print('   NOT-RUN 刀自己坏了：%r' % error)
            notrun += 1
            continue
        original = baseline[path]
        if mutated == original:
            print('   NOT-RUN 这一刀什么都没改（刀坏了，不是判据没牙）')
            notrun += 1
            continue
        write(path, mutated)
        try:
            code, out = run_harness()
        finally:
            write(path, original)
        if any(read(p) != baseline[p] for p in baseline):
            print('   !! 还原失败 —— 手工检查 %s' % path)
            return 3
        kind, lines = verdict(out)
        if kind == 'COMPILE':
            print('   NOT-RUN 编译坏了（刀坏了，不是判据没牙）：%s' % lines[:1])
            notrun += 1
        elif kind == 'RED':
            print('   CAUGHT（守卫失败）%s' % [l.split(' : ')[-1][:70] for l in lines])
            caught += 1
        elif kind == 'GREEN':
            print('   ESCAPED（守卫仍然绿 —— 这一格就是它没牙的证据）')
            escaped += 1
        else:
            print('   NOT-RUN 读不出成因：%s' % lines[:1])
            notrun += 1
    print(u'汇总：%d 刀 CAUGHT / %d 逃掉 / %d 没跑成（共 %d）' % (caught, escaped, notrun, len(KNIVES)))
    # M509 是**故意**要逃的那一刀：它测的是"守卫若退回名字级就会漏"，逃掉才是本轮想记的事实。
    # ⇒ 退出码规则：不许有 NOT-RUN；逃掉的必须**只有** M509 那一刀。
    return 1 if (notrun or escaped != 1) else 0


if __name__ == '__main__':
    sys.exit(main())
