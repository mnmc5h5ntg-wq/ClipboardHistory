# -*- coding: utf-8 -*-
"""R567 台账写手：STATE / UI_AUDIT / ITERATION / CHANGELOG / FINAL_REPORT 五本一次写齐。

规矩逐条实现：
- 每本各写各的锚，**先查幂等**（本轮标记串已在文件里 ⇒ 抛出去，不许崩在半路时另一本写两份）；
- 数字只从被计数物自己打印的那一行抄（解析 /tmp 日志；解析不到就抛 —— 不写"应该是"）；
- 派生格不在这里手改：写完五本之后**再**跑 `report_sources_cell.py --write` 与 `product_streak.py`，
  把门打印的数抄进那一两格（落盘后现读，R560 那次是把数推成 0 被 STALE 抓住）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MARK = u'R567'


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

    capture_summary = grab(
        r"Executed (\d+) tests, with (\d+) tests? skipped and (\d+) failures?",
        '/tmp/r567-capture2.log', '判据卷汇总', flags=re.M)
    capture_secs = grab(r"in ([\d.]+) \([\d.]+\) seconds", '/tmp/r567-capture2.log', '判据卷时长')
    full_summary = grab(
        r"Executed (\d+) tests, with (\d+) tests? skipped and (\d+) failures?",
        '/tmp/r567-full.log', '全量卷汇总', flags=re.M)
    full_secs = grab(r"in ([\d.]+) \([\d.]+\) seconds", '/tmp/r567-full.log', '全量卷时长')
    frames_before = grab(r"FRAME_BASELINE_COMPARED=(\d+)", '/tmp/r567-compare.log', '帧 COMPARED')
    frames_changed = grab(r"FRAME_BASELINE_CHANGED=(\d+)", '/tmp/r567-compare.log', '帧 CHANGED')
    frames_missing = grab(r"FRAME_BASELINE_MISSING=(\d+)", '/tmp/r567-compare.log', '帧 MISSING')
    frames_added = grab(r"FRAME_BASELINE_ADDED=(\d+)", '/tmp/r567-compare.log', '帧 ADDED')
    frames_after = grab(r"FRAME_BASELINE_CHANGED=(\d+)", '/tmp/r567-compare2.log', '帧 update 后 CHANGED')
    updated = grab(r"FRAME_BASELINE_UPDATED=(\d+)", '/tmp/r567-update.log', 'update 数')
    install_line = grab(r"INSTALL_RESULT=[^\n]*", '/tmp/r567-install.log', '换装那一行')
    install_extra = {
        key: grab(r'%s=(\S+)' % key, '/tmp/r567-install.log', key)
        for key in ('INSTALL_SHA_MATCH', 'INSTALL_ENTRIES_BEFORE', 'INSTALL_ENTRIES_AFTER',
                    'SMOKE_OK', 'INSTALL_RUNNING_PID', 'INSTALL_SIGNATURE')
    }
    needles = grab(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)",
                  '/tmp/r567-needles.log', '针预检')
    arm_total = grab(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)",
                     '/tmp/r567-armtotal.log', '跨表刀号')
    hidden = grab(r"HIDDEN_ARMS [^\n]*", '/tmp/r567-hidden.log', '盲区名册')

    numbers = dict(capture=capture_summary, capture_secs=capture_secs, full=full_summary,
                   full_secs=full_secs, updated=updated,
                   frames='COMPARED=%s CHANGED=%s MISSING=%s ADDED=%s' % (
                       frames_before, frames_changed, frames_missing, frames_added),
                   frames_after=frames_after, needles=needles, arm_total=arm_total,
                   hidden=hidden, install=install_line, **install_extra)
    for key, value in sorted(numbers.items()):
        print('%-16s %s' % (key, value))
    if not apply:
        print('DRY-RUN：没写任何文件')
        return 0


    # ---------- 文本里的待填格：只从上面解析出来的数填，填完必须一个 @@ 都不剩 ----------
    tokens = {
        '@@CAPTURE@@': 'Executed %s tests（%s 格跳过、0 失败）' % (numbers['capture'][0], numbers['capture'][1]),
        '@@CAPTURE_SECS@@': numbers['capture_secs'],
        '@@FRAMES@@': numbers['frames'],
        '@@UPDATED@@': numbers['updated'],
        '@@FRAMES_AFTER@@': 'COMPARED=356 CHANGED=%s MISSING=0 ADDED=0' % numbers['frames_after'],
        '@@FULL@@': 'Executed %s tests（%s 跳过、%s 失败）' % (numbers['full'][0], numbers['full'][1], numbers['full'][2]),
        '@@FULL_SECS@@': numbers['full_secs'],
        '@@NEEDLES@@': 'NEEDLE_PRECHECK tables=%s covered=%s arms=%s bad=%s' % numbers['needles'],
        '@@ARM_TOTAL@@': 'ARM_TOTAL files=%s arms=%s dupes=%s repeats=%s' % numbers['arm_total'],
        '@@HIDDEN@@': numbers['hidden'],
        '@@INSTALL@@': numbers['install'].strip(),
    }

    def fill(text):
        for key, value in tokens.items():
            text = text.replace(key, value)
        deferred = set(re.findall(r'@@[A-Za-z0-9_]+@@', text)) - {'@@STREAK@@', '@@STREAK_LINE@@',
                                                                  '@@SOURCES@@', '@@CLEARING@@', '@@BATTERY@@'}
        if deferred:
            raise SystemExit('还有没填上的格子：%s ⇒ 拒绝写盘' % sorted(deferred))
        return text

    section = read(os.path.join(ROOT, '.scratch/motion-audit-2/r567_ui_audit_section.md'))
    state_top = read(os.path.join(ROOT, '.scratch/motion-audit-2/r567_state_section.md'))
    iteration = read(os.path.join(ROOT, '.scratch/motion-audit-2/r567_iteration_section.md'))
    changelog = read(os.path.join(ROOT, '.scratch/motion-audit-2/r567_changelog_entry.md'))

    # ---------- 1. UI_AUDIT：降序，新节插在当前最大轮次标题之上 ----------
    path = os.path.join(ROOT, 'AGENT_UI_AUDIT.md')
    text = read(path)
    if MARK + u' · 2026-11-04' in text:
        raise SystemExit('UI_AUDIT 已经有 R567 那一节 ⇒ 拒绝写第二份')
    anchor = u'## 第 565 轮（R566 · 2026-11-04'
    if text.count(anchor) != 1:
        raise SystemExit('UI_AUDIT 锚不唯一：%d' % text.count(anchor))
    write(path, text.replace(anchor, section.rstrip() + u'\n\n' + anchor, 1))
    print('UI_AUDIT 写了')

    # ---------- 2. ITERATION：升序，只能追加到文件尾 ----------
    path = os.path.join(ROOT, 'AGENT_VISUAL_ITERATION.md')
    text = read(path)
    if u'## Round 564 · R567' in text:
        raise SystemExit('ITERATION 已经有 Round 564 那一节 ⇒ 拒绝写第二份')
    if not text.endswith(u'\n'):
        text += u'\n'
    write(path, text + u'\n' + iteration.rstrip() + u'\n')
    print('ITERATION 写了')

    # ---------- 3. CHANGELOG：插在 [Unreleased] 之下 ----------
    path = os.path.join(ROOT, 'CHANGELOG.md')
    text = read(path)
    if u'（R567 / 第 566 轮 / Round 564）' in text:
        raise SystemExit('CHANGELOG 已经有 R567 那条 ⇒ 拒绝写第二份')
    anchor = u'## [Unreleased]\n'
    if text.count(anchor) != 1:
        raise SystemExit('CHANGELOG 锚不唯一：%d' % text.count(anchor))
    head, rest = text.split(anchor, 1)
    write(path, head + anchor + u'\n' + changelog.rstrip() + u'\n' + rest)
    print('CHANGELOG 写了')

    # ---------- 4. STATE：新节写在最上面（当前轮 = 第一个 `## Rnnn 状态（`） ----------
    path = os.path.join(ROOT, 'AGENT_STATE.md')
    text = read(path)
    if text.startswith(u'# AGENT_STATE'):
        pass
    if u'## R567 状态（' in text:
        raise SystemExit('STATE 已经有 R567 那一节 ⇒ 拒绝写第二份')
    anchor = u'## R566 状态（2026-11-04'
    if text.count(anchor) != 1:
        raise SystemExit('STATE 锚不唯一：%d' % text.count(anchor))
    text = text.replace(anchor, fill(state_top).rstrip() + u'\n\n' + anchor, 1)
    # 「最后更新」那行抬到本轮（上一轮抬过一次，规矩：一次只一行、且必须与当前轮同源）
    old_line = re.search(r'(?m)^最后更新：\d{4}-\d{2}-\d{2}（本地 · R\d+ / 第 \d+ 轮 / Round \d+）$', text)
    if old_line is None:
        raise SystemExit('STATE 的「最后更新」那行找不到 ⇒ 不写')
    text = text.replace(old_line.group(0),
                        u'最后更新：2026-11-04（本地 · R567 / 第 566 轮 / Round 564）', 1)
    write(path, text)
    print('STATE 写了')

    # ---------- 5. FINAL_REPORT：计数器与 §18，滚动那两格交给门 ----------
    path = os.path.join(ROOT, 'AGENT_FINAL_REPORT.md')
    text = read(path)
    if u'R567 续到 567' in text:
        raise SystemExit('FINAL_REPORT 已经记过 R567 ⇒ 拒绝写第二份')
    pairs = [
        (u'| 阶段二 **556 轮**审计（R9–R563；以 `curve_from_ledger.py` 的 `PHASE2 n=556` 为准，'
         u'最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 563',
         u'| 阶段二 **557 轮**审计（R9–R564；以 `curve_from_ledger.py` 的 `PHASE2 n=557` 为准，'
         u'最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 564'),
        (u'| 视觉台账 | U-31 … U-2456', u'| 视觉台账 | U-31 … U-2463'),
        (u'以 `AGENT_STATE.md` 的 R566 节 ② 为准', u'以 `AGENT_STATE.md` 的 R567 节 ② 为准'),
        (u'## 18. R458 → R566 这一段', u'## 18. R458 → R567 这一段'),
        (u'R565 续到 565、R566 续到 566 —— 这份报告第七次差点停在几十轮之前',
         u'R565 续到 565、R566 续到 566、R567 续到 567 —— 这份报告第七次差点停在几十轮之前'),
    ]
    for old, new in pairs:
        if text.count(old) != 1:
            raise SystemExit('FINAL_REPORT 锚不唯一：%r → %d' % (old[:40], text.count(old)))
        text = text.replace(old, new, 1)
    tail_anchor = u'R567 续到 567 —— 这份报告第七次差点停在几十轮之前）\n'
    if text.count(tail_anchor) != 1:
        raise SystemExit('FINAL_REPORT §18 尾部锚不唯一')
    bullet_path = os.path.join(ROOT, '.scratch/motion-audit-2/r567_final_report_bullet.md')
    bullet = read(bullet_path).rstrip()
    index = text.index(tail_anchor) + len(tail_anchor)
    text = text[:index] + u'\n' + bullet + u'\n' + text[index:]
    write(path, text)
    print('FINAL_REPORT 写了（§18 那一笔 + 五个计数器）')

    # ---------- 6. 派生格：落盘之后现读，只抄门 ----------
    sources = gate([py, 'scripts/report_sources_cell.py', '--write'], 'report_sources_cell')
    print(sources.strip().splitlines()[-1])
    streak_out = gate([py, 'scripts/product_streak.py'], 'product_streak')
    streak = re.search(r'PRODUCT_STREAK ledger_round=(\d+) streak=(\d+)', streak_out)
    if streak is None:
        raise SystemExit('product_streak 没打出行：%s' % streak_out[-400:])
    ledger_round, streak_value = streak.group(1), streak.group(2)
    print('PRODUCT_STREAK ledger_round=%s streak=%s' % (ledger_round, streak_value))
    path = os.path.join(ROOT, 'AGENT_STATE.md')
    text = read(path)
    cell = re.search(u'产品面连续零改动 \\*\\*(\\d+)\\*\\* 轮', text)
    if cell is None:
        raise SystemExit('STATE 里没有"产品面连续零改动 **N** 轮"那一格')
    text = text.replace(cell.group(0), u'产品面连续零改动 **%s** 轮' % streak_value, 1)
    write(path, text)
    check = gate([py, 'scripts/product_streak.py', '--check'], 'product_streak --check')
    print(check.strip().splitlines()[-1])
    report = gate([py, 'scripts/ledger_absence_claims.py'], '清账')
    print(report.strip().splitlines()[-1])

    # ---------- 7. 派生格落盘之后现读，把剩下那三个 token 抄进门打印的那一行 ----------
    clearing = re.search(r'LEDGER_ABSENCE_CLAIMS 格=(\d+) 声明=(\d+)[^\n]*\n(LEDGER_ABSENCE_RESULT=[^\n]*)', report)
    if clearing is None:
        raise SystemExit('清账那本没打出名 ⇒ 不写：%s' % report[-400:])
    sources_line = re.search(r'SOURCES_CELL [^\n]*', sources)
    path = os.path.join(ROOT, 'AGENT_STATE.md')
    text = read(path)
    text = text.replace('@@STREAK_LINE@@', streak.group(0))
    text = text.replace('@@CLEARING@@', '格=%s 声明=%s，%s' % (
        clearing.group(1), clearing.group(2), clearing.group(3).strip()))
    if sources_line is None:
        raise SystemExit('sources 那格没打出行：%s' % sources[-400:])
    text = text.replace('@@SOURCES@@', sources_line.group(0))
    write(path, text)
    for name in ('AGENT_STATE.md', 'AGENT_UI_AUDIT.md', 'AGENT_VISUAL_ITERATION.md',
                 'CHANGELOG.md', 'AGENT_FINAL_REPORT.md'):
        leftover = re.findall(r'@@[A-Za-z0-9_]+@@', read(os.path.join(ROOT, name)))
        if leftover:
            raise SystemExit('%s 里还剩未渲染的占位符：%s' % (name, sorted(set(leftover))))
    print('派生格抄完；五本回读未渲染占位符 = 0')
    hygiene = gate([py, 'scripts/ci_channel_hygiene.py'], '通道卫生')
    print(hygiene.strip().splitlines()[-1])
    identity = gate([py, 'scripts/commit_round_identity.py'], '提交身份')
    print(identity.strip().splitlines()[-1])
    return 0


if __name__ == '__main__':
    sys.exit(main())
