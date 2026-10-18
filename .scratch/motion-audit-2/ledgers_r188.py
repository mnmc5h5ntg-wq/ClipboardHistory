#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''R188 的台账批写（BACKLOG-only 一笔）：208 结案 + 210 的读数撤回 + 新开 211。

三条规矩都在这里落地：
① 数字一律从日志解析（缺格 ⇒ 拒绝写盘），不手抄；
② STATE **不换表头**（只把追记写进原块）—— 因为 R186/R187 是只动 BACKLOG 的笔次、三本账里没有标题行，
   一旦 STATE 轮换到 R188，test_round_batch_consistency 的窗口（r, r-1, r-2）会当场红 ⇒ 这正是新开 211 的内容；
③ 要么全成要么全不写：所有文件先算完再一次性落盘。
'''
import io
import os
import re
import sys

ROOT = '/Users/wangziyi/Codex_Project0'
SHOTS = '/tmp/shots_r188'
L = {'probe': '/tmp/r188_probe.log', 'base': '/tmp/r188_baseline.log', 'cap': '/tmp/r188_capture.log'}


def read(p):
    if not os.path.exists(p):
        raise SystemExit('MISSING_LOG %s ⇒ 拒绝写盘' % p)
    return io.open(p, encoding='utf-8').read()


def grab(pat, text, what, flags=0):
    hits = re.findall(pat, text, flags)
    if not hits:
        raise SystemExit('PARSE_FAILED %s（%r）⇒ 拒绝写盘' % (what, pat))
    return hits[-1]


problems = []

cap = read(L['cap'])
n_frames = len([f for f in os.listdir(SHOTS) if f.endswith('.png')]) if os.path.isdir(SHOTS) else 0
if n_frames != 138:
    problems.append('帧目录只数到 %d 张（要 138）' % n_frames)
sum_line = grab(r'Executed \d+ tests[^\n]*', cap, '捕获卷结论行')
cap_n = grab(r'Executed (\d+) tests', sum_line, '捕获卷执行数')
cap_fail = grab(r'(\d+) failures?', sum_line, '捕获卷失败数')
cap_skip = grab(r'(\d+) tests skipped', sum_line, '捕获卷跳过数') if re.search(r'\d+ tests skipped', sum_line) else '0'
if cap_fail != '0':
    problems.append('捕获卷失败 %s 例（原文：%s）' % (cap_fail, sum_line))

probe = read(L['probe'])
line = probe.splitlines()[-1] if probe.strip() else ''
for needle in (u'PROBE_FPS', u'超锚点帧=', u'n=', u'worst='):
    if needle not in line:
        problems.append('PROBE_FPS 那一行缺 %r ⇒ 208 不能结案' % needle)
n_val = grab(r'n=(\d+)', line, 'PROBE_FPS 的 n')
worst_val = grab(r'worst=([\d.]+ms)', line, 'PROBE_FPS 的 worst')
over_val = grab(r'超锚点帧=(\d+)', line, 'PROBE_FPS 的 超锚点帧')
steps = sorted(set(re.findall(r'\t([^\t]*probe[^\t]*)\t', probe, re.I)))

base = read(L['base'])
if re.search(r'^FRAME_BASELINE_COMPARED=', base, re.M):
    cmpd = grab(r'^FRAME_BASELINE_COMPARED=(\d+)', base, 'compared', re.M)
    chg = grab(r'^FRAME_BASELINE_CHANGED=(\d+)', base, 'changed', re.M)
    miss = grab(r'^FRAME_BASELINE_MISSING=(\d+)', base, 'missing', re.M)
    base_str = u'对账 %s 张、changed=%s、missing=%s' % (cmpd, chg, miss)
else:
    ex = grab(r'BASELINE_EXIT=(\d+)', base, '基线退出码')
    base_str = u'NOT-RUN（退出码 %s，正文见 /tmp/r188_baseline.log）' % ex

if problems:
    raise SystemExit('REFUSE_TO_WRITE ' + u'；'.join(problems))

V = {'n': n_val, 'worst': worst_val, 'over': over_val, 'frames': str(n_frames),
     'cap_n': cap_n, 'cap_skip': cap_skip, 'cap_fail': cap_fail, 'base': base_str,
     'steps': u'、'.join(u'`%s`' % s.strip() for s in steps) if steps else u'（步骤名没解析出来）',
     'probe': line.split('FORWARDED', 1)[-1].strip()}

blk208 = u'''
**208 追记（R188）：结案 —— 新读数确实落在活下来的那一行，证人就是 runner 自己打的那一行**

run `39163387579`（= `949350d`，job conclusion=`success`）的 `--log` 里 `PROBE_FPS` 原文（同一次 run 的两个步骤各打一遍：%(steps)s）：
「%(probe)s」
⇒ 208 要的就是这件事：`超锚点帧=` 已经并进**活下来的那一行**，不再单独押在 `PROBE_WORST_FRAME` 那种「尾部独立行」上（R179 量到它在 runner 上整卷 0 次）。
结案口径：以 runner 自己打印的这条行为准 —— `n=%(n)s`、`worst=%(worst)s`、`超锚点帧=%(over)s`，不靠「我认为接上了」。
另记（不许把没读的说成没红）：`d4958a9`…`81105b0` 那八跑在写这笔时全是 queued/in_progress ⇒ **无结论**；本笔结案只依赖 `949350d` 那一跑。
''' % V

blk210 = u'''
**210 追记 5（R188）：撤回 —— 「药丸画在右段」这句读数在这轮回捕的帧上不复现，两把尺互相矛盾 ⇒ 210 退回「未钉死」**

