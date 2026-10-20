#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R237 台账批写（事务性：全部锚点命中才落盘，任何一处不对就什么都不写）。"""
import io, os, re, subprocess, sys

REPO = "/Users/wangziyi/Codex_Project0"
NUM = "/tmp/r237_numbers.json"


def load(name):
    with io.open(os.path.join(REPO, name), encoding="utf-8") as f:
        return f.read()


def replace_once(text, old, new, tag):
    n = text.count(old)
    if n != 1:
        raise SystemExit("ANCHOR %s 命中 %d 次（要恰好 1 次）⇒ 什么都不写" % (tag, n))
    return text.replace(old, new, 1)


def sub_once(text, pattern, new, tag):
    hits = re.findall(pattern, text, re.S)
    if len(hits) != 1:
        raise SystemExit("PATTERN %s 命中 %d 处（要恰好 1 处）⇒ 什么都不写" % (tag, len(hits)))
    return re.sub(pattern, new, text, count=1, flags=re.S), hits[0]


import json
N = json.load(io.open(NUM, encoding="utf-8")) if os.path.exists(NUM) else {}


def need(k):
    if k not in N:
        raise SystemExit("数字 %s 没现读进 %s ⇒ 不许手抄，什么都不写" % (k, NUM))
    return N[k]


# ---------- ① AGENT_UI_AUDIT.md：降序插在「当前最大轮次标题」之上 ----------
ui = load("AGENT_UI_AUDIT.md")
m = re.search(u"^## 第 \\d+ 轮（R\\d+.*$", ui, re.M)
if not m:
    raise SystemExit("UI_AUDIT 找不到轮次标题 ⇒ 什么都不写")
