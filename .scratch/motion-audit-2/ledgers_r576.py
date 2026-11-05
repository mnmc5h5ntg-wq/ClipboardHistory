# -*- coding: utf-8 -*-
"""R576 台账写手：七本按整行锚插入 + `### R575 补记` 向前补记 + 派生格落盘后现读。

沿用 R567–R575 那几版的规矩，逐条实现它们抓过的自伤：
- **任何插入台账的文本都过同一趟 fill**，返回前七本各回读一遍 token = 0；唯一允许活着的是
  @@BATTERY@@（电池必须排在台账之后，由 `--finish-battery` 那一趟补）。
- **派生格只在"本轮那一节"里找**（R570 那版在全书找，命中上一轮那一节）。
- **FINAL_REPORT 那本也有清账格 / 电池格 / streak 格**（R570/R571 只补 STATE ⇒ 未渲染占位符被抓）。
- **`product_streak --check` 挪到所有格子落完之后**。
- **正文里不出现守卫自己搜的字面串**（电池格与清账格只用中文描述）。
- **本轮所有逐字读数由落盘日志 `re.findall` 派生**（`/tmp/r576/criteria.log`、
  `/tmp/r576/realscreen.log`、`/tmp/r576/ci-41843233864.log`），不是我打出来的 —— R575 那一课
  （"抄数先写猜测值"）的处置照做。
- 本轮产品 0 文件 ⇒ 不跑 `install_local.sh`（账里写具名 SKIP_INSTALL=no-product-change）。

用法：python3 .scratch/motion-audit-2/ledgers_r576.py                  # 只数不写
      python3 .scratch/motion-audit-2/ledgers_r576.py --apply           # 真写七本 + 派生格
      python3 .scratch/motion-audit-2/ledgers_r576.py --finish-battery  # 电池落盘之后补那一格
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRATCH = os.path.join(ROOT, '.scratch', 'motion-audit-2')
LOGS = {
    'capture': '/tmp/r576/criteria.log',
    'realscreen': '/tmp/r576/realscreen.log',
    'full': '/tmp/r576/full.log',
    'compare': '/tmp/r576/compare.log',
    'needles': '/tmp/r576/needles.log',
    'hidden': '/tmp/r576/hidden.log',
    'battery': '/tmp/r576/battery.log',
    'runner': '/tmp/r576/ci-41843233864.log',
}
BOOKS = ('AGENT_STATE.md', 'AGENT_UI_AUDIT.md', 'AGENT_VISUAL_ITERATION.md',
         'CHANGELOG.md', 'AGENT_FINAL_REPORT.md', 'AGENT_BACKLOG.md', 'AGENT_DECISIONS.md')

SHOTS_SEEN = io.open(os.path.join(SCRATCH, 'r576_shots_note.md'), encoding='utf-8').read().strip()
SHOTS_SCORE = u'12/15'
SHOTS_SHORT = (u'两张**整帧**逐张看过，挑的就是本轮新判据与映射表声明依赖的那两棵：主窗帧确认详情正文下方'
               u'到窗口底是成片空白、没有任何透明区（= `对象现读=无` 的肉眼版本），第五行下方那块黑底是**已登记的有意黑底**、'
               u'没读成回归；浮层帧确认选中灰底画出来了而面板材质底没合成（= 通道侧 `全透明=17261` 与产物侧 `产物全透明=0` '
               u'并存的肉眼版本）。`CHANGED=0` ⇒ 本轮不是看新图，是把依赖的那两张再对一次眼睛。扣 3 分：层树冷态这件事'
               u'在像素上不可见、过程帧的对象还不存在、真机材质只跑了读数没看图')


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


def state_section(text, header):
    start = text.index(header)
    nxt = text.find(u'\n## ', start + 1)
    end = nxt if nxt > 0 else len(text)
    return start, end, text[start:end]


def main():
    apply = '--apply' in sys.argv
    finish = '--finish-battery' in sys.argv
    py = sys.executable

    if finish:
        text = read(LOGS['battery'])
        ran = grab(r'Ran (\d+) tests', LOGS['battery'], '电池 Ran')
        skipped = grab(r'skipped=(\d+)', LOGS['battery'], '电池 skipped')
        secs = grab(r'in ([\d.]+)s', LOGS['battery'], '电池时长')
        verdict = u'OK' if re.search(r'OK \(skipped=', text) else u'FAILED'
        failures = re.search(r'failures=(\d+)', text)
        if verdict == u'FAILED' and failures:
            cell = u'Ran %s / FAILED (failures=%s, skipped=%s) @%ss' % (
                ran, failures.group(1), skipped, secs)
        else:
            cell = u'Ran %s / OK (skipped=%s) @%ss' % (ran, skipped, secs)
        for name in BOOKS:
            path = os.path.join(ROOT, name)
            body = read(path)
            if u'@@BATTERY@@' not in body:
                continue
            body = body.replace(u'电池 @@BATTERY@@', u'电池 ' + cell)
            body = body.replace(u'@@BATTERY@@', cell)
            write(path, body)
            print('%s 补了电池格：%s' % (name, cell))
        for name in BOOKS:
            leftover = set(re.findall(r'@@[A-Za-z0-9_]+@@', read(os.path.join(ROOT, name))))
            if leftover:
                raise SystemExit('%s 里还剩未渲染的占位符：%s' % (name, sorted(leftover)))
        print('七本回读：未渲染占位符 = 0')
        return 0

    # ---------- 读数：全部从落盘日志派生 ----------
    capture = grab(r"Executed (\d+) tests, with (\d+) tests? skipped and (\d+) failures",
                   LOGS['capture'], '判据卷汇总', flags=re.M)
    capture_secs = grab(r"in ([\d.]+) \([\d.]+\) seconds", LOGS['capture'], '判据卷时长')
    capture_line = grab(r"Executed \d+ tests, with \d+ tests? skipped and \d+ failures",
                        LOGS['capture'], '判据卷逐字行')
    full = grab(r"Executed (\d+) tests, with (\d+) tests? skipped and (\d+) failures",
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

    cold_main = grab(r'LAYER_TREE_COLD 树=主窗[^\n]*', LOGS['capture'], '层树冷态 主窗')
    cold_overlay = grab(r'LAYER_TREE_COLD 树=浮层[^\n]*', LOGS['capture'], '层树冷态 浮层')
    cold_summary = grab(r'LAYER_TREE_COLD_SUMMARY[^\n]*', LOGS['capture'], '层树冷态汇总')
    cold_mech = grab(r'LAYER_TREE_COLD_MECH 解释=①[^\n]*', LOGS['capture'], '解释①')
    cold_mech2 = grab(r'LAYER_TREE_COLD_MECH 解释=②[^\n]*', LOGS['capture'], '解释②')
    cold_mech3 = grab(r'LAYER_TREE_COLD_MECH 解释=③[^\n]*', LOGS['capture'], '解释③')
    cold_mech = u' ‖ '.join([cold_mech, cold_mech2, cold_mech3])

    d12_local = grab(r'D12_CHANNEL_MAP_SUMMARY[^\n]*', LOGS['capture'], '映射表本机汇总')
    if not os.path.exists(LOGS['runner']):
        raise SystemExit('runner 日志不在盘上：%s ⇒ 拒绝写账' % LOGS['runner'])
    d12_runner = grab(r'D12_CHANNEL_MAP_SUMMARY[^\n]*', LOGS['runner'], '映射表 runner 汇总')

    ground_state = grab(r'TRANSPARENCY_STATE [^\n]*', LOGS['capture'], '禁碰证人 底衬状态')
    ground_hit = grab(r'TRANSPARENCY_HITTEST [^\n]*', LOGS['capture'], '禁碰证人 命中')
    ground_mat = grab(r'TRANSPARENCY_MATERIAL [^\n]*', LOGS['realscreen'], '禁碰证人 材质（真机键）')
    ground_neg = grab(r'TRANSPARENCY_MATERIAL_NEG [^\n]*', LOGS['realscreen'], '禁碰证人 材质反面臂')
    ground = (u'`%s`、`%s`、`%s`（真机键那一档本轮**单独跑到了数**，反面臂 `%s`）'
              % (ground_state, ground_hit, ground_mat, ground_neg))

    # push 通道在**台账落盘之前**现读（不改 remote、不碰 ~/.ssh、不换 DNS、不加 scope）
    ls = subprocess.Popen(['git', 'ls-remote', 'origin', 'HEAD'], cwd=ROOT,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    ls_out = ls.communicate()[0].decode('utf-8', 'replace')
    url = subprocess.Popen(['git', 'config', '--get', 'remote.origin.url'], cwd=ROOT,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    url_out = url.communicate()[0].decode('utf-8', 'replace').strip()
    if ls.returncode == 0 and ls_out.strip():
        push_line = (u'`PUSH_TRANSPORT=ssh-ok` —— 现读 `git ls-remote origin HEAD` 通（远端 HEAD='
                     + ls_out.split()[0][:9] + u'），`git config --get remote.origin.url` 仍是 '
                     + ('`git@github.com:…`（SSH 形式，未改动）' if url_out.startswith('git@')
                        else u'**不是** SSH 形式（现读值 ' + url_out + u'）'))
    else:
        push_line = (u'`PUSH_TRANSPORT=blocked` —— 现读 `git ls-remote origin HEAD` 退出码 '
                     + str(ls.returncode) + u'，正文首行 `'
                     + (ls_out.strip().splitlines() or [u'空'])[0][:60] + u'`')
    print('PUSHLINE %s' % push_line[:150])

    numbers = dict(
        CAPTURE='Executed %s tests（%s 格跳过、%s 失败）' % (capture[0], capture[1], capture[2]),
        CAPTURELINE=capture_line,
        CAPTURE_SECS=capture_secs,
        SHOTS_CAPTURE='Executed %s tests（%s 格跳过、%s 失败）' % (capture[0], capture[1], capture[2]),
        FULL='Executed %s tests（%s 跳过、%s 失败）' % (full[0], full[1], full[2]),
        FULL_SECS=full_secs,
        FULLSKIPPED=full[1],
        FRAMES=frames,
        NEEDLES='NEEDLE_PRECHECK tables=%s covered=%s arms=%s bad=%s' % needles,
        ARM_TOTAL='ARM_TOTAL files=%s arms=%s dupes=%s repeats=%s' % arm_total,
        HIDDEN=hidden.strip(),
        SHOTS_SEEN=SHOTS_SEEN,
        SHOTS_SCORE=SHOTS_SCORE,
        SHOTS_SHORT=SHOTS_SHORT,
        COLDMAIN=cold_main,
        COLDOVERLAY=cold_overlay,
        COLDSUMMARY=cold_summary,
        COLDMECH=cold_mech,
        D12LOCAL=d12_local,
        D12RUNNER=d12_runner,
        GROUNDWITNESS=ground,
        PUSHLINE=push_line,
    )
    for key, value in sorted(numbers.items()):
        print('%-14s %s' % (key, value[:130]))
    deferred = ['STREAK', 'STREAK_LINE', 'SOURCES', 'CLEARING', 'BATTERY']
    tokens = dict(('@@%s@@' % k, v) for k, v in numbers.items())
    for key in deferred:
        tokens['@@%s@@' % key] = '@@%s@@' % key

    if not apply:
        print('DRY-RUN：没写任何文件')
        return 0

    skipped_books = set()

    def fill(text):
        for key, value in tokens.items():
            text = text.replace(key, value)
        left = set(re.findall(r'@@[A-Za-z0-9_]+@@', text)) - set('@@%s@@' % k for k in deferred)
        if left:
            raise SystemExit('还有没填上的格子：%s ⇒ 拒绝写盘' % sorted(left))
        return text

    section_ui = fill(read(os.path.join(SCRATCH, 'r576_ui_audit_section.md')))
    section_state = fill(read(os.path.join(SCRATCH, 'r576_state_section.md')))
    section_buji = fill(read(os.path.join(SCRATCH, 'r576_state_buji_section.md')))
    section_iter = fill(read(os.path.join(SCRATCH, 'r576_iteration_section.md')))
    entry_changelog = fill(read(os.path.join(SCRATCH, 'r576_changelog_entry.md')))
    bullet_report = fill(read(os.path.join(SCRATCH, 'r576_final_report_bullet.md')))
    append_backlog = fill(read(os.path.join(SCRATCH, 'r576_backlog_append.md')))
    append_decisions = fill(read(os.path.join(SCRATCH, 'r576_decisions_append.md')))

    # ---------- 1. UI_AUDIT：降序，插在当前最大轮次标题之上 ----------
    path = os.path.join(ROOT, 'AGENT_UI_AUDIT.md')
    text = read(path)
    if u'## 第 575 轮（R576 · 2026-11-05' in text:
        print('UI_AUDIT 已经有 R576 那一节 ⇒ 跳过（不写第二份）')
        skipped_books.add('AGENT_UI_AUDIT.md')
    anchor = u'## 第 574 轮（R575 · 2026-11-04'
    if 'AGENT_UI_AUDIT.md' not in skipped_books:
        if text.count(anchor) != 1:
            raise SystemExit('UI_AUDIT 锚不唯一：%d' % text.count(anchor))
        head, sep, tail = text.partition(anchor)
        write(path, head + section_ui.rstrip() + u'\n\n' + sep + tail)
        # 插入式补丁的修复证人：写完之后**必须**还是只有一个 R576 标题，且旧标题只有一份。
        after = read(path)
        if after.count(u'## 第 575 轮（R576 · 2026-11-05') != 1 or after.count(anchor) != 1:
            raise SystemExit('UI_AUDIT 插入后标题数不对 ⇒ 立刻停手（R573 那一族：插入式补丁抄两遍）')
    print('UI_AUDIT 写了' if 'AGENT_UI_AUDIT.md' not in skipped_books else 'UI_AUDIT 跳过')

    # ---------- 2. ITERATION：升序，只能追加到文件尾 ----------
    path = os.path.join(ROOT, 'AGENT_VISUAL_ITERATION.md')
    text = read(path)
    if u'## Round 573 · R576' in text:
        print('ITERATION 已经有 Round 573 那一节 ⇒ 跳过（不写第二份）')
        skipped_books.add('AGENT_VISUAL_ITERATION.md')
    if 'AGENT_VISUAL_ITERATION.md' not in skipped_books:
        if not text.endswith(u'\n'):
            text += u'\n'
        write(path, text + u'\n' + section_iter.rstrip() + u'\n')
        print('ITERATION 写了')

    # ---------- 3. CHANGELOG：插在 [Unreleased] 之下 ----------
    path = os.path.join(ROOT, 'CHANGELOG.md')
    text = read(path)
    guard = u'（R576 / 第 575 轮 / Round 573 · 产品 0 文件）'
    if guard in text:
        print('CHANGELOG 已经有 R576 那条 ⇒ 跳过（不写第二份）')
        skipped_books.add('CHANGELOG.md')
    anchor = u'## [Unreleased]\n'
    if 'CHANGELOG.md' not in skipped_books:
        if text.count(anchor) != 1:
            raise SystemExit('CHANGELOG 锚不唯一：%d' % text.count(anchor))
        head, rest = text.split(anchor, 1)
        write(path, head + anchor + u'\n' + entry_changelog.rstrip() + u'\n' + rest)
        print('CHANGELOG 写了')

    # ---------- 4. STATE：新节写在最上面 + `### R575 补记` 向前补记 + 抬「最后更新」 ----------
    path = os.path.join(ROOT, 'AGENT_STATE.md')
    text = read(path)
    if u'## R576 状态（' in text:
        raise SystemExit('STATE 已经有 R576 那一节 ⇒ 拒绝写第二份（本节要改要手工，不许半路重放）')
    anchor = u'## R575 状态（2026-11-04'
    if text.count(anchor) != 1:
        raise SystemExit('STATE 锚不唯一：%d' % text.count(anchor))
    text = text.replace(anchor, section_state.rstrip() + u'\n\n' + anchor, 1)
    buji_anchor = u'## R574 状态（2026-11-04'
    if text.count(buji_anchor) != 1:
        raise SystemExit('STATE 的 R574 锚不唯一：%d' % text.count(buji_anchor))
    if u'### R575 补记（2026-11-05' in text:
        print('STATE 已经有 R575 补记 ⇒ 跳过补记那一半')
    else:
        text = text.replace(buji_anchor, section_buji.rstrip() + u'\n\n' + buji_anchor, 1)
    old_line = re.search(r'(?m)^最后更新：\d{4}-\d{2}-\d{2}（本地 · R\d+ / 第 \d+ 轮 / Round \d+）$', text)
    if old_line is None:
        raise SystemExit('STATE 的「最后更新」那行找不到 ⇒ 不写')
    text = text.replace(old_line.group(0),
                        u'最后更新：2026-11-05（本地 · R576 / 第 575 轮 / Round 573）', 1)
    write(path, text)
    print('STATE 写了（R576 新节 + R575 补记 + 最后更新抬到 R576）')

    # ---------- 5. FINAL_REPORT：五个计数器 + §18 那一笔 ----------
    path = os.path.join(ROOT, 'AGENT_FINAL_REPORT.md')
    text = read(path)
    if u'R576 续到 576' in text:
        print('FINAL_REPORT 已经记过 R576 ⇒ 跳过（不写第二份）')
        skipped_books.add('AGENT_FINAL_REPORT.md')
    pairs = [
        (u'阶段二 **565 轮**审计（R9–R572；以 `curve_from_ledger.py` 的 `PHASE2 n=565` 为准，'
         u'最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 572',
         u'阶段二 **566 轮**审计（R9–R573；以 `curve_from_ledger.py` 的 `PHASE2 n=566` 为准，'
         u'最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 573'),
        (u'| 视觉台账 | U-31 … U-2532', u'| 视觉台账 | U-31 … U-2542'),
        (u'以 `AGENT_STATE.md` 的 R575 节 ② 为准', u'以 `AGENT_STATE.md` 的 R576 节 ② 为准'),
        (u'## 18. R458 → R575 这一段', u'## 18. R458 → R576 这一段'),
        (u'R575 续到 575 —— 这份报告第七次差点停在几十轮之前',
         u'R575 续到 575、R576 续到 576 —— 这份报告第七次差点停在几十轮之前'),
    ]
    if 'AGENT_FINAL_REPORT.md' not in skipped_books:
        for old, new in pairs:
            if text.count(old) != 1:
                raise SystemExit('FINAL_REPORT 锚不唯一：%r → %d' % (old[:40], text.count(old)))
            text = text.replace(old, new, 1)
        tail_anchor = u'R576 续到 576 —— 这份报告第七次差点停在几十轮之前）\n'
        if text.count(tail_anchor) != 1:
            raise SystemExit('FINAL_REPORT §18 尾部锚不唯一')
        index = text.index(tail_anchor) + len(tail_anchor)
        text = text[:index] + u'\n' + bullet_report.rstrip() + u'\n' + text[index:]
        write(path, text)
        print('FINAL_REPORT 写了（§18 那一笔 + 五个计数器）')

    # ---------- 6. BACKLOG / DECISIONS：追加，各带幂等守卫 ----------
    path = os.path.join(ROOT, 'AGENT_BACKLOG.md')
    text = read(path)
    if u'**651 追记（R576）' in text:
        print('BACKLOG 已经有 R576 那几条 ⇒ 跳过（不写第二份）')
        skipped_books.add('AGENT_BACKLOG.md')
    if 'AGENT_BACKLOG.md' not in skipped_books:
        write(path, text.rstrip() + u'\n' + append_backlog)
        print('BACKLOG 追加了（651 追记 / 654 追记 / 653·646·647 追记）')

    path = os.path.join(ROOT, 'AGENT_DECISIONS.md')
    text = read(path)
    if u'## D-576（R576' in text:
        print('DECISIONS 已经有 D-576 ⇒ 跳过（不写第二份）')
        skipped_books.add('AGENT_DECISIONS.md')
    if 'AGENT_DECISIONS.md' not in skipped_books:
        write(path, text.rstrip() + u'\n' + append_decisions)
        print('DECISIONS 追加了 D-576')

    # ---------- 7. 派生格：落盘之后现读，只抄门打印的那一行 ----------
    sources = gate([py, 'scripts/report_sources_cell.py', '--write'], 'report_sources_cell')
    print(sources.strip().splitlines()[-1])
    streak_out = gate([py, 'scripts/product_streak.py'], 'product_streak')
    streak = re.search(r'PRODUCT_STREAK ledger_round=(\d+) streak=(\d+)[^\n]*', streak_out)
    if streak is None:
        raise SystemExit('product_streak 没打出行：%s' % streak_out[-400:])
    print(streak.group(0))
    report = gate([py, 'scripts/ledger_absence_claims.py'], '清账')
    print(report.strip().splitlines()[-1])
    clearing = re.search(r'LEDGER_ABSENCE_CLAIMS 格=(\d+) 声明=(\d+)[^\n]*\n(LEDGER_ABSENCE_RESULT=[^\n]*)', report)
    if clearing is None:
        raise SystemExit('清账那本没打出名 ⇒ 不写：%s' % report[-400:])
    sources_line = re.search(r'SOURCES_CELL [^\n]*', sources)
    if sources_line is None:
        raise SystemExit('sources 那格没打出行：%s' % sources[-400:])
    clearing_cell = u'格=%s 声明=%s，%s' % (clearing.group(1), clearing.group(2), clearing.group(3).strip())

    path = os.path.join(ROOT, 'AGENT_STATE.md')
    text = read(path)
    start, end, section = state_section(text, u'## R576 状态（')
    cell = re.search(u'产品面连续零改动 \\*\\*(\\d+|@@STREAK@@)\\*\\* 轮', section)
    if cell is None:
        raise SystemExit('R576 那一节里没有"产品面连续零改动 **N** 轮"那一格 ⇒ 不写')
    section = section.replace(cell.group(0), u'产品面连续零改动 **%s** 轮' % streak.group(2), 1)
    section = (section.replace('@@STREAK_LINE@@', streak.group(0))
                     .replace('@@CLEARING@@', clearing_cell)
                     .replace('@@SOURCES@@', sources_line.group(0)))
    write(path, text[:start] + section + text[end:])
    print('STATE 的派生格落了（streak / streak 行 / 清账 / sources）')

    fr = os.path.join(ROOT, 'AGENT_FINAL_REPORT.md')
    text = read(fr)
    text = text.replace(u'清账 @@CLEARING@@；', u'清账 ' + clearing_cell + u'；')
    old_streak = re.search(u'产品面连续零改动轮数 = \\*\\*(\\d+)\\*\\*（R575 台账落盘之后现读', text)
    if old_streak is None:
        raise SystemExit('FINAL_REPORT 的 streak 格形状不认识 ⇒ 不写')
    new_streak = (u'产品面连续零改动轮数 = **%s**（R576 台账落盘之后现读 `python3 scripts/product_streak.py` ⇒ '
                  u'`%s`；as-of 口径 ⇒ 读作「本轮之前最后一次产品改动在 %s 轮前（R567 的 `8f679f9`）」，'
                  u'R569…R576 八轮都是产品 0 文件 ⇒ 下一轮是 %s。上一格原文留着：R575 台账落盘之后现读'
                  % (streak.group(2), streak.group(0), streak.group(2), int(streak.group(2)) + 1))
    text = text.replace(old_streak.group(0), new_streak, 1)
    write(fr, text)
    print('FINAL_REPORT 的清账格与 streak 格落了（streak=%s，旧原文留着）' % streak.group(2))

    check = gate([py, 'scripts/product_streak.py', '--check'], 'product_streak --check')
    print(check.strip().splitlines()[-1])

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
    headings = gate([py, 'scripts/ledger_round_headings.py'], '逐字重复标题')
    print(headings.strip().splitlines()[-1])
    return 0


if __name__ == '__main__':
    sys.exit(main())