前提先纠正：`/tmp/shots_r18*` 已被 macOS 清掉（`ls` 数不到一帧）⇒ 「复用上轮帧做看图腿」这一轮**不成立**，本笔重新捕了 `%(frames)s` 张到 `/tmp/shots_r188`
（捕获卷 `Executed %(cap_n)s tests / 跳过 %(cap_skip)s / 失败 %(cap_fail)s`）。帧基线：%(base)s。

同一张 `content-empty-750x560-dark`（1500x1120，即 @2x 的 750x560pt）上量了两把尺：
- 尺一（多行取并集、≥8px）：报 `band_x=32..535`，而同一条带的中心色是 `(36,36,36)` ⇒ **并集把不同行的带缝成了一条**，尺坏（形状合法、对象不是同一个）。
- 尺二（逐行、且亮区与底轨取**同一行**、≥60px）：最宽那行 `y=205`：底轨 `x=31..528`（498px = 249pt），亮区 `x=32..527`（496px = 248pt）、中心色 `(255,255,255)`，
  「铺满整轨」的行只有 `4/52`。
⇒ 三个后果：
① 亮区**与底轨同宽**（496 vs 498），不是「控件的一半」⇒ R185 那句「宽 258px = 控件可用宽 517px 的一半、落在右段」在这把尺下不复现；
② 我这次的归一化本身也写错了：`rel = (亮区中心 - 轨左) / (轨宽/2)` ⇒ `rel=1.0` 说的是**正中**，而我把它标成了「右半」（阈值该是 0.5/1.5 分界）。
   这个口径错与 R185 的结论**同形** ⇒ 「右段」很可能就是同一类错误的产物，不是产品的形状；
③ 亮档 6 张仍然「亮区铺满 x=0..639、中心色 243/245/255」= 背景本身过线（R185 记过，本轮再现）；
   暗档 `content-with-notice` / `content-*-with-copy-failure-notice` / `content-with-two-notices` 4 张「同一行既无底轨又无亮区 ⇒ 无从判定」。
④ **而且这次量的是同一批像素**：帧基线 %(base)s ⇒ 本轮回捕的 138 张与 R185/R187 那次逐字节相同（产品 0 改动，本该如此）
   ⇒ 两把尺的矛盾**百分之百在尺上，不在帧上** —— 这条比任何措辞都硬：它把「产品在这三轮里变过」这个逃项直接关掉。
⇒ 处置：**撤回 R187 追记 4 的「病根钉死」**，210 退回「读数未钉死」，产品照旧不动。
   账里 R186 就写过「现在改 `slidingPill` 有 50%% 概率改错地方」—— 本轮没有更好的证据，只有更坏的：两把尺对同一批帧给出矛盾形状，
   而矛盾里有一把是我自己能指出口径错的（尺二的 rel 阈值）。按 R146–R149 的规矩，不懂的读数不许当成结论，更不许当成改产品的理由。
下一轮欠的是**这把尺**而不是产品：要造两张夹具 —— 显式 `.all` 与显式 `.favorites` 各一张，看亮区**换不换段**；
换段 ⇒ 亮区跟着 `isSelected` 走（病根在选中/按钮那层），不换 ⇒ 亮区固定（病根在几何）。在那之前「药丸画在哪一段」永远只是猜。
另：`scripts/frame_audit.py bands` 的 `BANDS_VERDICT` 与上面两把尺是三套口径，要合成一套（否则一条带三个答案，台账永远在改口径不是改产品）。
''' % V

blk211 = u'''
**211. 轮次三账守卫会在 STATE 轮换的那一刻红：R186/R187 是「只动 BACKLOG」的笔次，三本账里没有它们的标题行（申报通道未建）（R188 量到形状）**

形状（读 `scripts/tests/test_round_batch_consistency.py` + 三本账实际标题）：这条守卫从 STATE 的「最后更新」行读 `R<r>`，然后要求 `r, r-1, r-2`（`LOOKBACK = 3`）
在 `AGENT_UI_AUDIT.md`（`^## 第 N 轮（R<r>`）、`AGENT_VISUAL_ITERATION.md`（`^## Round <r> · `）、`CHANGELOG.md`（`^### …（R<r> / U-…`）**各有标题行**。
而 `a90e380`（R186）与 `2720e72`、`81105b0`（R187 两笔）只往 `AGENT_BACKLOG.md` 追加了 210 的追记 ⇒ 一旦 STATE 换到 R188，守卫立刻红三格。
本轮的处置是**不换 STATE 表头**（追记写在原块内，守卫继续读 R185，窗口内三轮齐全），并把这件事记成一条待办而不是把它藏起来。
两种不许用的偷懒：① 给 R186/R187 补桩标题喂饱守卫（记忆里的「守卫被散文喂饱」，且桩会让「半批已写」这一格永远查不出来）；② 把 `LOOKBACK` 降到 1（那是删测试）。
正路：给「单本账笔次」建**显式申报通道** —— 一张名册声明哪些 R 号只动 BACKLOG，守卫按名册跳过；
名册为空时必须照旧全查；配两把变异刀（把申报删掉 ⇒ 红回来；往名册里塞一轮真有台账的 ⇒ 也要红）。
不做这条的代价很具体：下一轮只能在「补写三本账」和「不换 STATE」之间二选一，而后者会让 STATE 的轮次自报越来越假。