first_line = m.group(0)
U_UI = u"""## 第 236 轮（R237 / Round 234 · 2026-10-20）：本机绿的边界 —— runner 的 STEP[4] 把「读缝的格子」判成编译期 error，本机不报，于是补一把**与 SDK 无关**的静态尺（U-761…U-764 / D-222）

- **U-761：`Build (must be warning-free)` 在 runner 上是 error，在本机连警告都没有。** run `39345462910`（= 台账半 `7713d18`，产品半 `415abf3` 同一次 push 只出这一跑）STEP[4] 正文只有一条不同的诊断，逐字：`ClipboardHistory/Tests/ClipboardHistoryAppTests/MenuBarSwiftUIDismissRowInkTests.swift:80:57: error: main actor-isolated static property 'dismissRowInk' can not be referenced from a nonisolated context`，配套 `note: add '@MainActor' to make instance method 'testSeamInkClearsTheTextFloorInBothStates()' part of global actor 'MainActor'`，收尾 `##[error]Process completed with exit code 1.`。同一支文件本机 `swift build --build-tests` 里这一条**不存在**（本轮重跑：`BUILD_WARN=0`、全量卷 %(full)s、判据卷 5 格 0 失败）。成因按「缺席解释逐一列全」判：① 我写错了？被 runner 自己的 note 否掉 —— 它说的是**推断出来的**隔离，不是我引用了不存在的东西；② 两套工具链对 conform `View` 的类型成员是否整体推断成 main-actor 不一致 ⇒ 与「本机 0 error」共存且唯一解释得通。修法取最小的一处：给那一格加 `@MainActor`（**产品 0 文件**，画面一字未动）。这条推断本机复现不出来：本机只有一套 SDK。
- **U-762：于是「编译器会替我记住」在本机等于没有 ⇒ 补静态尺。** `Tests/ClipboardHistoryAppTests/MenuBarSeamReaderIsolationTests.swift` 两格：①真值表（没标注 / 有标注 / 只在注释与字符串字面量里，三形状各判一次；夹具用假名 `Foo.Bar.`，免得①里出现真名被②算成一处引用）；②真扫测试目录，剥掉行注释与字面量后要求「代码位读缝的那根 func（或外层类型）紧邻标注里有 main-actor」。本轮现读的结论行：`SEAM_READER_ISOLATION 目录=ClipboardHistoryAppTests 文件=%(files)s 代码位引用=%(refs)s 未标注=%(bad)s`。名单为空=红（`refs >= 1`），结论行打在闸门之前。它是**尺不是编译器**：不解析语法树，只管这一颗名字，管不了别的 SwiftUI 成员。
- **U-763：这把尺有没有牙 —— M792 CAUGHT。** `.scratch/motion-audit-2/mutate_r237.py` 一刀：删掉 U-761 刚补的那行 `@MainActor`（删除型替换串不留原 token）。基线先绿（`R237_BASELINE 绿`、红名=无），变异后红在**该红的那一格**：`R237_KNIFE M792 CAUGHT EXTRA=ClipboardHistoryAppTests.MenuBarSeamReaderIsolationTests.testEveryLiveSeamReaderCarriesMainActor`，`R237_MUTATE 刀=1 CAUGHT=1 ESCAPED=0 NOT_RUN=0 RESTORE_CLEAN=yes`。这正是要的形状：本机编译器不报的写法，改完之后**判据自己红**，不用等下一跑 CI 编译失败。刀号先在台账查重：M792 未出现过（R236 用到 M791），跨表唯一。
- **U-764：未做 / 未证（不许写成已交付）。** ① 本笔修复的 **runner 侧验收未读** —— STEP[4] 会不会转绿，只有下一跑 CI 说了算；② STEP[15]/[17]/[18]/[19] 这四朵在 STEP[4] 修好之前**不许重新归因成产品事实**：编译不过 ⇒ 后面的步骤根本没有以「跑过产品判据」的身份运行，它们的红现在只说明同一个成因；③ 这把尺只覆盖「读 `MenuBarRecommendationsView` 那颗缝」，没推广到别处（推广要先量还有几处代码位在读别的 SwiftUI 静态成员 —— 未量）；④ 本机没有第二套 SDK，「工具链推断不同」这一句是**由两边的观测共存推出来的**，不是我在本机实测过两套；⑤ 249 / 263 与 251 / 250 / 253 的「接进 CI」那半仍欠，与上一轮同。

""" % N
idx = ui.index(first_line)
ui_new = ui[:idx] + U_UI + ui[idx:]

# ---------- ② AGENT_VISUAL_ITERATION.md：升序，只能追加到文件尾 ----------
it = load("AGENT_VISUAL_ITERATION.md")
lab = re.findall(u"^\\| (.*?[0-9]/15) \\|$", it, re.M)
rows = re.findall(u"^\\|[^\\n]*\\|\\s*\\d+\\s*/\\s*15[^\\n]*$", it, re.M)
if len(rows) < 7:
    raise SystemExit("ITERATION 里读不到自评表行（找到 %d 行）⇒ 表形状变了，什么都不写" % len(rows))
last7 = rows[-7:]
labels = [r.split(u"|")[1].strip() for r in last7]
scores = N["scores"]
if len(labels) != 7 or len(scores) != 7:
    raise SystemExit("自评表维度不是 7 行/评分不是 7 个 ⇒ 什么都不写")
