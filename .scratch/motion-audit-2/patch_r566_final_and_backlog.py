#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R566 的第二批台账：AGENT_FINAL_REPORT 的计数器 + §18 那一笔，BACKLOG 的 633 更新与新单 642。

计数器一格都不手抄：标题、§1、§18 头、U 上界、state 指针全部按"+1"改写，由
`test_final_report_headline.py` / `test_round_claim_consistency.py` 去对活账。
"""
import io
import re
import sys

NUM = {
    'BATTERY': '台账后现读',
    'FULL': '1406/57/1 红（负载相关，见 STATE ⑤）',
    'CAPTURE': '222/4 skipped/0 失败（1010.3s）',
    'FRAMES': 'CHANGED=135（不 update）',
    'U_TO': '2456',
}

check = '--check' in sys.argv


def rd(p):
    return io.open(p, encoding='utf-8').read()


def wr(p, t):
    io.open(p, 'w', encoding='utf-8').write(t)


def once(t, old, new, label):
    if t.count(old) != 1:
        sys.stderr.write('ANCHOR_BAD %s 命中=%d\n' % (label, t.count(old)))
        sys.exit(1)
    return t.replace(old, new, 1)


def fill(text):
    out = text
    for key, value in NUM.items():
        out = out.replace('@@%s@@' % key, value)
    if '@@' in out:
        i = out.find('@@')
        sys.stderr.write('NUM_NOT_FILLED %s\n' % out[i:i + 26])
        sys.exit(1)
    bad = re.search(r'%(?=[a-zA-Z])', out)
    if bad:
        sys.stderr.write('BARE_PERCENT_LEFT %s\n' % out[max(0, bad.start() - 30):bad.start() + 30])
        sys.exit(1)
    return out


n = 'AGENT_FINAL_REPORT.md'
t = rd(n)
if 'R566 续到 566' in t:
    sys.stderr.write('ALREADY_PATCHED final-report\n')
    sys.exit(1)
for old, new, label in [
    ('R9–R562，563 节自评', 'R9–R563，564 节自评', 'title'),
    ('阶段二 **555 轮**审计（R9–R562；以 `curve_from_ledger.py` 的 `PHASE2 n=555` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 562',
     '阶段二 **556 轮**审计（R9–R563；以 `curve_from_ledger.py` 的 `PHASE2 n=556` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 563', '§1'),
    ('| 视觉台账 | U-31 … U-2450', '| 视觉台账 | U-31 … U-@@UT@@', 'U 上界'),
    ('- **R565 补段（同一轮续写，未收口：4 笔未推 + 本段的台账笔）**',
     '- **R565 补段（同一轮续写；这一批后来全部推齐、ahead=0 —— 见 `AGENT_STATE.md` 的 R565 补记 ⑭/⑮）**', 'fr-stale-close'),
    ('以 `AGENT_STATE.md` 的 R565 节 ② 为准', '以 `AGENT_STATE.md` 的 R566 节 ② 为准', 'state pointer'),
    ('## 18. R458 → R565 这一段', '## 18. R458 → R566 这一段', '§18 head'),
    ('R565 续到 565 —— 这份报告第七次差点停在几十轮之前）',
     'R565 续到 565、R566 续到 566 —— 这份报告第七次差点停在几十轮之前）', '§18 tail'),
]:
    t = once(t, old, new, label)

anchor = '数若变就照实在补记里加一行）。\n'
bullet = (u'- **R566（产品 0 文件；判据 1 格 + 刀 2 把 + 新开 642）**：本机码签身份从"账里的一句话"变成"一条会红的现读判据" —— '
          u'`security find-identity` 现读 1 条 `ClipboardHistory Local Signing`（R553 时 0 条），新格真签一枚临时包并要求 '
          u'`SIGNATURE_KIND=local identity=…` + 包里真有 `Authority=`/`flags=0x0`；没有该身份的机器具名 `SIGN_LIVE_NOT_RUN=no-identity`（skip 与断言同函数）。'
          u'刀 **M1474**（有身份却回退）/**M1475**（回退不报=静默 adhoc，R553 最初的洞）全 CAUGHT、RESTORE_CLEAN=yes。'
          u'真跑交付链：`make bundle` ⇒ `SIGNATURE_KIND=local`，`install_local.sh --yes` ⇒ `INSTALL_SIGNATURE=local flags=0x0 / SMOKE_OK=1 / ENTRIES=451=451`，'
          u'并与上一轮那份备份逐字对拍 `CodeDirectory size=23793 hashes=737+3 / Signature size=1900 / 同一 Authority` ⇒ 这条验收从此有判据（R554 起只有读数）。'
          u'**新自伤**：`bc5a2af` 起三连的 commit subject 逐字重复（641 的形状当场再犯，已推不 amend、forward 点名）；'
          u'安装条目数 433→451 跨轮无门 ⇒ 开 **642**；换装排在验证链最前是顺序偏离（本轮靶就是换装）。\u3002'
          u'判据卷 @@CAPTURE@@；帧 @@FRAMES@@（**基线不 update**）；全量 @@FULL@@；build 0 告警；电池 @@BATTERY@@。\n')
t = once(t, anchor, anchor + fill(bullet), '§18 bullet')
if not check:
    wr(n, t)

# ---- BACKLOG：633 更新 + 新单 642 ----
n = 'AGENT_BACKLOG.md'
t = rd(n)
if '**642.' in t:
    sys.stderr.write('ALREADY_PATCHED backlog\n')
    sys.exit(1)
lines = t.split('\n')
idx = next(i for i, ln in enumerate(lines) if ln.startswith('**633.'))
end = idx
while end < len(lines) and lines[end].strip():
    end += 1
lines.insert(end, '    本轮（R566）推进的是**判据那一半**：`test_sign_bundle.py` 新增现读真钥匙串那一格（有身份 ⇒ 真签必须 `local`），'
                  '刀 M1474/M1475 各钉一种坏法；跨轮对拍（本轮那份 vs 上一轮备份）`CodeDirectory size=23793 hashes=737+3`、`Signature size=1900`、'
                  '`Authority=ClipboardHistory Local Signing` 逐字相同 ⇒ 身份不再靠一句话。**人工那一格仍开着**：'
                  '请用户在访达里对桌面文件夹**再授权一次**（签名身份变过 ⇒ 系统当新版本，这一次是最后一次），之后再复制一个桌面文件不该弹；'
                  '下一次若还弹，先现读 `SIGNATURE_KIND`（若成 `adhoc` 就是构建链回退，不是 TCC 抽风）。用户回执前不销单。')
entry = '''
**642. 安装条目数跨轮从 433 涨到 451 —— 同一版本、产品 `Sources/` 一字未动，而这一格从不判跨轮稳定**（R566 换装现读并新开）
    读数：R564/R565 两轮 `INSTALL_ENTRIES=433=433`；本轮 `INSTALL_ENTRIES_BEFORE=451 INSTALL_ENTRIES_AFTER=451`（before 数的正是 R565 装上去那一份 ⇒ 376…451 这一跳发生在"R565 打包"与"R566 打包"之间，而不是安装口径变了）。
    为什么这是个洞而不是噪音：条目数与包内容一起决定 CDHash，而 CDHash 决定 TCC 认不认"同一个 App"（633 的根因就在这条链上）。**授权能跨轮活下来**这句话的前提是包内容稳定；今天它涨了 18 条而**没有任何门说过一句**。
    现判据的缺口：`install_local.sh` 只判 `before == after`（同一份的两次数），跨轮比较从来不存在 ⇒ 这一格不许被读成"有门保着"。
    下一步（本轮不做，先数清再决定）：(i) 用备份目录 `before-before-R566` 与 `/Applications/时间剪史.app` 做**逐条名单差集**，数出那 18 条到底是什么（怀疑方向：`make bundle` 从 `.build/debug` 资源目录取 `AppIcon.icns` 之外的东西、`._*` AppleDouble 残留、`dot_clean` 不可用时的静默 `|| true`）；(ii) 分辨完再决定进门形状 —— 若那 18 条是垃圾 ⇒ 修打包并**降**条目数（棘轮只准降），配一把刀钉"垃圾回到包里必须红"；若是产品真需要的资源 ⇒ 把跨轮基准改成由 `make bundle` 自己打印的清单，而不是常量。'''
lines.append(entry)
io.open(n, 'w', encoding='utf-8').write('\n'.join(lines))
print('FINAL_REPORT_AND_BACKLOG books=2 check=%d' % (1 if check else 0))
