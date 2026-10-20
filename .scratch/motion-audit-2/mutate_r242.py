#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R242 的变异表（BACKLOG 277 / 278）：四把刀各摘掉本轮新加的一句声称。

本轮改了两处、各有一句不许空口的话：
  - Swift 侧（`UICaptureHarness.swift`）把 modechip 悬停那格的「众数颗数 > 400」换成
    **两态之间变了多少颗 + 占比 + 分母地板 + 同一帧自己的负对照**。
      · M798 把变化判定 `>= delta` 换成恒真 ⇒ 负对照必须响（不响说明那格只是装饰）。
      · M799 把两态差那把尺的矩形挪出窗外 ⇒ 分母地板必须响（"占比"不许在空矩形上签字）。
      · M800 把点亮那帧换成空闲那帧 ⇒ 颗数与占比两条地板一起必须响（对象没换=尺在读同一张纸）。
  - Python 侧（`test_final_report_headline.py`）给「最近哪一笔动过 Sources/」加了浅历史上**不许判**的闸门。
      · M801 把 `if shallow:` 摘成恒假 ⇒ 合成浅克隆那一格必须响（它真造了一颗 depth=1 的克隆）。

needle 整行/整串字面、命中恰好一次；跑完逐字节还原并复核；基线臂不可信就拒绝出表（exit 1）。
两种 runner 各认各的红名格式：swift 是 `Test Case '-[模块.类 用例]' failed`，
python 是 `FAIL: 用例` / `用例 ... FAIL` —— 拿错格式会把"没解析到"当成"没红"。
"""
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
HARNESS = 'ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift'
GUARD = 'scripts/tests/test_final_report_headline.py'
SWIFT_TEST = 'UICaptureTests/testModeChipHoverFillIsVisibleOnItsOwnSurface'

ARMS = [
    ('M798', u'两态差的判定从「差够 delta」换成恒真（抖动也算变化）', 'swift', HARNESS,
     'if abs(grey(idle, i) - grey(lit, i)) >= delta { changed += 1 }',
     'if true { changed += 1 }',
     SWIFT_TEST),
    ('M799', u'把两态差的矩形挪到窗外（分母塌了还想给占比签字）', 'swift', HARNESS,
     u'bytesPerRow: idleRaw.bpr,\n                                        rectPt: Self.modeChipFillRect, framePtWidth: 200, delta: 4)',
     u'bytesPerRow: idleRaw.bpr,\n                                        rectPt: CGRect(x: 900, y: 900, width: 4, height: 4), framePtWidth: 200, delta: 4)',
     SWIFT_TEST),
    ('M800', u'把"点亮那帧"换成"空闲那帧"（两态差读的是同一张纸）', 'swift', HARNESS,
     'Self.bandChanged(idle: idleRaw.buf, lit: litRaw.buf',
     'Self.bandChanged(idle: idleRaw.buf, lit: idleRaw.buf',
     SWIFT_TEST),
    ('M801', u'摘掉浅历史上不许判的闸门', 'python', GUARD,
     u'    if shallow:\n        return (\'skip\',',
     u'    if False:\n        return (\'skip\',',
     'test_a_shallow_history_must_not_be_allowed_to_judge'),
]


def read(p):
    return io.open(os.path.join(ROOT, p), encoding='utf-8').read()


def write(p, s):
    with io.open(os.path.join(ROOT, p), 'w', encoding='utf-8') as h:
        h.write(s)


def run_swift():
    proc = subprocess.run(['swift', 'test', '--filter', SWIFT_TEST],
                          cwd=os.path.join(ROOT, 'ClipboardHistory'),
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.stdout.decode('utf-8', 'replace'), proc.returncode


def run_python():
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
    proc = subprocess.run([sys.executable, '-m', 'unittest', '-v',
                           'scripts.tests.test_final_report_headline'],
                          cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.stdout.decode('utf-8', 'replace'), proc.returncode


def run(kind):
    return run_swift() if kind == 'swift' else run_python()


def red_names(out, kind):
    if kind == 'swift':
        return sorted(set(re.findall(r"Test Case '-\[[\w.]+ (\w+)\]' failed", out)))
    names = set(re.findall(r'^FAIL: (\S+)', out, re.M))
    names |= set(re.findall(r'^(\S+).* \.\.\. FAIL', out, re.M))
    return sorted(n.split('.')[-1] for n in names)


BASE_CACHE = {}


def baseline(kind):
    """每种 runner 只测一次基线（第一版每把刀都重跑一遍基线：三支 swift 刀就平白多花 3 次构建）。
    基线不可信 ⇒ 整表拒绝出 —— 插刀前不能确认这一卷本身是绿的，CAUGHT 就毫无意义。"""
    if kind not in BASE_CACHE:
        out, rc = run(kind)
        # 基线判据的两个出口分开：退出码说"跑成没有"，红名说"有没有红"。
        # 第一版在这里按全量卷的措辞找 'Test Suite 'All tests' passed'，而 `swift test --filter` 打的是
        # 'selected tests' ⇒ 一次绿跑被读成"基线不可信"、整表拒发（坏在最坏一侧）。
        # 第二次是**真**的不可信：并发跑了两支 swift，模块缓存被写坏成 "failed to build module 'Swift'"，
        # 退出码非 0 ⇒ 表照样拒发。这一条闸门两次都站对了方向。
        ok = rc == 0 and not red_names(out, kind) and (u'Executed' in out if kind == 'swift' else u'Ran ' in out)
        BASE_CACHE[kind] = (out, ok, rc)
    return BASE_CACHE[kind][0], BASE_CACHE[kind][1]


rows = []
caught = escaped = not_run = other = dirty = 0
for mid, why, kind, rel, old, new, want in ARMS:
    base, ok = baseline(kind)
    io.open('/tmp/r242_base_%s.log' % mid, 'w', encoding='utf-8').write(base)
    if not ok:
        print('%s 基线臂不可信 ⇒ 拒绝出表（红名=%s）' % (mid, ','.join(red_names(base, kind)) or '无'))
        sys.exit(1)
    text = read(rel)
    hits = text.count(old)
    if hits != 1:
        not_run += 1
        rows.append((mid, 'NOT_RUN', 'needle 命中 %d 次（要恰好 1）' % hits, '', 'yes'))
        continue
    write(rel, text.replace(old, new, 1))
    out, rc = run(kind)
    io.open('/tmp/r242_%s.log' % mid, 'w', encoding='utf-8').write(out)
    write(rel, text)
    restore = (read(rel) == text)
    if not restore:
        dirty += 1
    marker = u'Executed' if kind == 'swift' else u'Ran '
    if marker not in out:
        not_run += 1
        rows.append((mid, 'NOT_RUN', u'插刀后这一卷根本没跑成（rc=%d，没有 %s 行）—— 不许当成 ESCAPED'
                     % (rc, marker), want, 'yes' if restore else 'NO'))
        continue
    reds = red_names(out, kind)
    if not reds:
        escaped += 1
        verdict = 'ESCAPED'
    elif want in reds:
        caught += 1
        verdict = 'CAUGHT'
    else:
        other += 1
        verdict = 'WRONG_CELL'
    rows.append((mid, verdict, ','.join(reds) or '无', want, 'yes' if restore else 'NO'))

print('R242 变异表（对象=两把尺自己，产品 Swift 视图 0 文件）')
print('%-6s %-10s %-46s %-52s %s' % ('刀号', '结论', '红名', '期望那一格', '还原'))
for r in rows:
    print('%-6s %-10s %-46s %-52s %s' % (r[0], r[1], r[2][:46], r[3][:52], r[4]))
print('R242_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d 抓错格=%d RESTORE_CLEAN=%s'
      % (len(ARMS), caught, escaped, not_run, other, 'yes' if dirty == 0 else 'NO'))
sys.exit(0 if (caught == len(ARMS) and escaped == 0 and not_run == 0 and other == 0 and dirty == 0) else 1)