tot = sum(scores)
tbl = u"\n".join(u"| %s | %d/15 |" % (labels[i], scores[i]) for i in range(7))
IT = u"""## Round %(rnd)d · 本机绿≠CI 绿：runner 把「读缝的格子」判成编译期 error，本机连警告都没有 ⇒ 补一把与 SDK 无关的静态尺（%(date)s / R237 / 第 236 轮 / U-761…U-764 / D-222 · 产品 0 文件）

本轮次对照：脚本臂 R237 = 第 236 轮 = Round %(rnd)d（这本账自己的编号仍比脚本臂慢 3，标题里逐字带上 R237 供 `test_round_batch_consistency` 的第二种形状命中）。

做了什么：读 R236 那一跑的 CI ⇒ STEP[4] `Build (must be warning-free)` 是 **error** 不是 warning，指在 R236 新写的判据格上（`@MainActor` 推断差异）。最小修法加一行标注（产品 0 文件），再补 `MenuBarSeamReaderIsolationTests`（真值表 + 真扫：`SEAM_READER_ISOLATION 文件=%(files)s 代码位引用=%(refs)s 未标注=%(bad)s`），配一刀 M792 问「这把尺有没有牙」⇒ CAUGHT、RESTORE_CLEAN=yes。

看图腿：本轮**没重捕帧**。前置量先读了 —— `git status --porcelain ClipboardHistory/Sources` = `PRODUCT_FILES=0`，上一轮的 %(frames)s 张帧仍在盘上（`ls /tmp/shots_r236/*.png`），于是按零产品改动的规矩复用它对账：`FRAME_BASELINE_COMPARED=%(cmp)s / CHANGED=%(chg)s / MISSING=%(mis)s / ADDED=%(add)s`。这是「画面没动」的对账，不是本轮有新画面。

七维度自评：

%(tbl)s

合计 %(tot)d/105。""" % dict(rnd=N["round_it"], date="2026-10-20", files=need("files"),
                          refs=need("refs"), bad=need("bad"), frames=N["frames"], cmp=N["cmp"],
                          chg=N["chg"], mis=N["mis"], add=N["add"], tbl=tbl, tot=tot)
it_new = it.rstrip(u"\n") + u"\n\n" + IT + u"\n"

# ---------- ③ AGENT_DECISIONS.md：追加 D-222 ----------
de = load("AGENT_DECISIONS.md")
DE = u"""**D-222（R237）：编译器只在某些机器上会说的话，不能当作「有人替我记住了」——要在本机造一把与它无关的尺。**

形状（三步，缺一步就只是把运气写成流程）：

1. **把风险换成静态可判的形状。** 「非隔离上下文读这颗值」在本机不报、在 runner 报 error ⇒ 不能靠编译器。于是判据不问「编译器怎么说」，问「引用行往上第一根 func 的紧邻标注里有没有 main-actor」，并且先把行注释与字符串字面量剥掉（同一颗名字在文档注释和路径字面量里都出现过，R236 实测过被自己的引用喂饱）。
2. **判据自印读数，结论行打在闸门之前**：`SEAM_READER_ISOLATION 文件=… 代码位引用=… 未标注=…`。没有这一行，绿就只等于「我没判」。
3. **一刀删掉保护标注必须让判据自己红**（M792 CAUGHT）。尺只在真产物上绿过一次是不够的，它要能被一根针戳红。

附则：① 名单为空=红（`代码位引用 >= 1`）—— 缝被搬走与尺被弄坏是两种相反的事，都不许由「0 处引用」绿着代替；② 「本机绿」这句话以后要写成**「本机这一套 SDK 绿」**，工具链差异不是环境问题，是「我的记账里没有这台机器」的覆盖率问题；③ STEP[4] 编译不过时，后面那些红**只是同一个成因的回声**，不许逐朵重新归因成产品事实。"""
de_new = de.rstrip(u"\n") + u"\n\n" + DE + u"\n"

