# -*- coding: utf-8 -*-
"""R562 ⓪ 开工节：CI 读单（头笔 queued ⇒ 三格具名 NOT-RUN）+ 基线全现读 + 第二格选定（636 退场第一步＝夹具）。"""
import io
import re
import sys

P = 'AGENT_STATE.md'
CHECK = '--check' in sys.argv

BODY = u"""## R562 ⓪ 开工（2026-11-03 · 第 561 轮 / Round 559 · CI 读单 + 基线全现读 + 第二格选定）

> 本节是**开工节**，不是轮次节（标题不写「状态」两字 —— `product_streak.py` 按第一个 `## Rnnn 状态（` 认当前轮）。

**前置实读**：`git log --oneline -1` = `f12f50d`；已跟踪改动 **0**；ahead=**0**（HEAD=origin=`f12f50d`）；`api.github.com=200 / www.apple.com=200`。

**① CI 读单（只登记、不轮询）**
- `41519677393 ↔ f12f50d`（R561 那一批头笔 = 补记笔，内容含 R561 全部代码）状态 **queued、已等 232s**，`steps` 打出的 `conclusion=` 是**空串**、`JOB build-and-test ⇒` 也是空 ⇒ 这不是「没红」，是**没有结论** ⇒ 本轮三格**具名 NOT-RUN**：(a) 几何派生尺 `SolidRuler` 在 runner 的真 1x 帧上到底判没判到（预期 `HEAT_LEGEND_COVERAGE … 倍率=1.0x 地板 格4/图例4`，若仍 `solid-unresolved` ⇒ 是派生式算错、不是产品问题）；(b) `过渡帧数=` 第四个 runner 真数（三跑已 2/5/0）；(c) STEP[9] `SKIP_ROSTER` 第四跑 + STEP[18] 622。**不轮询、不推测、不拿「应该绿了」当读数**；收口前复述一次 `queue`，到数就把这三格改写成读数（R559/R560/R561 三连都是这么办的）。
- 同批无独立跑 ⇒ 具名 `CI_UNREAD`：R561 的 `5e08357`/`a8adab4`/`324c513`、R560 的 `0a49b5f`/`631f910`/`700dee9`/`8004a42`/`22bd17d`、R558 的 `b8949f5`/`1ea1bb7`。
- 已读、不必重读：`41509855001 ↔ 26c1939` = concluded failure，只红 STEP[19] `Motion coverage floor`（四格读数在 `### R561 补记` ②，629 的第三数=0 已按既有口径入账）。
- 永不重开：`41452722560 ↔ 58851c2`、`41455782587 ↔ 598b253`（cancelled、0 失败步骤、`log not found`）。

**② 基线全现读**（本轮一律命令派生，不抄上一轮正文）
- 帧基线名单：`python3 -c "import json;print(json.load(open('docs/frame_baseline.json'))['count'])"` ⇒ **354**（`frames` 字典同长 354）。
- 预检名册：`NEEDLE_PRECHECK tables=358 covered=295 arms=757 bad=0`；`ARM_TOTAL files=451 arms=1244 dupes=0 repeats=0`；`HIDDEN_ARMS 表=445 可判=1183 rot=0 抽不出=6 已声明表=6 处置=ok`（`scripts/hidden_arms.py` **没有** `--arm-total` 这个参数 ⇒ `ARM_TOTAL` 那行由 `mutate_needle_precheck.py` 自己打，第一次抄 `hidden_arms.py --arm-total` 得到的是 usage 报错 + 退出码 2，不是读数）。
- 清账表：**162/63/0**；streak：`PRODUCT_STREAK ledger_round=560 streak=1 last=631f910 last_round=559 newest=631f910 newest_round=559`（本轮是**开工现读**，收口那一格仍要台账落盘之后重读）。
- 刀号现读最高 **M1459** ⇒ 本轮从 **M1460** 起（跳号/重复由 `ARM_TOTAL` 的 `dupes/repeats` 守）。
- 判据卷 / 全量卷 / 换装本轮**没有现读**（它们是上一轮的收口读数）⇒ 具名 `NOT_RUN=this-round-not-yet-run`，按 ⑤ 的顺序跑到哪读到哪。

**③ 第二格选定（本轮必须落一个真实面）**
- 优先序 ①（⓪(a) 若仍走出口就修派生式）**今天不能选** —— 不是被现读否掉，是那条读数**还没到**（queued ⇒ NOT-RUN）。把它写成 R563 的 ⓪ 头格，到数就照口径修（不许降地板、不许改期望、不许加豁免）。
- 所以本轮走优先序 ②：**636 的退场第一步＝补一个能画到 depth1/depth2 的夹具**，让 `◦` 与 `▪` 第一次有帧对象，再按「三级同尺寸」量。为什么不破 R549 禁碰：禁碰的是产品那颗 `⦁` 的**绘制面**（`BULLET_INK` 那次改的是 glyph 选择与墨高），夹具只是喂给它的正文（`Tests/` 里的多行串），产品一行不动。
- ⚠ 三条诚实前置：① 夹具新捕的帧会让帧名单**上涨** ⇒ 必须走同一笔 `frame_baseline.py update` 并写进台账那一笔，名单外一个帧不许有；② 若判据量出三级**不同尺寸** ⇒ 改产品会同时撞 R549（`⦁` 那颗）与 R560（`markerFont(for:)` 任务标记）两个禁碰面 ⇒ **本轮不动产品**，把读数、代价与两条出路摆给用户；③ 若量出三级**同尺寸** ⇒ 636 那条「`▪` 落到冬青黑体」按 R560 定的契约（**判的是像素同尺寸，不是字体名相同**）就不成立 ⇒ 具名写清是「按现口径不判为缺陷」还是「结案」，不许把两种说法混着写。
- 本轮**先看像素再看判据**：夹具捕出来的帧必须真看过图（`CLIPBOARD_HISTORY_UI_SHOTS` 重捕 → 逐张看那三级列表），不许只拿读数收口。

**④ 刀的自检（登记之前）**：每把新刀先量「它让读数变了多少、变化量落在容差之外没有」——同值空刀与落在 ≤1px 容差内的空刀都是空刀（R560 那把 Menlo 差 1px 是第二形态），空刀不许登记、照实写进账。

**⑤ 本轮三条前置自检**（R561 的自伤直接写成的规矩）：① 台账生成器**落盘之后回读一次**并给出未渲染占位符计数（`%(?=[a-zA-Z])` 在本轮那一节 = 0 才算写完）；② 账里声明「逐字」之前先用 `startswith` 跟真日志对一遍，`ci_read.py readings` 的打印窗口截掉的部分**不许手补**、要标注截断；③ CJK 串里不许出现 ASCII 双引号，写盘脚本先 `py_compile` 再落。

"""


def main():
    t = io.open(P, encoding='utf-8').read()
    anchor = u'## R561 状态（2026-11-03 · 第 560 轮 / Round 558 · 产品 0 文件 + 判据 1 条 + 真值表 + 三把刀）'
    if t.count(anchor) != 1:
        sys.stderr.write('ANCHOR_BAD hits=%d\n' % t.count(anchor))
        return 1
    if u'## R562 ⓪ 开工' in t:
        sys.stderr.write('ALREADY_WRITTEN\n')
        return 1
    if not CHECK:
        new = BODY + anchor
        t = t.replace(anchor, new, 1)
        t = re.sub(u'最后更新：2026-11-03（本地 · R561 / 第 560 轮 / Round 558）',
                   u'最后更新：2026-11-03（本地 · R562 / 第 561 轮 / Round 559）', t, count=1)
        io.open(P, 'w', encoding='utf-8').write(t)
    sys.stdout.write('STATE_R562_OPEN_%s\n' % ('CHECK_OK' if CHECK else 'WRITTEN'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
