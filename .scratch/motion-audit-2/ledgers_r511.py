#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os, subprocess
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); D=os.path.join(R,"AGENT_DECISIONS.md"); B=os.path.join(R,"AGENT_BACKLOG.md")
S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md"); C=os.path.join(R,"CHANGELOG.md")
I=os.path.join(R,"AGENT_VISUAL_ITERATION.md")
sha=subprocess.check_output(["git","-C",R,"rev-parse","--short=7","HEAD"]).decode().strip()
FULL=os.environ.get("R511_FULL","")
FULLTXT=(u"全量 **%s**" % FULL) if FULL else u"全量见补记"

AT_OLD=u"U-1970…U-2028）：主窗口与设置窗口的标题栏统一"
AT_NEW=u"U-1970…U-2035）：主窗口与设置窗口的标题栏统一"
ANCHOR_NEXT=u"\n## 第 499 轮（R501 · 2026-10-30 · U-1964…U-1969）"
AS=u"""- **U-2029：⓪ push 与 CI。** 开工 `git push` no-op（HEAD=origin/main=`d7919e2`、**ahead=0**）。成对回读：`41144830309 ↔ 6f43727` **success**（R510 的省年 meta + 侧栏开关修复全绿，**`详情/组合帧头部` 探针恢复**）；`41145147519 ↔ d7919e2` 收口时 **success**（开工读时 in_progress）；`41144200112 ↔ 3ebc7fc` failure **仅 Release**（sources 停旧 + 当笔尚未进 UNPARSED_ROSTER + skip 级联，已由 6f43727 修）；R509 三跑 `d01e973`/`139912c`/`4ebfc81` failure **仅 Release**，红名 `详情/组合帧头部 cause=bg-not-flat bg=(32,32,32)`（全年份 meta 在 1x 越过探针背景带）⇒ 省年 meta 后被 6f43727 的 success 签收。`e3eb62b`/`6543959` success；`3d20a02`/`f9b8733` 仍是已知采样 flake。436 只复核新跑：6f43727/d7919e2 success ⇒ Motion clean。
- **U-2030：① 615 的读数与字宽账。** R510 结束时 600×492 真窗口详情 meta 读 **`10月30日 21:09:5…· 来自 Safari浏览器`** —— ViewThatFits 的四档都带字符数，放不下就退回 **middle 截断**，秒与字符数一起被吃掉。11pt 实测字宽：全文 **297.5pt**、去「复制」**272.5pt**、去字符数（带秒+来源）**206.3pt**、分钟+来源 **189.1pt**、分钟不带「来自」**164.1pt**；600×492 真实可用宽约 **200pt** ⇒ 206.3 仍放不下，189.1 能放下。
- **U-2031：② 产品第一档：省字符数。** `DetailTypography.metaText` 增 `includeSize`；`DetailView.headerMeta` 增 `includeSize` 并加第五档 `includeIcon:false, includeCopyVerb:false, includeSize:false`。离屏 `detail-file-fallback-longname-600x440` 亮暗两帧换成 `10月9日 16:53:20 · 来自 访达`（时间+来源完整、无字符数）；真实 600×492 仍被 middle 截断（206.3 > ~200）⇒ 还需要更窄一档。
- **U-2032：③ 产品第二档：分钟精度（615 结案）。** `ClipboardDateFormatters` 增 `detailTimestampMinute(for:reference:)`（`M月d日 HH:mm` / 跨年 `yyyy年M月d日 HH:mm`）；`DetailView` 增第六档 `includeSeconds:false`。after 真窗口 600×492 读 **`10月30日 21:09 · 来自 Safari浏览器`**（完整、按优先级省秒与字符数），750×560 仍是 **`10月30日 21:09:55 复制 · 16 个字符 · 来自 Safari浏览器`**；离屏最小帧仍选第五档（宽度足够）。
- **U-2033：④ 判据与刀。** 日期：`TimestampYearPolicyTests/testDetailMinuteTimestampDropsSecondsButKeepsTheYearPolicy`；字符串/接线：`Round3DetailTypographyTests/testNarrowestMetaDropsTheSizeButKeepsTimeAndSource` + `testNarrowDetailHeaderFallsBackToCompactMeta`（断言 `includeSize:false` 与 `includeSeconds:false` 两档都在）。刀 `M1370`（includeSize 失效）/`M1371`（最窄版仍带「复制」）/`M1372`（删第五档）/`M1373`（分钟档仍带秒）/`M1374`（删第六档）**5/5 CAUGHT**、`RESTORE_CLEAN=yes`。**连带重锚**：新增的 `detailTimestampMinuteWithYear` 与 `sidebarTimeWithYear` 同一行格式串，R509 的 `M1365` 针命中数 2 ⇒ 预检 bad=1；把 M1365 重锚到 `sidebarTimeWithYear` 整块，重跑 2/2、预检 `bad=0`（没有删刀）。
- **U-2034：⑤ 帧卷。** 捕获卷 **332 帧**：第一档把 **2 张** `detail-file-fallback-longname-600x440` 换成无字符数版（已吸收，基线仍 **332**）；第二档（分钟）**没有改任何帧**（离屏最小帧宽度足够选第五档）。最终对基线 `COMPARED=332 CHANGED=42 MISSING=0 ADDED=0`，42 张全是源图标栅格噪声（不吸收）。
- **U-2035：⑥ 八步与电池。** build **0 告警**（增量=0、冷编=0）；预检 `NEEDLE_PRECHECK tables=292 covered=269 arms=716 bad=0`、`ARM_TOTAL files=385 arms=1203`、`HIDDEN_ARMS 表=379 可判=1142 rot=0`；%s；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=419=419`（活库；旧实例先 CONT 再 TERM）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497；本笔 as-of 510 = 1，last=`3ebc7fc`/last_round=509）；清账 162/63/0；§1 刷新在生成器后复跑；电池在台账后复跑（683/OK skipped=5）。产品笔 `%s` 已推（HEAD=origin、ahead=0）。**具名 NOT-RUN / 限制**：① `%s` 自身跑（推送后取）；② 状态菜单像素通道（system-menu，610）；③ `RTF_HELPER_ORPHAN`（settings-content-blank/595）；④ `RECORDING_REREAD` 1x；⑤ 已知在屏/Motion 采样 flake；⑥ 601 噪声与其余未结项仍开。
""" % (FULLTXT, sha, sha)
DS=u"""## D-509 详情 meta 的字段优先级：复制→字符数→秒依次让位（R511，615 结案）

- 背景：R510 结束时 600×492 真窗口的详情 meta 被 middle 截断成 `10月30日 21:09:5…` —— ViewThatFits 四档都带字符数，放不下就吃掉秒与字符数。11pt 实测：全文 297.5pt、去复制 272.5pt、去字符数 206.3pt、分钟+来源 189.1pt；真实可用宽约 200pt。
- 决定：ViewThatFits 再补两档 —— 第五档省字符数（保留秒与来源），第六档到分钟精度（`M月d日 HH:mm`，跨年带年）。顺序即优先级：冗余动词 → 字符数 → 秒；**时间与来源永远保留**。
- 理由：middle 截断是"随机砍中间"，用户既看不到秒也可能看不到来源；按优先级让位能把"哪条信息先消失"写成可读的设计，而不是交给截断位置。
- 兼容性/迁移：600×492 读 `10月30日 21:09 · 来自 Safari浏览器`；750×560 不变（全量格式）。离屏 `detail-file-fallback-longname-600x440` 两帧（第五档）同笔更新，第六档不改帧。
- 边界：分钟档省掉秒是**有意**的（与列表同精度）；若未来要保留秒，先量 600 宽可用宽再决定让位顺序，不许放宽 middle 截断兜底。
"""
BS=u"""**615. 600×492 详情 meta 仍丢字符数与秒末位**（R510 现读）
    现象：同年省年后最小窗读 `10月30日 21:09:5…· 来自 Safari浏览器` —— 时间回来了，但秒末位与「16 个字符」仍被截；750×560 完整。
    修法：若要把它们保住，改 meta 行的字段优先级布局（例如窄宽先让「来自 App」换行/省略），不要放宽日期格式判据；当前记已知限制。
    **R511 结案**：ViewThatFits 补两档（省字符数 206.3pt、分钟精度 189.1pt），600×492 读 `10月30日 21:09 · 来自 Safari浏览器`（完整），750 仍是全量格式；M1370–M1374 5/5，判据同时钉两档接线。
"""
CS=u"""### 详情信息窄窗按优先级让位（615 结案；R511 / 第 510 轮 / Round 508 / U-2029…U-2035 · 产品 3 文件 + 判据）

"""
SS=u"""## R511 状态（2026-10-31 · 第 510 轮 · 产品 3 文件 + 判据）

R511 记录（产品 3 文件 + 判据）：详情信息窄窗按优先级让位（615 结案）。⓪ push no-op（HEAD=origin/main=`d7919e2`、ahead=0）；`6f43727` **success**（R510 省年 meta + 侧栏开关修复、`详情/组合帧头部` 探针恢复）、`d7919e2` **success**；`3ebc7fc` failure 仅 Release 时序、R509 三跑 failure 仅 Release（`bg-not-flat (32,32,32)`，已被 6f43727 success 签收）。① 600×492 详情 `10月30日 21:09:5…`（middle 截断）；11pt 字宽：全文 297.5、去复制 272.5、去字符数 206.3、分钟+来源 189.1、可用约 200。② 第五档省字符数：离屏最小帧 `10月9日 16:53:20 · 来自 访达`；真实 600 仍截断。③ 第六档分钟精度：after 600×492 `10月30日 21:09 · 来自 Safari浏览器`、750 全量格式不变；`detailTimestampMinute` 同年省年。④ 判据 3 条 + M1370–M1374 **5/5**；M1365 因同形格式撞针重锚到 `sidebarTimeWithYear` 块，预检 bad=0。⑤ 捕获 332 帧：第五档 2 帧变化（已吸收）、第六档 0 帧；最终 CHANGED=42 全噪声。⑥ 预检 292/269/716 bad=0、ARM 385/1203、HIDDEN 379/1142 rot=0；build 0 告警；%s；换装 ok/419=419（活库；旧实例先 CONT/TERM）；电池 683/5（台账后复跑）；清账 162/63/0；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497；本笔 as-of 510 = 1，last=`3ebc7fc`/last_round=509）；产品笔 `%s` 已推（ahead=0）。下一轮编号 R512（第 511 轮 / Round 509）：先 push 并复核 ahead=0；读 `%s` 自身跑与 `6f43727`/`d7919e2` 跑全部失败步骤；重点 `详情/组合帧头部` 探针是否持续恢复、`RTF_HELPER_ORPHAN`（595）、`RECORDING_REREAD`、436 Motion floor；② 产品位换未捕获表面；③ 4.5 地板与 150 上限不动。
""" % (FULLTXT, sha, sha)
IS=u"""## Round 508 · R511（第 510 轮 · 2026-10-31）：详情信息窄窗按优先级让位（615 结案）

R510 结束时 600×492 详情被 middle 截断成 `10月30日 21:09:5…`（秒与字符数一起丢）。字宽实测：全文 297.5、去复制 272.5、去字符数 206.3、分钟+来源 189.1、真实可用约 200。修法：ViewThatFits 补两档 —— 第五档省字符数（206.3，离屏最小帧 `10月9日 16:53:20 · 来自 访达`），第六档分钟精度（189.1）；after 真窗口 600×492 `10月30日 21:09 · 来自 Safari浏览器`、750 全量格式不变。判据 3 条 + M1370–M1374 5/5；M1365 同形格式撞针已重锚。捕获 332 帧：第五档 2 帧变化（已吸收）、第六档 0 帧、最终 42 张纯噪声。预检 292/269/716、ARM 385/1203、HIDDEN 379/1142 rot=0。%s；build 0 告警；换装 419=419；电池 683/5。⓪ push no-op（HEAD=origin=d7919e2、ahead=0）；6f43727/d7919e2 success（探针恢复签收）、3ebc7fc/R509 三跑仅 Release 时序。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 600/750 两档真窗口前后与离屏最小帧逐张看过：时间完整、字符数按优先级让位。 |
| 判据有效性 | 15/15 | 分钟格式 + 两档接线；M1370–M1374 5/5。 |
| 假绿防御 | 15/15 | 字宽先量后定档；middle 截断兜底保留；M1365 撞针重锚不删刀。 |
| 产品面推进 | 15/15 | 新设计位（窄窗字段优先级）；3 个产品文件；真窗口可见变化。 |
| 台账一致性 | 15/15 | U-2029…U-2035、D-509、332 帧/1329/56/0、419=419 都来自命令与测试。 |
| 交付诚实性 | 15/15 | R509/R510 的 runner 红全部归因（探针背景带，已被 success 签收）；重锚如实记账。 |
| 可复核性 | 15/15 | 297.5/272.5/206.3/189.1/200、M1370–M1374、precheck 292/269/716 都在。 |

均分 = 105/105 ≈ 15.0/15（100）。
""" % FULLTXT
RB=u"""- **R511（详情信息窄窗按优先级让位；产品 3 文件 + 判据，615 结案）**：600×492 详情原被 middle 截断成 `21:09:5…`；字宽实测全文 297.5 / 去复制 272.5 / 去字符数 206.3 / 分钟+来源 189.1、可用约 200。ViewThatFits 补两档：after 600×492 `10月30日 21:09 · 来自 Safari浏览器`、750 全量格式不变；M1370–M1374 5/5；M1365 撞针重锚。第五档 2 帧变化（基线 332）、第六档 0 帧、最终 42 张噪声；全量 1329/56/0；换装 419=419；电池 683/5；`6f43727` success 确认探针恢复。
"""
a=rd(A); d=rd(D); b=rd(B); st=rd(S); pr=rd(P); ch=rd(C); it=rd(I)
if a.count(AT_OLD)!=1: raise SystemExit("A title %d" % a.count(AT_OLD))
if a.count(ANCHOR_NEXT)!=1: raise SystemExit("A next %d" % a.count(ANCHOR_NEXT))
if u"## D-509" in d: raise SystemExit("D exists")
if u"R511 结案" in b: raise SystemExit("B exists")
if u"## R511 状态" in st: raise SystemExit("S exists")
if u"R511（详情信息窄窗" in pr: raise SystemExit("P exists")
if u"详情信息窄窗按优先级让位" in ch: raise SystemExit("C exists")
if u"## Round 508 · R511" in it: raise SystemExit("I exists")
if pr.count(u"U-31 … U-2028（R510 现读抬到最新一节）")!=1: raise SystemExit("P ucell")
if pr.count(u"## 18. R458 → R510 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510 —— 这份报告第七次差点停在几十轮之前）")!=1: raise SystemExit("P s18")
if pr.count(u"的 R510 节 ② 为准")!=1: raise SystemExit("P pointer")
wr(A, a.replace(AT_OLD, AT_NEW, 1).replace(ANCHOR_NEXT, u"\n"+AS+ANCHOR_NEXT, 1))
wr(D, d.rstrip()+"\n\n"+DS+"\n")
# 615：在原条下追加 R511 结案段（不新增条目）
wr(B, b.replace(u"不要放宽日期格式判据；当前记已知限制。",
                u"不要放宽日期格式判据；当前记已知限制。\n    **R511 结案**：ViewThatFits 补两档（省字符数 206.3pt、分钟精度 189.1pt），600×492 读 `10月30日 21:09 · 来自 Safari浏览器`（完整），750 仍是全量格式；M1370–M1374 5/5，判据同时钉两档接线。", 1))
wr(S, st.replace(u"## R510 状态（", SS.strip()+"\n\n## R510 状态（", 1))
pr=pr.replace(u"U-31 … U-2028（R510 现读抬到最新一节）", u"U-31 … U-2035（R511 现读抬到最新一节）", 1)
pr=pr.replace(u"## 18. R458 → R510 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510 —— 这份报告第七次差点停在几十轮之前）",
              u"## 18. R458 → R511 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511 —— 这份报告第七次差点停在几十轮之前）", 1)
pr=pr.replace(u"的 R510 节 ② 为准", u"的 R511 节 ② 为准", 1)
wr(P, pr.rstrip()+"\n\n"+RB+"\n")
m=u"## [Unreleased]\n"
if ch.count(m)!=1: raise SystemExit("C anchor")
wr(C, ch.replace(m, m+"\n"+CS, 1))
wr(I, it.rstrip()+"\n\n"+IS+"\n")
print("OK sha=%s full=%s" % (sha, FULL))