# ---------- ④ AGENT_BACKLOG.md：新开并结案（本机半）+ 记 runner 半 ----------
bk = load("AGENT_BACKLOG.md")
BK = u"""**268（R237 新开 → 本机半结案）：读 SwiftUI 树静态成员的测试格子必须带 `@MainActor` —— 本机 SDK 不报，runner 报编译期 error。**

来源：run `39345462910` STEP[4] 的正文（原文见 U-761），主语是 R236 自己新写的那一格。
本机半已结案：加那一行标注（产品 0 文件）+ 上线 `MenuBarSeamReaderIsolationTests`（真值表三形状 + 真扫，`SEAM_READER_ISOLATION 文件=%(files)s 代码位引用=%(refs)s 未标注=%(bad)s`）+ 一刀 M792 **CAUGHT**（删标注 ⇒ 尺自己红，`RESTORE_CLEAN=yes`）。
**没结案的一半**：这一笔修复的 runner 侧验收未读 —— 下一轮 ⓪ 要现拿 run↔commit 成对，验 STEP[4] 是否转绿、`SEAM_READER_ISOLATION` 在 runner 上打出的读数、以及 STEP[15]/[17]/[18]/[19] 是否随编译恢复而重新开始判（在那之前它们的红只算同一成因的回声）。
推广也**没做**：尺只管这一颗名字；要推广先量「还有几处代码位在读别的 SwiftUI 静态成员」——没量过就不登记。""" % N
bk_new = bk.rstrip(u"\n") + u"\n\n" + BK + u"\n"

# ---------- ⑤ CHANGELOG.md：插在 [Unreleased] 之下（本轮必须有标题行） ----------
cl = load("CHANGELOG.md")
CL_HEAD = u"""### 判据与尺：读缝的格子必须标 `@MainActor` —— runner 的 STEP[4] 判编译期 error、本机不报，补一把与 SDK 无关的静态尺（R237 / U-761…U-764 / D-222 · 产品 0 文件，画面一字未动）

- `MenuBarSwiftUIDismissRowInkTests.testSeamInkClearsTheTextFloorInBothStates` 加一行 `@MainActor`（run `39345462910` STEP[4] 的 error 原文：`main actor-isolated static property 'dismissRowInk' can not be referenced from a nonisolated context`）。
- 新增 `MenuBarSeamReaderIsolationTests`：①真值表三形状（没标注 / 有标注 / 只在注释与字面量里）②真扫测试目录（剥注释与字面量，要求代码位引用所在 func 紧邻标注里有 main-actor；名单为空=红）；自印 `SEAM_READER_ISOLATION 文件=%(files)s 代码位引用=%(refs)s 未标注=%(bad)s`。
- 变异刀 M792（删掉那行标注）**CAUGHT** 在 `testEveryLiveSeamReaderCarriesMainActor`，`刀=1 CAUGHT=1 ESCAPED=0 NOT_RUN=0 RESTORE_CLEAN=yes`；未做的：runner 侧验收、推广到别的 SwiftUI 成员（见 U-764 / 268）。

""" % N
anchor = u"## [Unreleased]"
cl_new = replace_once(cl, anchor + u"\n", anchor + u"\n\n" + CL_HEAD.rstrip(u"\n") + u"\n", "CHANGELOG-UNRELEASED")

# ---------- ⑥ AGENT_STATE.md：本轮块插在最上面（current_round 读第一处匹配） ----------
st = load("AGENT_STATE.md")
m2 = re.search(u"^# [^\\n]*$", st, re.M)
if not m2:
    raise SystemExit("STATE 找不到一级标题 ⇒ 什么都不写")
