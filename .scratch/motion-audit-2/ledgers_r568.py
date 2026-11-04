# -*- coding: utf-8 -*-
"""R568 台账写手：STATE / UI_AUDIT / ITERATION / CHANGELOG / FINAL_REPORT 五本 + BACKLOG / DECISIONS 两本追加。

规矩逐条实现（R567 那一版的四处自伤都在这里钉住了）：
- **任何插入台账的文本都过同一趟 fill**（不是只 fill STATE），返回前把七本各回读一遍 token = 0；
- 每本先查**幂等**（本轮标记串已在文件里 ⇒ 抛出去），崩在半路不会让另一本写两份；
- 数字只从被计数物自己打印的那一行抄（解析 /tmp 日志；解析不到就抛，不写"应该是"）；
- 派生格不在这里手改：写完七本之后**再**跑 `report_sources_cell.py --write` 与 `product_streak.py`，
  把门打印的数抄进那一两格（落盘后现读）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRATCH = os.path.join(ROOT, '.scratch', 'motion-audit-2')
MARK = u'R568'
LOGS = {
    'capture': '/tmp/r568/capture2.log',
    'full': '/tmp/r568/full.log',
    'compare': '/tmp/r568/compare2.log',
    'needles': '/tmp/r568/needles.log',
    'armtotal': '/tmp/r568/armtotal.log',
    'hidden': '/tmp/r568/hidden.log',
    'install': '/tmp/r568/install.log',
}


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
    proc = subprocess.Popen(args, cwd=ROOT, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
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
                     LOGS['armtotal'], '跨表刀号')
    hidden = grab(r"HIDDEN_ARMS [^\n]*", LOGS['hidden'], '盲区名册')
    install_line = grab(r"INSTALL_RESULT=[^\n]*", LOGS['install'], '换装那一行')

    numbers = dict(
        CAPTURE='Executed %s tests（%s 格跳过、0 失败）' % (capture[0], capture[1]),
        CAPTURE_SECS=capture_secs,
        FULL='Executed %s tests（%s 跳过、%s 失败）' % (full[0], full[1], full[2]),
        FULL_SECS=full_secs,
        FRAMES=frames,
        NEEDLES='NEEDLE_PRECHECK tables=%s covered=%s arms=%s bad=%s' % needles,
        ARM_TOTAL='ARM_TOTAL files=%s arms=%s dupes=%s repeats=%s' % arm_total,
        HIDDEN=hidden.strip(),
        INSTALL=install_line.strip(),
    )
    for key, value in sorted(numbers.items()):
        print('%-14s %s' % (key, value))
    deferred = ['STREAK_LINE', 'SOURCES', 'CLEARING', 'BATTERY']
    tokens = dict(('@@%s@@' % key, value) for key, value in numbers.items())
    for key in deferred:
        tokens['@@%s@@' % key] = '@@%s@@' % key        # 派生格留到第 7 步，先允许穿过 fill
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

    section_ui = fill(read(os.path.join(SCRATCH, 'r568_ui_audit_section.md')))
    section_state = fill(read(os.path.join(SCRATCH, 'r568_state_section.md')))
    section_iter = fill(read(os.path.join(SCRATCH, 'r568_iteration_section.md')))
    entry_changelog = fill(read(os.path.join(SCRATCH, 'r568_changelog_entry.md')))
    bullet_report = fill(read(os.path.join(SCRATCH, 'r568_final_report_bullet.md')))
    append_backlog = fill(read(os.path.join(SCRATCH, 'r568_backlog_append.md')))
    append_decisions = fill(read(os.path.join(SCRATCH, 'r568_decisions_append.md')))

    # ---------- 1. UI_AUDIT：降序，新节插在当前最大轮次标题之上 ----------
    path = os.path.join(ROOT, 'AGENT_UI_AUDIT.md')
    text = read(path)
    if u'## 第 567 轮（R568' in text:
        raise SystemExit('UI_AUDIT 已经有 R568 那一节 ⇒ 拒绝写第二份')
    anchor = u'## 第 566 轮（R567 · 2026-11-04'
    if text.count(anchor) != 1:
        raise SystemExit('UI_AUDIT 锚不唯一：%d' % text.count(anchor))
    write(path, text.replace(anchor, section_ui.rstrip() + u'\n\n' + anchor, 1))
    print('UI_AUDIT 写了')

    # ---------- 2. ITERATION：升序，只能追加到文件尾 ----------
    path = os.path.join(ROOT, 'AGENT_VISUAL_ITERATION.md')
    text = read(path)
    if u'## Round 565 · R568' in text:
        raise SystemExit('ITERATION 已经有 Round 565 那一节 ⇒ 拒绝写第二份')
    if not text.endswith(u'\n'):
        text += u'\n'
    write(path, text + u'\n' + section_iter.rstrip() + u'\n')
    print('ITERATION 写了')

    # ---------- 3. CHANGELOG：插在 [Unreleased] 之下 ----------
    path = os.path.join(ROOT, 'CHANGELOG.md')
    text = read(path)
    if u'（R568 / 第 567 轮 / Round 565）' in text:
        raise SystemExit('CHANGELOG 已经有 R568 那条 ⇒ 拒绝写第二份')
    anchor = u'## [Unreleased]\n'
    if text.count(anchor) != 1:
        raise SystemExit('CHANGELOG 锚不唯一：%d' % text.count(anchor))
    head, rest = text.split(anchor, 1)
    write(path, head + anchor + u'\n' + entry_changelog.rstrip() + u'\n' + rest)
    print('CHANGELOG 写了')

    # ---------- 4. STATE：新节写在最上面，并把「最后更新」抬到本轮 ----------
    path = os.path.join(ROOT, 'AGENT_STATE.md')
    text = read(path)
    if u'## R568 状态（' in text:
        raise SystemExit('STATE 已经有 R568 那一节 ⇒ 拒绝写第二份')
    anchor = u'## R567 状态（2026-11-04'
    if text.count(anchor) != 1:
        raise SystemExit('STATE 锚不唯一：%d' % text.count(anchor))
    text = text.replace(anchor, section_state.rstrip() + u'\n\n' + anchor, 1)
    old_line = re.search(r'(?m)^最后更新：\d{4}-\d{2}-\d{2}（本地 · R\d+ / 第 \d+ 轮 / Round \d+）$', text)
    if old_line is None:
        raise SystemExit('STATE 的「最后更新」那行找不到 ⇒ 不写')
    text = text.replace(old_line.group(0),
                        u'最后更新：2026-11-04（本地 · R568 / 第 567 轮 / Round 565）', 1)
    write(path, text)
    print('STATE 写了（含「最后更新」抬到 R568 —— 这一抬就是 test_round_batch_consistency 三轮窗口的入口）')

    # ---------- 5. FINAL_REPORT：五个计数器 + §18 那一笔 ----------
    path = os.path.join(ROOT, 'AGENT_FINAL_REPORT.md')
    text = read(path)
    if u'R568 续到 568' in text:
        raise SystemExit('FINAL_REPORT 已经记过 R568 ⇒ 拒绝写第二份')
    pairs = [
        (u'| 阶段二 **557 轮**审计（R9–R564；以 `curve_from_ledger.py` 的 `PHASE2 n=557` 为准，'
         u'最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 564',
         u'| 阶段二 **558 轮**审计（R9–R565；以 `curve_from_ledger.py` 的 `PHASE2 n=558` 为准，'
         u'最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 565'),
        (u'| 视觉台账 | U-31 … U-2463', u'| 视觉台账 | U-31 … U-2470'),
        (u'以 `AGENT_STATE.md` 的 R567 节 ② 为准', u'以 `AGENT_STATE.md` 的 R568 节 ② 为准'),
        (u'## 18. R458 → R567 这一段', u'## 18. R458 → R568 这一段'),
        (u'R567 续到 567 —— 这份报告第七次差点停在几十轮之前',
         u'R567 续到 567、R568 续到 568 —— 这份报告第七次差点停在几十轮之前'),
    ]
    for old, new in pairs:
        if text.count(old) != 1:
            raise SystemExit('FINAL_REPORT 锚不唯一：%r → %d' % (old[:40], text.count(old)))
        text = text.replace(old, new, 1)
    tail_anchor = u'R568 续到 568 —— 这份报告第七次差点停在几十轮之前）\n'
    if text.count(tail_anchor) != 1:
        raise SystemExit('FINAL_REPORT §18 尾部锚不唯一')
    index = text.index(tail_anchor) + len(tail_anchor)
    text = text[:index] + u'\n' + bullet_report.rstrip() + u'\n' + text[index:]
    write(path, text)
    print('FINAL_REPORT 写了（§18 那一笔 + 五个计数器）')

    # ---------- 6. BACKLOG / DECISIONS：追加，各带幂等守卫 ----------
    path = os.path.join(ROOT, 'AGENT_BACKLOG.md')
    text = read(path)
    if u'**646. ' in text and u'（R568 现读并新开' in text:
        raise SystemExit('BACKLOG 已经有 R568 那几条 ⇒ 拒绝写第二份')
    write(path, text.rstrip() + u'\n' + append_backlog)
    print('BACKLOG 追加了（646 / 647 / 431 追记 / 639 追记 / 640 追记四 / 643 追记）')

    path = os.path.join(ROOT, 'AGENT_DECISIONS.md')
    text = read(path)
    if u'## D-568（R568' in text:
        raise SystemExit('DECISIONS 已经有 D-568 ⇒ 拒绝写第二份')
    write(path, text.rstrip() + u'\n' + append_decisions)
    print('DECISIONS 追加了 D-568')

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
    text = text.replace('@@CLEARING@@', '格=%s 声明=%s，%s' % (
        clearing.group(1), clearing.group(2), clearing.group(3).strip()))
    text = text.replace('@@SOURCES@@', sources_line.group(0))
    write(path, text)

    # ---------- 8. 七本回读：未渲染占位符必须 0（R567 那起的同一形状） ----------
    # 唯一允许活着的 token 是 @@BATTERY@@：电池**必须**排在台账之后（D-333 那条），
    # 它的数由 `patch_r568_battery.py` 在跑完电池之后补，那一支会要求七本全 0。
    for name in ('AGENT_STATE.md', 'AGENT_UI_AUDIT.md', 'AGENT_VISUAL_ITERATION.md',
                 'CHANGELOG.md', 'AGENT_FINAL_REPORT.md', 'AGENT_BACKLOG.md', 'AGENT_DECISIONS.md'):
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
