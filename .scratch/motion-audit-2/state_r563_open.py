# -*- coding: utf-8 -*-
"""R563 ⓪ 开工节 + 改掉 `### R562 补记` ④ 里那句与证据互斥的「636 本轮结案」。

两处动作都是**改账**：没有撤判据、没有降地板、没有加豁免。
"""
import io
import re
import sys

P = 'AGENT_STATE.md'
CHECK = '--check' in sys.argv

FIX_OLD = (u'**636 本轮结案**（缺陷断言被机制 + 像素两条证伪，判据与三把刀已落地，退场条件被显式改写成第三条 '
           u'—— 结案的是**我自己上一轮开的单**，不是别人给的门）')
FIX_NEW = (u'**636 半落地、单子继续开**（R563 改账：这一格从前写「本轮结案」，与同一轮里轮次节 ②(b) 和台账笔 `5d71660` '
           u'写的「半落地、继续开单」**互斥** ⇒ 按证据取后者 —— 三级项目符的墨 bbox 是**只印不判**的读数，'
           u'要给它定尺寸契约就得改 `bulletGlyph`/`markerFont`，那正撞 R549 与 R560 两个禁碰面 ⇒ 归用户点头。'
           u'**这是改账、不是改门**：没撤判据、没降地板、没加豁免，改的只是一个措辞；'
           u'矛盾成因也照实记 —— 补记笔写 ④ 时沿用了上一轮的口径措辞，没跟同一轮里已落盘的另外两处交叉核对）')

