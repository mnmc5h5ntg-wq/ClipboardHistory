#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R92 的变异电池：那道"夹具不许覆盖共享 /tmp"的守卫到底有没有牙。

harness = `python3 -m unittest discover -s scripts/tests`（全量，约 11 秒）。

一条自己的规矩（U-200 那一族，本轮不例外）：**"harness 退出非 0"不等于"抓到了"**。
Python 卷的非零有两种成因 —— 有一条 `FAIL: test_…`，还是**刀把文件改坏到收集阶段就炸**
（SyntaxError / ImportError）。后一种红是在给刀打分。⇒ 只认前者，后者一律 NOT-RUN。

每把刀都写清楚"它假装成什么"：M510 是"撤回接线"（把 run_bash 改回旧的那一行），
M511 是"边界少一道"，M512 是"证人标准放宽"，M513 是"三支并成一支"，M514 是"落点错位"，
M515 是**已知盲区**（改的是自检根本不认识的那一步 ⇒ 预期 ESCAPED，这一把不是失败，是记账）。

跑法：
    python3 .scratch/motion-audit-2/mutate_r92_clobber.py --measure   # 只看基线
    python3 .scratch/motion-audit-2/mutate_r92_clobber.py             # 逐刀
"""
import os
import re
import subprocess
import sys

REPO = '/Users/wangziyi/Codex_Project0'
SELFTEST = os.path.join(REPO, 'scripts/tests/test_ci_report_selftest.py')
GATE = os.path.join(REPO, 'scripts/ci_capture_gate.py')
CI = os.path.join(REPO, '.github/workflows/ci.yml')


def read(path):
    with open(path, encoding='utf-8') as handle:
        return handle.read()


def write(path, text):
    with open(path, 'w', encoding='utf-8') as handle:
        handle.write(text)


def sub_once(text, old, new, tag):
    """替换必须**恰好命中一次**：命中 0 次或多次都说明锚点已经和代码脱钩了，
    那把刀就没在改它声称在改的东西（R90 的"刀坏了不是判据没牙"，同一个坑）。"""
    count = text.count(old)
    if count != 1:
        raise AssertionError('%s 的锚点命中 %d 次（要求 1）：%s' % (tag, count, old[:70]))
    return text.replace(old, new)


def run_harness():
    proc = subprocess.Popen([sys.executable, '-m', 'unittest', 'discover', '-s', 'scripts/tests'],
                            cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.communicate()[0].decode('utf-8', 'replace')
    return proc.returncode, out


def verdict(out):
    """把"断言红 / 收集阶段就炸 / 真绿"分开。只有第一种算 CAUGHT。"""
    fails = [l for l in out.splitlines() if l.startswith('FAIL: ')]
    if fails:
        return 'RED', fails[:3]
    if 'SyntaxError' in out or 'ImportError' in out or 'ModuleNotFoundError' in out:
        tail = [l for l in out.splitlines() if 'Error' in l][:2]
        return 'COLLECT', tail
    if re.search(r'^OK', out, re.M):
        return 'GREEN', []
    if re.search(r'^FAILED', out, re.M):
        # errors=（异常）但没有 FAIL: ⇒ 测试自己炸了，不是判据把变异判红
        return 'ERROR', [l for l in out.splitlines() if l.startswith('ERROR: ')][:3]
    return 'UNKNOWN', out.splitlines()[-2:]


# ---------------------------------------------------------------- 每一把刀
def k_revert_wiring(_):
    """M510：把 `run_bash` 改回 R92 之前那一行（只换 /tmp/shots-ci）。"""
    return SELFTEST, sub_once(
        read(SELFTEST),
        '    prepared = prepare(script, shots_dir)',
        '    prepared = script.replace("/tmp/shots-ci", shots_dir)',
        'M510')


def k_drop_boundary(_):
    """M511：去掉路径尾部的边界 —— 它会连 `tempfile` 的目录名一起吃。"""
    return SELFTEST, sub_once(
        read(SELFTEST),
        r'(?:/[A-Za-z0-9_.+:\-]+)*(?![A-Za-z0-9_.\-])',
        r'(?:/[A-Za-z0-9_.+:\-]+)*',
        'M511')


def k_loosen_witness(_):
    """M512：同源证人放宽成"读数通道有行就行"。"""
    return GATE, sub_once(
        read(GATE),
        '        same_source = args.readings and any(\n'
        '            line.startswith("CAPTURE_READINGS_SELFTEST") and args.readings in line\n'
        '            for line in readings_text.splitlines())',
        '        same_source = bool(args.readings) and readings_count > 0',
        'M512')


def k_collapse_causes(_):
    """M513：三支成因并回一支（全都印老那句"这一步没跑到用例"）。"""
    text = read(GATE)
    text = sub_once(text, '        if same_source:\n', '        if False:  # M513\n', 'M513a')
    text = sub_once(text, '        elif readings_count > 0:\n', '        elif False:  # M513b\n', 'M513b')
    return GATE, text


def k_frames_dir_misplaced(_):
    """M514：PNG 仍旧直接落在临时目录根，而 `find` 找的是映射出来的那一层。"""
    return SELFTEST, sub_once(
        read(SELFTEST),
        '    frames_dir = sandbox_path("/tmp/shots-ci", shots)',
        '    frames_dir = shots',
        'M514')


def k_unseen_step_writes_tmp(_):
    """M515（**预期 ESCAPED**）：往自检根本不认识的那一步里加一句共享 /tmp 写入。

    `test_cell_commands_never_address_the_shared_tmp` 扫的是 EXPECT 里那五步，
    而 `Frame baseline vs working manifest` 不在其中 ⇒ 这一句没有任何东西会去跑它。
    这一把不是"修得不够好"，是把**边界**量出来：守卫管的是"自检知道的那些步"，
    不是"作业里所有写 /tmp 的人"。出路记在 BACKLOG 129（证据挪去 per-job 的 `$RUNNER_TEMP`）。
    """
    text = read(CI)
    anchor = '          python3 scripts/frame_baseline.py check "$frames" --against working \\\n'
    if text.count(anchor) != 1:
        raise AssertionError('M515 的锚点命中 %d 次（要求 1）' % text.count(anchor))
    return CI, text.replace(
        anchor,
        '          cp /tmp/frames.log /tmp/frames-snapshot.log || true\n' + anchor)


KNIVES = [
    ('M510', '撤回接线：run_bash 只换 /tmp/shots-ci（这就是 R89 之后的原样）', k_revert_wiring, 'CAUGHT'),
    ('M511', '去掉路径尾部边界：正则连 tempfile 的目录名一起吃', k_drop_boundary, 'CAUGHT'),
    ('M512', '同源证人放宽成"读数通道有行就行"', k_loosen_witness, 'CAUGHT'),
    ('M513', '三支成因并回一支（红话重新撒谎）', k_collapse_causes, 'CAUGHT'),
    ('M514', 'PNG 落点错位：find 的是映射后那一层', k_frames_dir_misplaced, 'CAUGHT'),
    ('M515', '自检不认识的那一步里写共享 /tmp（已知盲区）', k_unseen_step_writes_tmp, 'ESCAPED'),
]


def main():
    baseline = {p: read(p) for p in (SELFTEST, GATE, CI)}
    code, out = run_harness()
    kind, detail = verdict(out)
    print('基线：harness=%d verdict=%s（范围 = scripts/tests 全部 181 条；不含 Swift 卷）' % (code, kind))
    if '--measure' in sys.argv:
        print('EXPECTED: 基线 GREEN（当前 %s）' % kind)
        return 0
    if kind != 'GREEN':
        print('基线不绿 ⇒ 拒跑\n' + out[-1200:])
        return 2
    caught = escaped = notrun = wrong = 0
    for tag, note, fn, expect in KNIVES:
        print('%s %s（预期 %s）' % (tag, note, expect))
        try:
            path, mutated = fn(None)
        except AssertionError as error:
            print('   NOT-RUN 刀自己坏了：%s' % error)
            notrun += 1
            continue
        original = baseline[path]
        if mutated == original:
            print('   NOT-RUN 这一刀什么都没改（刀坏了）')
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
        kind, detail = verdict(out)
        if kind in ('COLLECT', 'ERROR', 'UNKNOWN'):
            print('   NOT-RUN harness 炸在收集/异常阶段（%s）：%s' % (kind, detail))
            notrun += 1
            continue
        actual = 'CAUGHT' if kind == 'RED' else 'ESCAPED'
        if actual == expect:
            print('   %s%s' % (actual, ('  ← 正是这一把要量出来的盲区' if actual == 'ESCAPED' else '')))
            if actual == 'ESCAPED':
                print('     判据仍然是绿的：%s' % (detail or ''))
                escaped += 1
            else:
                print('     红在：%s' % (detail or ''))
                caught += 1
        else:
            print('   预期 %s 实际 %s ⇒ 这一格的账要重算：%s' % (expect, actual, detail))
            wrong += 1
    print('汇总：%d 刀 CAUGHT / %d 如期 ESCAPED（已知盲区）/ %d 没跑成 / %d 预期不符（共 %d）'
          % (caught, escaped, notrun, wrong, len(KNIVES)))
    return 1 if (wrong or notrun) else 0


if __name__ == '__main__':
    sys.exit(main())