ST = u"""

## R237（本地 · 2026-10-20 08:2x）：本机绿≠CI 绿 —— runner 的 STEP[4] 是编译期 error，补了一把与 SDK 无关的静态尺（第 236 轮 / Round 234 / U-761…U-764 / D-222 / BACKLOG 268）

最后更新：2026-10-20 08:25（本地 · R237 / 第 236 轮 / Round 234）

本轮落地：① 读 R236 那一跑 CI ⇒ `STEP[4] Build (must be warning-free)` 打的是 **error**（`dismissRowInk` 非隔离引用），STEP[5]–[14] 因此 skipped、STEP[15]/[17]/[18]/[19] 的红是同一成因的回声；② 最小修法加一行 `@MainActor`（**产品 0 文件**）；③ 新判据 `MenuBarSeamReaderIsolationTests`（真值表 + 真扫，现读 `SEAM_READER_ISOLATION 文件=%(files)s 代码位引用=%(refs)s 未标注=%(bad)s`）；④ 变异刀 M792 CAUGHT、`RESTORE_CLEAN=yes`；⑤ 看图腿复用上一轮 %(frames)s 张帧：`COMPARED=%(cmp)s CHANGED=%(chg)s MISSING=%(mis)s ADDED=%(add)s`（先量 `PRODUCT_FILES=0` 才复用）。

验证：`BUILD_WARN=0`；判据卷 `MenuBarSeamReaderIsolationTests|MenuBarSwiftUIDismissRowInkTests` 5 格 0 失败；全量卷 %(full)s；帧基线如上；脚本电池在台账落盘之后跑，读数写在本笔 commit message 里（顺序规矩）。

**下一轮（R238 / 第 237 轮 / Round 235）的靶**

⓪ **本笔的 CI 完全未读**（268 的 runner 半、也是 R236 那三笔一直没读完的那一半）⇒ `python3 scripts/ci_read.py latest` 现拿 run↔commit 成对，再看 `steps <run>`：**要验的是 STEP[4] 有没有转绿**（这一条不绿，后面所有步骤的处置都不许当成产品读数）、`SEAM_READER_ISOLATION` 在 runner 上打的那一行、新判据两格有没有露面、以及 249 / 263 那两格。
① 249 与 263 的分辨读数（`pixels > 400` 那个证人；判据要自印读数，`--log-failed` 会截断断言正文）。
② 268 的 runner 半（见 ⓪）。
③ 251 / 250 / 253 的「接进 CI」那半。
④ 267（10ms 绝对地板 vs 存在性断言）、260、262、258 第三处、254→255→248、243、227③、222、215、201 / 202、207、240。
⑤ 要用户真机或授权的：220 路 A（改全局键盘偏好）、228②、265（悬停那一行的真机观感）。
""" % N
st_new = st[:m2.end()] + ST + st[m2.end():]

# ---------- ⑦ AGENT_FINAL_REPORT.md：只改计数器 ----------
fr = load("AGENT_FINAL_REPORT.md")
fr, old_cell = sub_once(fr, u"U-31 … U-\\d+", u"U-31 … U-764", "REPORT-U-CELL")
fr = replace_once(fr, u"（R236：U-757…U-760 之后现读刷新", u"（R237：U-761…U-764 之后现读刷新", "REPORT-U-ROUND")

for tag, txt in [("AGENT_UI_AUDIT.md", ui_new), ("AGENT_VISUAL_ITERATION.md", it_new),
                 ("AGENT_DECISIONS.md", de_new), ("AGENT_BACKLOG.md", bk_new),
                 ("CHANGELOG.md", cl_new), ("AGENT_STATE.md", st_new),
                 ("AGENT_FINAL_REPORT.md", fr)]:
    assert txt != load(tag), "NO-OP %s ⇒ 什么都不写" % tag

with io.open(os.path.join(REPO, ".scratch/motion-audit-2/r237_labels.json"), "w", encoding="utf-8") as f:
    json.dump({"labels": labels, "prev_rows": last7}, f, ensure_ascii=False, indent=1)

written = []
for tag, txt in [(u"AGENT_UI_AUDIT.md", ui_new), (u"AGENT_VISUAL_ITERATION.md", it_new),
                 (u"AGENT_DECISIONS.md", de_new), (u"AGENT_BACKLOG.md", bk_new),
                 (u"CHANGELOG.md", cl_new), (u"AGENT_STATE.md", st_new),
                 (u"AGENT_FINAL_REPORT.md", fr)]:
    with io.open(os.path.join(REPO, tag), "w", encoding="utf-8") as f:
        f.write(txt)
    written.append(tag)
print(u"LEDGERS_R237 写了 %d 本：%s" % (len(written), u", ".join(written)))
print(u"自评行标签： %s / 分数 %s = %d/105" % (u" | ".join(labels), scores, tot))