BODY = u"""## R563 ⓪ 开工（2026-11-03 · 第 562 轮 / Round 560 · CI 读单 + 基线全现读 + 一处账内矛盾改账 + 产品位待挑）

> 本节是**开工节**，不是轮次节（标题不写「状态」两字 —— `product_streak.py` 按第一个 `## Rnnn 状态（` 认当前轮）。

**前置实读**：`git log --oneline -1` = `75b32d6`；已跟踪改动 **0**；ahead=**0**（HEAD=origin=`75b32d6`）；`api.github.com=200 / www.apple.com=200`。

**① CI 读单（只登记、不轮询）**
- `41531750912 ↔ 75b32d6`（R562 那一批头笔 = 补记笔，含 R562 全部代码）状态 **queued、已等 229s**，`steps` 打的 `conclusion=` 是空串、`JOB build-and-test ⇒` 也是空 ⇒ 这是「**没有结论**」不是「没红」⇒ 本轮四格**具名 NOT-RUN**：(a) `HEAT_LEGEND_*` 这一跑走哪条 —— ⚠ 这一格本轮只是**复核**，首次签收已在 `41519677393↔f12f50d`（`格色=6 图例色=5 缺=[] 倍率=1.0x 地板 格4/图例4`、`NOT_RUN` 零行），不许记成第二次首次；(b) 本轮新那条 `BULLET_LEVELS` 在 runner 1x 走哪条；(c) `过渡帧数=` 第五数（已 2/5/0/5，每格 71.5/26.0/75.6/28.9ms）；(d) STEP[9] 第五跑 + STEP[18] 622。**不轮询、不推测**；收口前复述一次 `queue`，到数就把这四格改写成读数。
- (b) 的两条出路**预先写死**（读数站在边界上不许临场决定）：判到 ⇒ 报 `行/列/步进` 的 px 与 pt；打 `BULLET_LEVELS_NOT_RUN=detail-frame-plain` ⇒ 详情帧在 1x 没落墨（R483 家族）⇒ 具名入账并补内容墨证人，**不许读成「判过了」**；红在步进等距 ⇒ 先分辨是 1x 像素预算不够（合并容差在 1x 只剩 1px）还是产品真漂（对照 M1461 那条 16/19pt 的红形状）：前者按 `scale` 派生容差、**不许降墨下界、不许改期望、不许加豁免**，后者才是产品缺陷。⚠ 本机那次 LANCZOS 降采样体检只是**代理**，它不签这一格。
- (c) 的处置：读到几都按 629 既有口径具名入账，**不重开产品排查、不动 ≥2、不改期望**；若再次 ≤1，把「登记成 `sampled`」与「把尺改成对采样相位不敏感」两条出路的代价摆给用户 ⇒ **工作侧不自行登记 `sampled`**（那会改 CI 拦什么）。
- 同批无独立跑 ⇒ 具名 `CI_UNREAD`：R562 的 `327bc53`/`ff2cb9f`/`5d71660`/`c8c950f`、R561 的 `5e08357`/`a8adab4`/`324c513`、R560 五笔、R558 两笔。
- 永不重开：`41452722560 ↔ 58851c2`、`41455782587 ↔ 598b253`（cancelled、0 失败步骤、`log not found`）。

**② 基线全现读**（本轮一律命令派生，不抄上一轮正文）
- 帧基线 `docs/frame_baseline.json` ⇒ `count=356`（`frames` 字典同长 356；R562 从 354 涨到 356 的那两格就是新夹具的两档）。
- 预检名册 ⇒ `NEEDLE_PRECHECK tables=361 covered=295 arms=757 bad=0`、`ARM_TOTAL files=454 arms=1244 dupes=0 repeats=0`、`HIDDEN_ARMS 表=448 可判=1183 rot=0 抽不出=6 已声明表=6 处置=ok`（`/tmp/r563-precheck1.log`、`/tmp/r563-hidden1.log`；**串行**，`mutate_needle_precheck.py` 会真跑 swift，并行必撞锁）。
- 清账 ⇒ `LEDGER_ABSENCE_CLAIMS 格=162 声明=63` / `LEDGER_ABSENCE_RESULT=ok 不成立=0/63`。
- streak ⇒ `PRODUCT_STREAK ledger_round=561 streak=2 sections=537 last=631f910 last_round=559 newest=631f910 newest_round=559` ⇒ **产品面已连续两轮 0 文件 ⇒ 本轮必须落一个 `Sources/` 真实位**（收口那一格仍要台账落盘之后重读）。
- 刀号 ⇒ 扫 `.scratch/motion-audit-2/mutate_*.py` 全部 `M\\d{4}` 取最大 = **M1462**（`mutate_r562_widen_merge_window.py`）⇒ 本轮从 **M1463** 起（跳号/重复由 `ARM_TOTAL` 的 `dupes/repeats` 守）。
- 判据卷 / 全量卷 / 换装本轮**还没跑** ⇒ 具名 `NOT_RUN=this-round-not-yet-run`，按 ⑤ 的顺序跑到哪读到哪。

**③ 本轮先消掉的一处账内矛盾（改账，不是改门）**：`### R562 补记` ④ 写着「636 本轮结案」，而同一轮的轮次节 ②(b) 与台账笔 `5d71660` 都写「636 半落地、单子继续开（三级项目符的尺寸没有被判过）」⇒ 两处互斥。按证据取**继续开单**，本节把补记那一格逐字改齐（见该格里的改账说明与成因）。**没有撤判据、没有降地板、没有加豁免** —— 被改的只有一个措辞；两处矛盾不许并存到 R564。

**④ 第二格：本轮必须落一个真实产品面（`Sources/`）**。挑位方法写死，不许先定答案：① 现读清账表与盲区名册（`HIDDEN_ARMS` 的「抽不出=6」与名册里那些**有名字的未覆盖**）；② 逐张看帧（不是只看新夹具那两张）；③ 先列三条证伪（这条坏法会不会被既有判据抓到？旧值能不能从帧/结构量读出来？改它会不会撞禁碰面？）；④ 只有三条都过才动产品。合法判据：**有旧值→新值可报、有帧或结构量作证、至少两把刀**。禁碰 **11 面**一面对都不许碰；`.contentFade` 0.20 与所有声明时长一字不动；不许拿判据账/夹具账冒充产品位。

**⑤ 本轮三条前置自检**（前两轮自伤直接写成的规矩）：① 台账生成器**每一本都要有幂等守卫**（R562 只给一本加 ⇒ 中途崩之后重跑把 UI 那一本写成两份，被唯一性判据抓真红），且**守卫搜索的串不许出现在守卫自己写的正文里**；② 落盘之后回读一次并给出未渲染占位符计数（`%(?=[a-zA-Z])` 在本轮节内 = 0）；③ 声称「逐字」之前先用 `startswith` 对一遍；CJK 串里不许 ASCII 双引号，写盘脚本先 `py_compile`；电池只抄它自己打印的 `Ran/OK/FAILED`，`&&` 里不插 grep。

"""


def main():
    t = io.open(P, encoding='utf-8').read()
    if t.count(FIX_OLD) != 1:
        sys.stderr.write('ANCHOR_BAD r562_④_636 hits=%d\n' % t.count(FIX_OLD))
        return 1
    anchor = u'## R562 状态（2026-11-03 · 第 561 轮 / Round 559 · 产品 0 文件 + 夹具 1 张 + 判据 1 条 + 三把刀）'
    if t.count(anchor) != 1:
        sys.stderr.write('ANCHOR_BAD state R562 状态节 hits=%d\n' % t.count(anchor))
        return 1
    if u'## R563 ⓪ 开工' in t:
        sys.stderr.write('ALREADY_WRITTEN\n')
        return 1
    if not CHECK:
        t = t.replace(FIX_OLD, FIX_NEW, 1)
        t = t.replace(anchor, BODY + anchor, 1)
        t = re.sub(u'最后更新：2026-11-03（本地 · R562 / 第 561 轮 / Round 559）',
                   u'最后更新：2026-11-03（本地 · R563 / 第 562 轮 / Round 560）', t, count=1)
        io.open(P, 'w', encoding='utf-8').write(t)
    sys.stdout.write('STATE_R563_OPEN_%s\n' % ('CHECK_OK' if CHECK else 'WRITTEN'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
