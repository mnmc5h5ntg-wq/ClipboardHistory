#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R90 的变异电池：心跳这条通道**每一格都有牙吗**。

判据（harness）= `python3 -m unittest discover -s scripts/tests`。
为什么用它而不是自建：这一轮的守卫全部是 Python 侧的（接线 + 真值表），
而"基线绿"这句话的范围必须写清 —— 它覆盖的是 scripts/tests 这 172 格，**不**包含 Swift 卷。

三条规矩沿用前几轮踩过的坑：
  * 先 `--measure` 打一遍真实失败消息，needle 只能从那一遍抄（R42）；
  * 每一刀都要过"文件必须不同"，否则报 NOT-RUN 而不是 CAUGHT（R87：刀坏了不是判据没牙）；
  * 删除型变异的替换串不许留着原 token 前缀（R88：子串查看不见"删掉了"）。
"""
import io
import os
import subprocess
import sys

REPO = '/Users/wangziyi/Codex_Project0'
PROBE = os.path.join(REPO, 'ClipboardHistory/Tests/ClipboardHistoryAppTests/UIInteractionProbeTests.swift')
REPORT = os.path.join(REPO, 'scripts/ui_probe_report.py')
CI = os.path.join(REPO, '.github/workflows/ci.yml')

EMIT_LINE = '        CaptureReadings.emit("PROBE_PULSE \\(pulseStamp)", to: Self.pulseURL)\n'
SETUP_HEAD = '    override func setUpWithError() throws {\n'
SUPER_LINE = '        try super.setUpWithError()\n'
PULSE_NAME = '        return dir.appendingPathComponent("probe-pulse.log")\n'
PULSE_PRIORITY = '    names, channel = (pulse_hung, "pulse") if pulse_hung else (hung, "started")\n'
EMPTY_RETURN = ('        lines.append("UI_PROBE_PULSE_EMPTY=1 心跳文件在、收掉那一刻 xctest 还活着，却一条心跳都没有 ⇒ "')


def read(path):
    return io.open(path, encoding='utf-8').read()


def write(path, text):
    io.open(path, 'w', encoding='utf-8').write(text)


def swap(text, old, new):
    assert text.count(old) == 1, u'锚点命中 %d 次（要求恰好 1）：%s' % (text.count(old), old[:60])
    return text.replace(old, new, 1)


# ---- 刀（每刀返回 (路径, 新内容)）-------------------------------------------------

def k_drop_emit(_):
    return PROBE, swap(read(PROBE), EMIT_LINE, u'')


def k_stdout_channel(_):
    return PROBE, swap(read(PROBE), EMIT_LINE,
                       '        print("PROBE_PULSE \\(pulseStamp)")\n')


def k_emit_after_super(_):
    body = EMIT_LINE + SUPER_LINE
    return PROBE, swap(read(PROBE), body, SUPER_LINE + EMIT_LINE)


def k_share_capture_file(_):
    return PROBE, swap(read(PROBE), PULSE_NAME,
                       '        return dir.appendingPathComponent("capture-readings.log")\n')


def k_ci_one_report_unwired(_):
    text = read(CI)
    old = u'            --pulse /tmp/probe-pulse.log \\\n'
    assert text.count(old) == 1, u'硬门那一处的 --pulse 形状不同，检查接线：%d' % text.count(old)
    return CI, swap(text, old, u'')


def k_started_wins(_):
    return REPORT, swap(read(REPORT), PULSE_PRIORITY,
                        '    names, channel = hung, "started"\n')


def k_pulse_empty_is_ok(_):
    text = read(REPORT)
    old = u'                     "这一格不许被读成『用例一条都没开始』，也不许退回 started 那条通道当结论")\n        return lines, False\n'
    assert text.count(old) == 1, u'PULSE_EMPTY 那一格的收尾形状变了：%d' % text.count(old)
    return REPORT, swap(text, old, old.replace('return lines, False', 'return lines, True'))


def k_share_shots_dir(_):
    """在屏卷的 shots 目录改回与捕获卷共用（R89 那朵红的原样）。"""
    text = read(CI)
    old = 'CLIPBOARD_HISTORY_UI_SHOTS=/tmp/shots-probe'
    assert text.count(old) == 1, u'探针那一步的目录形状变了：%d' % text.count(old)
    return CI, text.replace(old, 'CLIPBOARD_HISTORY_UI_SHOTS=/tmp/shots-ci', 1)


KNIVES = [
    ('M497', u'删掉 setUpWithError 里那行心跳（通道整个不存在）', k_drop_emit),
    ('M498', u'心跳改成 print（走 stdout ⇒ 驱动那层的缓冲，被 kill -9 就没了）', k_stdout_channel),
    ('M499', u'心跳挪到 `try super.setUpWithError()` 之后（super 出问题就不写了）', k_emit_after_super),
    ('M500', u'心跳文件名改成与捕获卷共用（第一次写会把别人那卷整份抹掉）', k_share_capture_file),
    ('M501', u'CI 硬门那一处不传 --pulse（两处里有一处瞎）', k_ci_one_report_unwired),
    ('M502', u'报告器改成"started 优先"（心跳不再是证据，只是装饰）', k_started_wins),
    ('M503', u'`PULSE_EMPTY` 那一格从红改成绿（通道坏了却宣布有名字）', k_pulse_empty_is_ok),    ('M504', u'在屏卷的 shots 目录改回与捕获卷共用（R89 那朵红的原样）', k_share_shots_dir),
]


def run_harness():
    proc = subprocess.Popen([sys.executable, '-m', 'unittest', 'discover', '-s', 'scripts/tests'],
                            cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.communicate()[0].decode('utf-8', 'replace')
    return proc.returncode, out


def main():
    baseline = {p: read(p) for p in (PROBE, REPORT, CI)}
    code, out = run_harness()
    print('基线：harness=%d（范围 = scripts/tests 全部；不含 Swift 卷）' % code)
    if '--measure' in sys.argv:
        print('EXPECTED: harness=0（当前 %d）' % code)
        return 0
    if code != 0:
        print('基线不绿 ⇒ 拒跑\n' + out[-900:])
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
        if code != 0:
            fails = [l for l in out.splitlines() if l.startswith('FAIL:') or l.startswith('ERROR:')]
            print('   CAUGHT（harness 退出 %d）%s' % (code, fails[:2]))
            caught += 1
        else:
            print('   ESCAPED（harness 仍然 0）')
            escaped += 1
    print(u'汇总：%d 刀 CAUGHT / %d 逃掉 / %d 没跑成（共 %d）' % (caught, escaped, notrun, len(KNIVES)))
    return 1 if (escaped or notrun) else 0


if __name__ == '__main__':
    sys.exit(main())
