# -*- coding: utf-8 -*-
"""R580 台账写手：七本按整行锚插入 + 派生格落盘后现读 + 红名对账由草稿自己数出来。

沿用 R567–R579 那几版的规矩，逐条实现它们抓过的自伤（本轮派单 ⑥ 点名"上轮那六处当清单"）：
- **任何插入台账的文本都过同一趟 fill**，返回前七本各回读一遍 token = 0；唯一允许活着的是
  @@BATTERY@@（电池必须排在台账之后，由 `--finish-battery` 那一趟补）。
- **派生格只在"本轮那一节"里找**（R570 那版在全书找，命中上一轮那一节）。
- **numstat 现读**：代码那一格 + 文档那一格都由 `git diff --numstat` 取，取不到就拒绝写账。
- **⓪ 与 runner 那几格由 `ci_status_r580.py` 落盘的摘录派生**（`/tmp/r580/ci_status.txt`），
  开场那一刻那一格另存 `/tmp/r580/ci_status_open.txt`（它**不是**脚本派生，账上已写明取值时刻）。
- **三跑互校**：`PROBE_COVERAGE_SUMMARY` 在两跑里 红=0 / 红=1 —— 这一对不许被平均、也不许被写成
  "STEP[18] 绿了"；红名单三跑逐字同集合这件事由**三份名单互相等不等**判，不等就 SystemExit。
- **本轮那句"四个数一字未动"由日志判**：`D12_CHANNEL_MAP_SUMMARY` 必须逐字含
  `条=8 runner可判=0 只能真机=1 今天无证人=7`，否则拒绝写账（账里那三处硬说"一字未动"）。
- **红名对账由草稿自己数**：`  · 红名「` 的行数、`^- ⑨·` 的行数、以及"没指向任何 ⑨ 编号"的行数，
  三个数都从 r580_state_section.md 现读派生 ⇒ 上一轮那种"⑨ 少数了一处"不会靠我眼力避免。
- 本轮产品 0 文件 ⇒ 不跑 `install_local.sh`（账里写具名 SKIP_INSTALL=no-product-change）。

用法：python3 .scratch/motion-audit-2/ledgers_r580.py                  # 只数不写
      python3 .scratch/motion-audit-2/ledgers_r580.py --apply           # 真写七本 + 派生格
      python3 .scratch/motion-audit-2/ledgers_r580.py --finish-battery  # 电池落盘之后补那一格
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRATCH = os.path.join(ROOT, '.scratch', 'motion-audit-2')
LOGS = {
    # 本轮（R580）**最终代码状态**那一趟：四把刀全部还原之后再跑，账只抄这一批
    'capture': '/tmp/r580/capture.log',        # UICaptureTests + TransparencyForensicsTests（带重捕）
    'forensics': '/tmp/r580/forensics.log',    # CLIPBOARD_HISTORY_UI_REALSCREEN=1 那一趟
    'full': '/tmp/r580/full.log',
    'compare': '/tmp/r580/baseline.log',
    'needles': '/tmp/r580/precheck.log',
    'hidden': '/tmp/r580/hidden.log',
    'battery': '/tmp/r580/battery.log',
    'knives': '/tmp/r580/knives.log',
    'probeA': '/tmp/r580/probe_A_arrived.log',       # 一次性探针第一往（假驱动 ⇒ 端到端 6 朵红）
    'probeBlind': '/tmp/r580/probe_blind_endtoend.log',  # 第二往（只注入 B 的形状 ⇒ 新那条红路）
    'probeComment': '/tmp/r580/probe_commentfed.log',    # 第一往那版**注释喂饱 A** 的读数
    'ci': '/tmp/r580/ci_status.txt',
    'ci_open': '/tmp/r580/ci_status_open.txt',
    'needle_recovery': '/tmp/r580/needle_recovery.txt',
}
BOOKS = ('AGENT_STATE.md', 'AGENT_UI_AUDIT.md', 'AGENT_VISUAL_ITERATION.md',
         'CHANGELOG.md', 'AGENT_FINAL_REPORT.md', 'AGENT_BACKLOG.md', 'AGENT_DECISIONS.md')

SHOTS_SEEN = io.open(os.path.join(SCRATCH, 'r580_shots_note.md'), encoding='utf-8').read().strip()
SHOTS_SCORE = u'12/15'
SHOTS_SHORT = io.open(os.path.join(SCRATCH, 'r580_shots_short.md'), encoding='utf-8').read().strip()

D12_UNCHANGED = u'条=8 runner可判=0 只能真机=1 今天无证人=7'


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


def numstat(rel):
    out = subprocess.run(['git', 'diff', '--numstat', '--', rel], cwd=ROOT,
                         capture_output=True, text=True).stdout.strip()
    if not out:
        return None
    parts = out.split('\n')[0].split('\t')
    if len(parts) < 2 or not parts[0].isdigit() or not parts[1].isdigit():
        raise SystemExit('numstat 读不到 %s：%r ⇒ 不许把 +N/−M 写进账' % (rel, out))
    return parts[0], parts[1]


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
    capture_line = grab(r"Executed \d+ tests, with \d+ tests? skipped and \d+ failures",
                        LOGS['capture'], '判据卷逐字行')
    capture_secs = grab(r"in ([\d.]+) \([\d.]+\) seconds", LOGS['capture'], '判据卷时长')
    full = grab(r"Executed (\d+) tests, with (\d+) tests? skipped and (\d+) failures",
                LOGS['full'], '全量卷汇总', flags=re.M)
    full_secs = grab(r"in ([\d.]+) \([\d.]+\) seconds", LOGS['full'], '全量卷时长')
    # 真机键那一趟**没有 skipped**（只跑一个类），所以那行的形状是 `with 1 failure` —— 模式必须两种都认，
    # 否则"取不到"会被误读成"那一趟没跑"。
    forensics_line = grab(r"Executed \d+ tests, with (?:\d+ tests? skipped and )?\d+ failures?",
                          LOGS['forensics'], '真机键那一趟逐字行')
    frames = 'COMPARED=%s CHANGED=%s MISSING=%s ADDED=%s' % (
        grab(r"FRAME_BASELINE_COMPARED=(\d+)", LOGS['compare'], '帧 COMPARED'),
        grab(r"FRAME_BASELINE_CHANGED=(\d+)", LOGS['compare'], '帧 CHANGED'),
        grab(r"FRAME_BASELINE_MISSING=(\d+)", LOGS['compare'], '帧 MISSING'),
        grab(r"FRAME_BASELINE_ADDED=(\d+)", LOGS['compare'], '帧 ADDED'))
    needles = grab(r"NEEDLE_PRECHECK tables=\d+ covered=\d+ arms=\d+ bad=\d+",
                   LOGS['needles'], '针预检')
    arm_total = grab(r"ARM_TOTAL files=\d+ arms=\d+ dupes=\d+ repeats=\d+",
                     LOGS['needles'], '跨表刀号')
    if u'bad=0' not in needles:
        raise SystemExit('针预检不是 bad=0（%s）⇒ 先修针再写账' % needles)
    hidden = grab(r"HIDDEN_ARMS [^\n]*", LOGS['hidden'], '盲区名册')

    # 本轮那张表的四个数：账里三处硬说"一字未动"，所以这一句必须由日志判，不许由我判。
    d12_local = grab(r'D12_CHANNEL_MAP_SUMMARY[^\n]*', LOGS['capture'], '映射表本机汇总')
    if D12_UNCHANGED not in d12_local:
        raise SystemExit('四个数变了（现读 %s）⇒ 账里那三处"一字未动"就不成立，先改措辞' % d12_local[:120])
    prereq_line = grab(r'D12_PREREQ [^\n]*', LOGS['capture'], '前置同类性')
    rejudged_line = grab(r'D12_REJUDGED [^\n]*', LOGS['capture'], '八条重判汇总')
    live_gate = grab(r'D12_LIVE_GATE [^\n]*', LOGS['capture'], '活门那格')
    live_gate_probe = grab(r'D12_LIVE_GATE_PROBE [^\n]*', LOGS['capture'], '注入正对照那格')
    if u'本轮该翻=0' not in live_gate or u'判=缺席' not in live_gate:
        raise SystemExit('活门那格不是"缺席/该翻 0"（%s）⇒ 账里的措辞要重写' % live_gate[:160])

    # 一次性探针三往（不入库，读数只进账）
    probe_a_gate = grab(r'D12_LIVE_GATE [^\n]*', LOGS['probeA'], '探针第一往的活门行')
    probe_a_fail = grab(r"Executed \d+ test[s]?, with \d+ failure[s]?[^\n]*", LOGS['probeA'],
                        '探针第一往的红数')
    probe_a_rows = len(re.findall(u'声明「今天无证人」而实测给的是「runner可判」', read(LOGS['probeA'])))
    probe_blind_gate = grab(r'D12_LIVE_GATE [^\n]*', LOGS['probeBlind'], '探针第二往的活门行')
    probe_blind_fail = grab(r"Executed \d+ test[s]?, with \d+ failure[s]?[^\n]*", LOGS['probeBlind'],
                            '探针第二往的红数')
    probe_comment_gate = grab(r'D12_LIVE_GATE [^\n]*', LOGS['probeComment'], '注释喂 A 那一趟的活门行')
    if probe_a_rows != 5:
        raise SystemExit('第一往该有 5 行逐条红，实读 %d ⇒ 「翻不动就红」这句话没有证人' % probe_a_rows)
    if u'现扫瞎' not in probe_blind_gate:
        raise SystemExit('第二往没落到"现扫瞎"那一支（%s）⇒ 新那条红路的端到端证人不存在' % probe_blind_gate[:160])
    if u'由A认得' not in probe_comment_gate:
        raise SystemExit('注释那一趟没被 A 喂饱 ⇒ 本轮那条尺病读数不成立（%s）' % probe_comment_gate[:160])
    # 两往的"红了几朵"**逐字抄那一趟的汇总行**，不我自己拼句子（R565 那一族：通道值要由被计数物自己打印）
    probe_a_cell = u'%s ‖ 逐条红=%d 行 + 那条「本轮该翻=5」红 ⇒ 该趟逐字 `%s`' % (
        probe_a_gate, probe_a_rows, probe_a_fail.strip())
    probe_blind_cell = u'%s ‖ 那一朵就是新那条红路 ⇒ 该趟逐字 `%s`' % (
        probe_blind_gate, probe_blind_fail.strip())
    probe_comment_cell = probe_comment_gate

    # 四把刀：CAUGHT 与 RESTORE_CLEAN 的个数由 knives.log 数，不靠我数
    knife_text = read(LOGS['knives'])
    caught = re.findall(r'(M15\d\d): CAUGHT', knife_text)
    clean = knife_text.count('RESTORE_CLEAN=yes')
    if caught != ['M1523', 'M1524', 'M1525', 'M1526'] or clean != 4:
        raise SystemExit('刀不是 4/4 CAUGHT 且 4 次 RESTORE_CLEAN（CAUGHT=%s clean=%d）⇒ 不写账'
                         % (caught, clean))
    knives_cell = (u'M1523/M1524/M1525/M1526 **4/4 CAUGHT**、RESTORE_CLEAN=yes ×%d（一把一次还原，'
                   u'串行跑在同一把锁外）' % clean)

    # 禁碰证人（真机键那一趟）
    ground_state = grab(r'TRANSPARENCY_STATE [^\n]*', LOGS['forensics'], '禁碰证人 底衬状态')
    ground_hit = grab(r'TRANSPARENCY_HITTEST [^\n]*', LOGS['forensics'], '禁碰证人 命中')
    ground_mat = grab(r'TRANSPARENCY_MATERIAL [^\n]*', LOGS['forensics'], '禁碰证人 材质（真机键）')
    ground_neg = grab(r'TRANSPARENCY_MATERIAL_NEG [^\n]*', LOGS['forensics'], '禁碰证人 材质反面臂')
    ground_tier = grab(r'TRANSPARENCY_MATERIAL_TIER [^\n]*', LOGS['forensics'], '禁碰证人 档位与正对照')
    bare_mag = re.search(u'TRANSPARENCY_MATERIAL_NEG 撤掉底衬 [^\\n]*?品红漏出=(\\d+)', ground_neg)
    ctrl = re.search(u'正对照品红=(\\d+)/(\\d+)', ground_tier)
    tier_read = re.search(u'档位=(\\S+)', ground_tier)
    if not (bare_mag and ctrl and tier_read):
        raise SystemExit('反面臂/档位那两行里读不到品红或档位 ⇒ 不许把禁碰证人写成签收')
    bare_magenta = int(bare_mag.group(1))
    control_magenta, control_samples = int(ctrl.group(1)), int(ctrl.group(2))
    tier_value = tier_read.group(1)
    if control_samples == 0:
        raise SystemExit('正对照采样数=0 ⇒ 那条活门自己没对象，不许写账')
    appearance = subprocess.run(['defaults', 'read', '-g', 'AppleInterfaceStyle'],
                                capture_output=True, text=True).stdout.strip() or 'Light'
    if tier_value not in ('Dark', 'Light'):
        raise SystemExit('判据打印的档位是「%s」⇒ 两通道不相符或未知，这一格没有名字' % tier_value)
    if appearance != tier_value:
        raise SystemExit('判据打印的档位 %s 与这台机器的偏好键 %s 不符 ⇒ 拒绝写账（三条通道打脸了）'
                         % (tier_value, appearance))
    if bare_magenta == 0:
        ground_cell = (u'`%s`、`%s`（这两条与 R579 逐字同）；材质那一档**当轮仍没签**：`%s`、反面臂 `%s`、'
                       u'档位与正对照 `%s` ⇒ 撤底衬那臂品红漏出=**%d**，而同一阈值在窗口之外那块品红板上读到 '
                       u'%d/%d 颗 ⇒「通道拍不到品红」那一支仍然被排掉，剩下的解释只有「%s 档的材质把品红混合到阈值以下」；'
                       u'具名 `TRANSPARENCY_MATERIAL_APPEARANCE_NOT_RUN=%s档无当轮证人_Light档有R568数` '
                       u'**一字未动**，本轮没接回、没选边、没翻这台机器的外观'
                       % (ground_state, ground_hit, ground_mat, ground_neg, ground_tier,
                          bare_magenta, control_magenta, control_samples, tier_value, tier_value))
    else:
        ground_cell = (u'`%s`、`%s`、`%s`（真机键那一档本轮单独跑到数，反面臂 `%s`，档位 `%s`，'
                       u'撤底衬那臂品红漏出=%d ⇒ 656 那一问在这一趟**有了当轮证人**，账上向前补记）'
                       % (ground_state, ground_hit, ground_mat, ground_neg, ground_tier, bare_magenta))

    # push 通道在**台账落盘之前**现读（不改 remote、不碰 ~/.ssh、不换 DNS、不加 scope）
    ls = subprocess.Popen(['git', 'ls-remote', 'origin', 'HEAD'], cwd=ROOT,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    ls_out = ls.communicate()[0].decode('utf-8', 'replace')
    url = subprocess.run(['git', 'config', '--get', 'remote.origin.url'], cwd=ROOT,
                         capture_output=True, text=True).stdout.strip()
    ahead = subprocess.run(['git', 'rev-list', '--count', 'origin/main..HEAD'], cwd=ROOT,
                           capture_output=True, text=True).stdout.strip() or '?'
    head_sha = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT,
                              capture_output=True, text=True).stdout.strip()
    if ls.returncode == 0 and ls_out.strip():
        push_line = (u'`PUSH_TRANSPORT=ssh-ok` —— 现读 `git ls-remote origin HEAD` 通（远端 HEAD='
                     + ls_out.split()[0][:9] + u'），`git config --get remote.origin.url` 仍是 '
                     + (u'`git@github.com:…`（SSH 形式，未改动）' if url.startswith('git@')
                        else u'**不是** SSH 形式（现读值 ' + url + u'）'))
    else:
        push_line = (u'`PUSH_TRANSPORT=blocked` —— 现读 `git ls-remote origin HEAD` 退出码 '
                     + str(ls.returncode) + u'，正文首行 `'
                     + (ls_out.strip().splitlines() or [u'空'])[0][:60] + u'`')
    print('PUSHLINE %s' % push_line[:150])

    product_files = [p for p in subprocess.run(['git', 'diff', '--name-only'], cwd=ROOT,
                                                capture_output=True, text=True).stdout.split('\n')
                     if p.startswith('ClipboardHistory/Sources/') or p.startswith('Sources/')]
    code_pair = numstat('ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift')
    if code_pair is None:
        raise SystemExit('代码文件 numstat 空 ⇒ 本轮那格没有证人（工作树不该是干净的）')
    code_cell = u'+%s / −%s' % code_pair
    doc_pair = numstat('docs/FOLD_DUO_SPEC_2026-11-03.md')
    if doc_pair != ('1', '0'):
        raise SystemExit('文档那一笔必须 +1/−0，实得 %r ⇒ 停手对拍（R578/R579 那一族）' % (doc_pair,))

    # ---------- ⓪ 的摘录：中途复核 + 开场那一刻 ----------
    if not os.path.exists(LOGS['ci']):
        raise SystemExit('⓪ 的摘录不在盘上：%s ⇒ 拒绝写账（先跑 ci_status_r580.py）' % LOGS['ci'])
    ci_status = read(LOGS['ci'])
    open_status = read(LOGS['ci_open'])

    def cifield(label):
        for line in ci_status.split('\n'):
            if line.startswith(label + ' ::'):
                return line.split(' ::', 1)[1].strip()
        raise SystemExit('⓪ 摘录里没有 %s 那一格 ⇒ 先补取数，不许手打' % label)

    def openfield(label):
        for line in open_status.split('\n'):
            if line.startswith(label + ' ::'):
                return line.split(' ::', 1)[1].strip()
        raise SystemExit('⓪ 开场摘录里没有 %s 那一格 ⇒ 这一句不能写' % label)

    names_main = cifield('NAMES_MAIN')
    names_buji = cifield('NAMES_BUJI')
    names_buji2 = cifield('NAMES_BUJI2')
    if not (names_main == names_buji == names_buji2):
        raise SystemExit('三跑红名单不同集合 ⇒ 账里那句"逐字同集合"不成立，停手对拍')

    numbers = dict(
        OPEN_RUNS=openfield('OPEN_RUNS'), OPEN_CHANNEL=openfield('OPEN_CHANNEL'),
        STATUS_MAIN=cifield('STATUS_MAIN'), STATUS_BUJI=cifield('STATUS_BUJI'),
        STATUS_BUJI2=cifield('STATUS_BUJI2'),
        STEPS_MAIN=cifield('STEPS_MAIN'), STEPS_BUJI=cifield('STEPS_BUJI'),
        STEPS_BUJI2=cifield('STEPS_BUJI2'),
        NAMES_MAIN=names_main, NAMES_BUJI=names_buji, NAMES_BUJI2=names_buji2,
        GEOMETRY_RUNNER=cifield('GEOMETRY_MAIN'), MATERIAL_RUNNER=cifield('MATERIAL_MAIN'),
        MATERIAL_RUNNER2=cifield('MATERIAL_BUJI2'), PROBE_MAIN=cifield('PROBE_MAIN'),
        PROBE_BUJI2=cifield('PROBE_BUJI2'), GATE_MAIN=cifield('GATE_MAIN'),
        MOTION_MAIN=cifield('MOTION_MAIN'), LIVE_GATE_RUNNER=cifield('LIVE_GATE_MAIN'),
        API_CODE=cifield('API_ANON'), GITHUB_CODE=cifield('GITHUB_ANON'),
        GH_OK=cifield('GH_TOKEN_CHANNEL'),
        LIVE_GATE=live_gate, LIVE_GATE_PROBE=live_gate_probe,
        D12_LOCAL=d12_local, PREREQ=prereq_line, REJUDGED=rejudged_line,
        PROBE_A_ARRIVED=probe_a_cell, PROBE_BLIND=probe_blind_cell, PROBE_COMMENT=probe_comment_cell,
        KNIVES=knives_cell, GROUND_WITNESS=ground_cell,
        NEEDLE_RECOVERY=grab(r'NEEDLE_RECOVERY [^\n]*', LOGS['needle_recovery'], '撞针重建证人'),
        CAPTURE_LINE=capture_line, CAPTURE_SECS=capture_secs,
        FULL='Executed %s tests（%s 跳过、%s 失败）' % full, FULL_SECS=full_secs,
        FORENSICS_LINE=forensics_line, FRAMES=frames,
        NEEDLES=needles, ARM_TOTAL=arm_total, HIDDEN=hidden.strip(),
        SHOTS_SEEN=SHOTS_SEEN, SHOTS_SCORE=SHOTS_SCORE, SHOTS_SHORT=SHOTS_SHORT,
        CODE_CELL=code_cell, PRODUCT_FILE_COUNT=str(len(product_files)),
        PUSH_LINE=push_line, AHEAD=ahead, HEAD_SHA=head_sha,
    )
    # 红名对账：三个数都从草稿现读，不靠我数
    state_draft = read(os.path.join(SCRATCH, 'r580_state_section.md'))
    red_rows = re.findall(u'  · 红名「[^\\n]*', state_draft)
    jiu_rows = re.findall(u'(?m)^- ⑨·\\d', state_draft)
    numbers['RED_NAMES'] = str(len(red_rows))
    numbers['JIU_COUNT'] = str(len(jiu_rows))
    numbers['RED_EXTRA'] = str(len([r for r in red_rows if u'→ ⑨·' not in r]))
    for key, value in sorted(numbers.items()):
        print('%-20s %s' % (key, value[:120]))

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

    section_ui = fill(read(os.path.join(SCRATCH, 'r580_ui_audit_section.md')))
    section_state = fill(read(os.path.join(SCRATCH, 'r580_state_section.md')))
    section_iter = fill(read(os.path.join(SCRATCH, 'r580_iteration_section.md')))
    entry_changelog = fill(read(os.path.join(SCRATCH, 'r580_changelog_entry.md')))
    bullet_report = fill(read(os.path.join(SCRATCH, 'r580_final_report_bullet.md')))
    append_backlog = fill(read(os.path.join(SCRATCH, 'r580_backlog_append.md')))
    append_decisions = fill(read(os.path.join(SCRATCH, 'r580_decisions_append.md')))

    # ---------- 1. UI_AUDIT：降序，插在当前最大轮次标题之上 ----------
    path = os.path.join(ROOT, 'AGENT_UI_AUDIT.md')
    text = read(path)
    if u'## 第 579 轮（R580 · 2026-11-05' in text:
        print('UI_AUDIT 已经有 R580 那一节 ⇒ 跳过（不写第二份）')
        skipped_books.add('AGENT_UI_AUDIT.md')
    anchor = u'## 第 578 轮（R579 · 2026-11-05'
    if 'AGENT_UI_AUDIT.md' not in skipped_books:
        if text.count(anchor) != 1:
            raise SystemExit('UI_AUDIT 锚不唯一：%d' % text.count(anchor))
        head, sep, tail = text.partition(anchor)
        write(path, head + section_ui.rstrip() + u'\n\n' + sep + tail)
        after = read(path)
        if after.count(u'## 第 579 轮（R580 · 2026-11-05') != 1 or after.count(anchor) != 1:
            raise SystemExit('UI_AUDIT 插入后标题数不对 ⇒ 立刻停手（R573 那一族：插入式补丁抄两遍）')
    print('UI_AUDIT 写了' if 'AGENT_UI_AUDIT.md' not in skipped_books else 'UI_AUDIT 跳过')

    # ---------- 2. ITERATION：升序，只能追加到文件尾 ----------
    path = os.path.join(ROOT, 'AGENT_VISUAL_ITERATION.md')
    text = read(path)
    if u'## Round 577 · R580' in text:
        print('ITERATION 已经有 Round 577 那一节 ⇒ 跳过（不写第二份）')
        skipped_books.add('AGENT_VISUAL_ITERATION.md')
    if 'AGENT_VISUAL_ITERATION.md' not in skipped_books:
        if not text.endswith(u'\n'):
            text += u'\n'
        write(path, text + u'\n' + section_iter.rstrip() + u'\n')
        print('ITERATION 写了')

    # ---------- 3. CHANGELOG：插在 [Unreleased] 之下 ----------
    path = os.path.join(ROOT, 'CHANGELOG.md')
    text = read(path)
    guard = u'（R580 / 第 579 轮 / Round 577 · 产品 0 文件）'
    if guard in text:
        print('CHANGELOG 已经有 R580 那条 ⇒ 跳过（不写第二份）')
        skipped_books.add('CHANGELOG.md')
    anchor = u'## [Unreleased]\n'
    if 'CHANGELOG.md' not in skipped_books:
        if text.count(anchor) != 1:
            raise SystemExit('CHANGELOG 锚不唯一：%d' % text.count(anchor))
        head, rest = text.split(anchor, 1)
        write(path, head + anchor + u'\n' + entry_changelog.rstrip() + u'\n' + rest)
        print('CHANGELOG 写了')

    # ---------- 4. STATE：新节写在最上面 + 抬「最后更新」（本轮没有补记） ----------
    path = os.path.join(ROOT, 'AGENT_STATE.md')
    text = read(path)
    if u'## R580 状态（' in text:
        raise SystemExit('STATE 已经有 R580 那一节 ⇒ 拒绝写第二份（本节要改要手工，不许半路重放）')
    anchor = u'## R579 状态（2026-11-05'
    if text.count(anchor) != 1:
        raise SystemExit('STATE 主锚不唯一：%d' % text.count(anchor))
    text = text.replace(anchor, section_state.rstrip() + u'\n\n' + anchor, 1)
    old_line = re.search(r'(?m)^最后更新：\d{4}-\d{2}-\d{2}（本地 · R\d+ / 第 \d+ 轮 / Round \d+）$', text)
    if old_line is None:
        raise SystemExit('STATE 的「最后更新」那行找不到 ⇒ 不写')
    text = text.replace(old_line.group(0),
                        u'最后更新：2026-11-05（本地 · R580 / 第 579 轮 / Round 577）', 1)
    write(path, text)
    print('STATE 写了（R580 新节 + 最后更新抬到 R580）')

    # ---------- 5. FINAL_REPORT：五个计数器 + §18 那一笔 ----------
    path = os.path.join(ROOT, 'AGENT_FINAL_REPORT.md')
    text = read(path)
    if u'R580 续到 580' in text:
        print('FINAL_REPORT 已经记过 R580 ⇒ 跳过（不写第二份）')
        skipped_books.add('AGENT_FINAL_REPORT.md')
    umax = max(int(x) for x in re.findall(r'\bU-(\d{3,4})\b', read(os.path.join(ROOT, 'AGENT_UI_AUDIT.md'))))
    pairs = [
        (u'阶段二 **569 轮**审计（R9–R576；以 `curve_from_ledger.py` 的 `PHASE2 n=569` 为准，'
         u'最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 576',
         u'阶段二 **570 轮**审计（R9–R577；以 `curve_from_ledger.py` 的 `PHASE2 n=570` 为准，'
         u'最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 577'),
        (u'以 `AGENT_STATE.md` 的 R579 节 ② 为准', u'以 `AGENT_STATE.md` 的 R580 节 ② 为准'),
        (u'## 18. R458 → R579 这一段', u'## 18. R458 → R580 这一段'),
        (u'R578 续到 578、R579 续到 579 —— 这份报告第七次差点停在几十轮之前',
         u'R579 续到 579、R580 续到 580 —— 这份报告第七次差点停在几十轮之前'),
    ]
    if 'AGENT_FINAL_REPORT.md' not in skipped_books:
        for old, new in pairs:
            if text.count(old) != 1:
                raise SystemExit('FINAL_REPORT 锚不唯一：%r → %d' % (old[:40], text.count(old)))
            text = text.replace(old, new, 1)
        text, n_u = re.subn(r'\| 视觉台账 \| U-31 … U-\d{3,4}',
                            u'| 视觉台账 | U-31 … U-%d' % umax, text)
        if n_u != 1:
            raise SystemExit('视觉台账那格命中 %d 次 ⇒ 不写（派生格只许命中一次）' % n_u)
        print('视觉台账那格由 UI_AUDIT 现读派生 ⇒ U-%d' % umax)
        tail_anchor = u'R580 续到 580 —— 这份报告第七次差点停在几十轮之前）\n'
        if text.count(tail_anchor) != 1:
            raise SystemExit('FINAL_REPORT §18 尾部锚不唯一')
        index = text.index(tail_anchor) + len(tail_anchor)
        text = text[:index] + u'\n' + bullet_report.rstrip() + u'\n' + text[index:]
        write(path, text)
        print('FINAL_REPORT 写了（§18 那一笔 + 五个计数器）')

    # ---------- 6. BACKLOG / DECISIONS：追加，各带幂等守卫 ----------
    path = os.path.join(ROOT, 'AGENT_BACKLOG.md')
    text = read(path)
    if u'**654 追记（R580）' in text:
        print('BACKLOG 已经有 R580 那几条 ⇒ 跳过（不写第二份）')
        skipped_books.add('AGENT_BACKLOG.md')
    if 'AGENT_BACKLOG.md' not in skipped_books:
        write(path, text.rstrip() + u'\n' + append_backlog)
        print('BACKLOG 追加了（654 追记 / 656·655 状态 / 646·647·650·651·653 状态）')

    path = os.path.join(ROOT, 'AGENT_DECISIONS.md')
    text = read(path)
    if u'## D-580（R580' in text:
        print('DECISIONS 已经有 D-580 ⇒ 跳过（不写第二份）')
        skipped_books.add('AGENT_DECISIONS.md')
    if 'AGENT_DECISIONS.md' not in skipped_books:
        write(path, text.rstrip() + u'\n' + append_decisions)
        print('DECISIONS 追加了 D-580')

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
    start, end, section = state_section(text, u'## R580 状态（')
    cell = re.search(u'产品面连续零改动 \\*\\*(\\d+|@@STREAK@@)\\*\\* 轮', section)
    if cell is None:
        raise SystemExit('R580 那一节里没有"产品面连续零改动 **N** 轮"那一格 ⇒ 不写')
    section = section.replace(cell.group(0), u'产品面连续零改动 **%s** 轮' % streak.group(2), 1)
    section = (section.replace('@@STREAK_LINE@@', streak.group(0))
                     .replace('@@CLEARING@@', clearing_cell)
                     .replace('@@SOURCES@@', sources_line.group(0)))
    write(path, text[:start] + section + text[end:])
    print('STATE 的派生格落了（streak / streak 行 / 清账 / sources）')

    fr = os.path.join(ROOT, 'AGENT_FINAL_REPORT.md')
    text = read(fr)
    if text.count(u'清账 @@CLEARING@@；') != 1:
        raise SystemExit('FINAL_REPORT 里 @@CLEARING@@ 应恰好一处（本轮那一笔），实得 %d'
                         % text.count(u'清账 @@CLEARING@@；'))
    text = text.replace(u'清账 @@CLEARING@@；', u'清账 ' + clearing_cell + u'；')
    old_streak = re.search(u'产品面连续零改动轮数 = \\*\\*(\\d+)\\*\\*（R579 台账落盘之后现读', text)
    if old_streak is None:
        raise SystemExit('FINAL_REPORT 的 streak 格形状不认识 ⇒ 不写')
    new_streak = (u'产品面连续零改动轮数 = **%s**（R580 台账落盘之后现读 `python3 scripts/product_streak.py` ⇒ '
                  u'`%s`；as-of 口径 ⇒ 读作「本轮之前最后一次产品改动在 %s 轮前（R567 的 `8f679f9`）」，'
                  u'R569…R580 共 %s 轮都是产品 0 文件 ⇒ 下一轮是 %s。上一格原文留着：R579 台账落盘之后现读'
                  % (streak.group(2), streak.group(0), streak.group(2), streak.group(2),
                     int(streak.group(2)) + 1))
    text = text.replace(old_streak.group(0), new_streak, 1)
    write(fr, text)
    print('FINAL_REPORT 的清账格与 streak 格落了（streak=%s，旧原文留着）' % streak.group(2))

    # ---------- 7b. 派生格**扫全七本**（R580 ⑨·8 那一处：以前只补 STATE，UI_AUDIT 带着同一个
    # 占位符落盘，而抓它的那一步又坐在会崩的门后面 —— 于是"没被抓到"被读成"没有"）。
    derived = {'@@CLEARING@@': clearing_cell, '@@SOURCES@@': sources_line.group(0),
               '@@STREAK_LINE@@': streak.group(0)}
    for name in BOOKS:
        path = os.path.join(ROOT, name)
        body = read(path)
        if not any(tok in body for tok in derived):
            continue
        for tok, value in derived.items():
            body = body.replace(tok, value)
        write(path, body)
        print('%s 的派生格补平（扫全七本这一趟）' % name)

    # ---------- 8. 回读 + 三门：回读**必须先跑**，且任何一门崩掉都要先看到回读结果 ----------
    problems = []
    for name in BOOKS:
        leftover = set(re.findall(r'@@[A-Za-z0-9_]+@@', read(os.path.join(ROOT, name)))) - {u'@@BATTERY@@'}
        if leftover:
            problems.append('%s 里还剩未渲染的占位符：%s' % (name, sorted(leftover)))
    if problems:
        raise SystemExit(u'\n'.join(problems))
    print('七本回读：除 @@BATTERY@@（电池排在台账之后）之外未渲染占位符 = 0')

    for argv, label in (([py, 'scripts/ci_channel_hygiene.py'], u'通道卫生'),
                        ([py, 'scripts/commit_round_identity.py'], u'提交身份'),
                        ([py, 'scripts/ledger_round_headings.py'], u'逐字重复标题'),
                        ([py, 'scripts/product_streak.py', '--check'], u'product_streak --check')):
        try:
            out = gate(argv, label)
            print(out.strip().splitlines()[-1])
        except SystemExit as exc:
            raise SystemExit('%s 这一门在**回读之后**崩了（回读结果已打印在上面）：\n%s' % (label, exc))
    return 0


if __name__ == '__main__':
    sys.exit(main())