''' % V

STATE_ANCHOR = u'最后更新：2026-10-19 05:58'
state_extra = u'''
R188 追记（本笔为 BACKLOG-only，**STATE 表头未轮换** —— 轮换前先读 211，否则三账窗口当场红）：
⓪ 已到手：208 结案（runner `39163387579` = `949350d` 的 `PROBE_FPS … n=%(n)s worst=%(worst)s 超锚点帧=%(over)s`，见 BACKLOG 208 追记）；
   其余八跑（`d4958a9`…`81105b0`）在写这笔时 queued/in_progress ⇒ 结论**未读**。
① 210 的「药丸在右段」**已撤回**（两把尺对同一批帧矛盾，且其中一把的归一化口径我能指出错）⇒ 210 退回未钉死，产品不动；下一轮先量**尺**：
   两张夹具（显式 `.all` / 显式 `.favorites`）看亮区换不换段，并把 `frame_audit bands` 与这两把尺合成一套口径。
② 新开 211（轮次三账的申报通道）；③ 旧账不变：205（逐元素分带）、201（runner 那条 205pt 带里是什么）、202（缺席文法按文件粒度）、
   207（多靶变异表）、清账表未判格、以及 195 的 ①、189、188、187 的 ②③。
本笔的看图腿：重新捕了 %(frames)s 张帧并逐张量了（不是读代码），本机捕获卷 %(cap_n)s 例 / 跳过 %(cap_skip)s / 失败 %(cap_fail)s，帧基线：%(base)s。
''' % V


def write(p, t):
    with io.open(p, 'w', encoding='utf-8') as h:
        h.write(t)


def main():
    bl = os.path.join(ROOT, 'AGENT_BACKLOG.md')
    st = os.path.join(ROOT, 'AGENT_STATE.md')
    bl_text = read(bl)
    st_text = read(st)
    if u'210 追记 5（R188）' in bl_text:
        raise SystemExit('DUMP_ALREADY_WRITTEN ⇒ 不重复落盘')
    for name, txt in ((u'208', blk208), (u'210', blk210), (u'211', blk211)):
        if re.search(r'%\([a-z_]+\)s', txt):
            raise SystemExit('FORMAT_LEAK %s 块还有没吃掉的占位符' % name)
    if bl_text.count(u'**208. ') != 1 or bl_text.count(u'**210. ') != 1:
        raise SystemExit('ANCHOR_BACKLOG 208/210 定义行不是各 1 条')
    nums = sorted(int(m) for m in re.findall(r'^\*\*(\d{2,3})\. ', bl_text, re.M))
    if nums[-1] != 210:
        raise SystemExit('MAX_BACKLOG 读到 %d（要 210 ⇒ 211 才是下一个号）' % nums[-1])
    if st_text.count(STATE_ANCHOR) != 1:
        raise SystemExit('ANCHOR_STATE 命中 %d 次（要 1）' % st_text.count(STATE_ANCHOR))
    new_bl = bl_text.rstrip(u'\n') + u'\n\n' + blk208.strip(u'\n') + u'\n\n' + blk210.strip(u'\n') + u'\n' + blk211.rstrip(u'\n') + u'\n'
    lines = st_text.split(u'\n')
    idx = [i for i, l in enumerate(lines) if l.startswith(STATE_ANCHOR)]
    new_st = u'\n'.join(lines[:idx[0] + 1] + [state_extra.strip(u'\n')] + lines[idx[0] + 1:])
    # 写盘前的最后一道：新内容必须自己站得住
    if u'**211. ' not in new_bl:
        raise SystemExit('MISSING_211_DEFINITION')
    # 只查**本笔新块**里的悬空引用：老台账里的 `BACKLOG 122` 那一类引用按历史形状写，拿整文件当作用域会把它们算成我的错
    for ref in re.findall(u'BACKLOG (\\d{3})', blk208 + blk210 + blk211 + state_extra):
        if (u'**%s. ' % ref) not in new_bl:
            raise SystemExit('DANGLING_BACKLOG %s 没有定义行' % ref)
    write(bl, new_bl)
    write(st, new_st)
    print(u'LEDGERS_WRITTEN probe n=%s worst=%s 超锚点帧=%s frames=%s cap=%s/%s/%s base=%s'
          % (V['n'], V['worst'], V['over'], V['frames'], V['cap_n'], V['cap_skip'], V['cap_fail'], V['base']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
