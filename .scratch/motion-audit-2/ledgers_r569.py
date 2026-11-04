# -*- coding: utf-8 -*-
"""R569 台账写手：五本按锚插入 + BACKLOG / DECISIONS 追加 + 派生格落盘后现读。

沿用 R567/R568 那两版的规矩，并把它们抓过的自伤逐条实现：
- **任何插入台账的文本都过同一趟 fill**（不是只 fill STATE），返回前七本各回读一遍 token = 0；
  唯一允许活着的是 @@BATTERY@@（电池必须排在台账之后）。
- 每本先查**幂等**；数字只从被计数物自己打印的那一行抄，解析不到就抛。
- **正文里不出现守卫自己搜的字面串**（本轮写 `CHROME_METRIC_GUARD` 那几句时特意把 token 拆成中文）。
- 本轮产品 0 文件 ⇒ 不跑 `install_local.sh`（账里写具名 `SKIP_INSTALL=no-product-change`）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRATCH = os.path.join(ROOT, '.scratch', 'motion-audit-2')
LOGS = {
    'capture': '/tmp/r569/capture.log',
    'full': '/tmp/r569/full.log',
    'compare': '/tmp/r569/compare.log',
    'needles': '/tmp/r569/needles.log',
    'hidden': '/tmp/r569/hidden.log',
}
BOOKS = ('AGENT_STATE.md', 'AGENT_UI_AUDIT.md', 'AGENT_VISUAL_ITERATION.md',
         'CHANGELOG.md', 'AGENT_FINAL_REPORT.md', 'AGENT_BACKLOG.md', 'AGENT_DECISIONS.md')


def read(path):
    with io.open(path, encoding='utf-8') as handle:
        return handle.read()


def write(path, text):
    with io.open(path, 'w', encoding='utf-8') as handle:
        handle.write(text)


def grab(pattern, path, label, flags=0, last=True):
    if not os.path.exists(path):
        raise SystemExit('日志不在盘上：%s（%s）⇒ 拒绝写账' % (path, label))
    found = re.findall(pattern, read(path), flags)
    if not found:
        raise SystemExit('%s 没在 %s 里找到（模式 %s）⇒ 拒绝写账' % (label, path, pattern))
    return found[-1] if last else found[0]


def gate(args, label):
    proc = subprocess.Popen(args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.communicate()[0].decode('utf-8', 'replace')
    if proc.returncode != 0:
        raise SystemExit('%s 退出码 %d：\n%s' % (label, proc.returncode, out[-1200:]))
    return out


def main():
    apply = '--apply' in sys.argv
    py = sys.executable

    capture = grab(r"Executed (\d+) tests, with (\d+) tests? skipped and (\d+) failures?",
                   LOGS['capture'], '判据卷汇总', flags=re.M)
    capture_secs = grab(r"in ([\d.]+) \([\d.]+\) seconds", LOGS['capture'], '判据卷时长')
    full = grab(r"Executed (\d+) tests, with (\d+) tests? skipped and (\d+) failures?",
                LOGS['full'], '全量卷汇总', flags=re.M)
    full_secs = grab(r"in ([\d.]+) \([\d.]+\) seconds", LOGS['full'], '全量卷时长')
    frames = 'COMPARED=%s CHANGED=%s MISSING=%s ADDED=%s' % (
        grab(r"FRAME_BASELINE_COMPARED=(\d+)", LOGS['compare'], '帧 COMPARED'),
        grab(r"FRAME_BASELINE_CHANGED=(\d+)", LOGS['compare'], '帧 CHANGED'),
        grab(r"FRAME_BASELINE_MISSING=(\d+)", LOGS['compare'], '帧 MISSING'),
        grab(r"FRAME_BASELINE_ADDED=(\d+)", LOGS['compare'], '帧 ADDED'))
    needles = grab(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)",
                   LOGS['needles'], '针预检')
    arm_total = grab(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)",
                     LOGS['needles'], '跨表刀号')
    hidden = grab(r"HIDDEN_ARMS [^\n]*", LOGS['hidden'], '盲区名册')

    numbers = dict(
        CAPTURE='Executed %s tests（%s 格跳过、%s 失败）' % (capture[0], capture[1], capture[2]),
        CAPTURE_SECS=capture_secs,
        FULL='Executed %s tests（%s 跳过、%s 失败）' % (full[0], full[1], full[2]),
        FULL_SECS=full_secs,
        FRAMES=frames,
        NEEDLES='NEEDLE_PRECHECK tables=%s covered=%s arms=%s bad=%s' % needles,
        ARM_TOTAL='ARM_TOTAL files=%s arms=%s dupes=%s repeats=%s' % arm_total,
        HIDDEN=hidden.strip(),
    )
    for key, value in sorted(numbers.items()):
        print('%-14s %s' % (key, value))
    deferred = ['STREAK', 'STREAK_LINE', 'SOURCES', 'CLEARING', 'BATTERY']
    tokens = dict(('@@%s@@' % k, v) for k, v in numbers.items())
    for key in deferred:
        tokens['@@%s@@' % key] = '@@%s@@' % key
    if not apply:
        print('DRY-RUN：没写任何文件')
        return 0

    def fill(text):
        for key, value in tokens.items():
            text = text.replace(key, value)
        left = set(re.findall(r'@@[A-Za-z0-9_]+@@', text)) - set('@@%s@@' % k for k in deferred)
        if left:
            raise SystemExit('还有没填上的格子：%s ⇒ 拒绝写盘' % sorted(left))
        return text

    section_ui = fill(read(os.path.join(SCRATCH, 'r569_ui_audit_section.md')))
    section_state = fill(read(os.path.join(SCRATCH, 'r569_state_section.md')))
    section_iter = fill(read(os.path.join(SCRATCH, 'r569_iteration_section.md')))
    entry_changelog = fill(read(os.path.join(SCRATCH, 'r569_changelog_entry.md')))
    bullet_report = fill(read(os.path.join(SCRATCH, 'r569_final_report_bullet.md')))
    append_backlog = fill(read(os.path.join(SCRATCH, 'r569_backlog_append.md')))
    append_decisions = fill(read(os.path.join(SCRATCH, 'r569_decisions_append.md')))

    # ---------- 1. UI_AUDIT：降序，插在当前最大轮次标题之上 ----------
    path = os.path.join(ROOT, 'AGENT_UI_AUDIT.md')
    text = read(path)
    if u'## 第 568 轮（R569' in text:
        raise SystemExit('UI_AUDIT 已经有 R569 那一节 ⇒ 拒绝写第二份')
    anchor = u'## 第 567 轮（R568 · 2026-11-04'
    if text.count(anchor) != 1:
        raise SystemExit('UI_AUDIT 锚不唯一：%d' % text.count(anchor))
    write(path, text.replace(anchor, section_ui.rstrip() + u'\n\n' + anchor, 1))
    print('UI_AUDIT 写了')

    # ---------- 2. ITERATION：升序，只能追加到文件尾 ----------
    path = os.path.join(ROOT, 'AGENT_VISUAL_ITERATION.md')
    text = read(path)
    if u'## Round 566 · R569' in text:
        raise SystemExit('ITERATION 已经有 Round 566 那一节 ⇒ 拒绝写第二份')
    if not text.endswith(u'\n'):
        text += u'\n'
    write(path, text + u'\n' + section_iter.rstrip() + u'\n')
    print('ITERATION 写了')

    # ---------- 3. CHANGELOG：插在 [Unreleased] 之下 ----------
    path = os.path.join(ROOT, 'CHANGELOG.md')
    text = read(path)
    if u'（R569 / 第 568 轮 / Round 566）' in text:
        raise SystemExit('CHANGELOG 已经有 R569 那条 ⇒ 拒绝写第二份')
    anchor = u'## [Unreleased]\n'
    if text.count(anchor) != 1:
        raise SystemExit('CHANGELOG 锚不唯一：%d' % text.count(anchor))
    head, rest = text.split(anchor, 1)
    write(path, head + anchor + u'\n' + entry_changelog.rstrip() + u'\n' + rest)
    print('CHANGELOG 写了')

    # ---------- 4. STATE：新节写在最上面 + 抬「最后更新」 ----------
    path = os.path.join(ROOT, 'AGENT_STATE.md')
    text = read(path)
    if u'## R569 状态（' in text:
        raise SystemExit('STATE 已经有 R569 那一节 ⇒ 拒绝写第二份')
    anchor = u'## R568 状态（2026-11-04'
    if text.count(anchor) != 1:
        raise SystemExit('STATE 锚不唯一：%d' % text.count(anchor))
    text = text.replace(anchor, section_state.rstrip() + u'\n\n' + anchor, 1)
    old_line = re.search(r'(?m)^最后更新：\d{4}-\d{2}-\d{2}（本地 · R\d+ / 第 \d+ 轮 / Round \d+）$', text)
    if old_line is None:
        raise SystemExit('STATE 的「最后更新」那行找不到 ⇒ 不写')
    text = text.replace(old_line.group(0),
                        u'最后更新：2026-11-04（本地 · R569 / 第 568 轮 / Round 566）', 1)
    write(path, text)
    print('STATE 写了（含「最后更新」抬到 R569）')

    # ---------- 5. FINAL_REPORT：五个计数器 + §18 那一笔 ----------
    path = os.path.join(ROOT, 'AGENT_FINAL_REPORT.md')
    text = read(path)
    if u'R569 续到 569' in text:
        raise SystemExit('FINAL_REPORT 已经记过 R569 ⇒ 拒绝写第二份')
    pairs = [
        (u'阶段二 **558 轮**审计（R9–R565；以 `curve_from_ledger.py` 的 `PHASE2 n=558` 为准，'
         u'最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 565',
         u'阶段二 **559 轮**审计（R9–R566；以 `curve_from_ledger.py` 的 `PHASE2 n=559` 为准，'
         u'最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 566'),
        (u'| 视觉台账 | U-31 … U-2470', u'| 视觉台账 | U-31 … U-2477'),
        (u'以 `AGENT_STATE.md` 的 R568 节 ② 为准', u'以 `AGENT_STATE.md` 的 R569 节 ② 为准'),
        (u'## 18. R458 → R568 这一段', u'## 18. R458 → R569 这一段'),
        (u'R568 续到 568 —— 这份报告第七次差点停在几十轮之前',
         u'R568 续到 568、R569 续到 569 —— 这份报告第七次差点停在几十轮之前'),
    ]
    for old, new in pairs:
        if text.count(old) != 1:
            raise SystemExit('FINAL_REPORT 锚不唯一：%r → %d' % (old[:40], text.count(old)))
        text = text.replace(old, new, 1)
    tail_anchor = u'R569 续到 569 —— 这份报告第七次差点停在几十轮之前）\n'
    if text.count(tail_anchor) != 1:
        raise SystemExit('FINAL_REPORT §18 尾部锚不唯一')
    index = text.index(tail_anchor) + len(tail_anchor)
    text = text[:index] + u'\n' + bullet_report.rstrip() + u'\n' + text[index:]
    write(path, text)
    print('FINAL_REPORT 写了（§18 那一笔 + 五个计数器）')

    # ---------- 6. BACKLOG / DECISIONS：追加，各带幂等守卫 ----------
    path = os.path.join(ROOT, 'AGENT_BACKLOG.md')
    text = read(path)
    if u'**648. ' in text and u'（R569 现读并新开' in text:
        raise SystemExit('BACKLOG 已经有 R569 那几条 ⇒ 拒绝写第二份')
    write(path, text.rstrip() + u'\n' + append_backlog)
    print('BACKLOG 追加了（645 追记 / 646 追记 / 新开 648 / 639 追记 / 640 追记五 / 643 追记）')

    path = os.path.join(ROOT, 'AGENT_DECISIONS.md')
    text = read(path)
    if u'## D-569（R569' in text:
        raise SystemExit('DECISIONS 已经有 D-569 ⇒ 拒绝写第二份')
    write(path, text.rstrip() + u'\n' + append_decisions)
    print('DECISIONS 追加了 D-569')

    # ---------- 7. 派生格：落盘之后现读，只抄门打印的那一行 ----------
    sources = gate([py, 'scripts/report_sources_cell.py', '--write'], 'report_sources_cell')
    print(sources.strip().splitlines()[-1])
    streak_out = gate([py, 'scripts/product_streak.py'], 'product_streak')
    streak = re.search(r'PRODUCT_STREAK ledger_round=(\d+) streak=(\d+)[^\n]*', streak_out)
    if streak is None:
        raise SystemExit('product_streak 没打出行：%s' % streak_out[-400:])
    print(streak.group(0))
    path = os.path.join(ROOT, 'AGENT_STATE.md')
    text = read(path)
    cell = re.search(u'产品面连续零改动 \\*\\*(\\d+)\\*\\* 轮', text)
    if cell is None:
        raise SystemExit('STATE 里没有"产品面连续零改动 **N** 轮"那一格')
    text = text.replace(cell.group(0), u'产品面连续零改动 **%s** 轮' % streak.group(2), 1)
    write(path, text)
    check = gate([py, 'scripts/product_streak.py', '--check'], 'product_streak --check')
    print(check.strip().splitlines()[-1])
    report = gate([py, 'scripts/ledger_absence_claims.py'], '清账')
    print(report.strip().splitlines()[-1])

    clearing = re.search(r'LEDGER_ABSENCE_CLAIMS 格=(\d+) 声明=(\d+)[^\n]*\n(LEDGER_ABSENCE_RESULT=[^\n]*)', report)
    if clearing is None:
        raise SystemExit('清账那本没打出名 ⇒ 不写：%s' % report[-400:])
    sources_line = re.search(r'SOURCES_CELL [^\n]*', sources)
    if sources_line is None:
        raise SystemExit('sources 那格没打出行：%s' % sources[-400:])
    text = read(path)
    text = text.replace('@@STREAK_LINE@@', streak.group(0))
    text = text.replace('@@STREAK@@', streak.group(2))
    text = text.replace('@@CLEARING@@', '格=%s 声明=%s，%s' % (
        clearing.group(1), clearing.group(2), clearing.group(3).strip()))
    text = text.replace('@@SOURCES@@', sources_line.group(0))
    write(path, text)

    # ---------- 8. 七本回读：除 @@BATTERY@@ 之外不许有未渲染占位符 ----------
    for name in BOOKS:
        leftover = set(re.findall(r'@@[A-Za-z0-9_]+@@', read(os.path.join(ROOT, name)))) - {u'@@BATTERY@@'}
        if leftover:
            raise SystemExit('%s 里还剩未渲染的占位符：%s' % (name, sorted(leftover)))
    print('七本回读：除 @@BATTERY@@（电池排在台账之后）之外未渲染占位符 = 0')

    hygiene = gate([py, 'scripts/ci_channel_hygiene.py'], '通道卫生')
    print(hygiene.strip().splitlines()[-1])
    identity = gate([py, 'scripts/commit_round_identity.py'], '提交身份')
    print(identity.strip().splitlines()[-1])
    return 0


if __name__ == '__main__':
    sys.exit(main())
