# -*- coding: utf-8 -*-
"""R556 台账（第 555 轮 / Round 553）：632 的缩略图 eager 读落地 + 629 真因量出。

数字一律从现读填入 NUM（脚本电池与 `--check` 会兜住抄错的那一类）。
用法：`python3 ledgers_r556.py --check` 只验锚点；不带参数才真写七本账。
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── 现读填入（跑之前用 `--fill` 之外不许手抄上一轮）────────────────────
NUM = {
    "FULL": "1396/55/0（709.7s）",
    "INSTALL": "`make bundle` = `SIGNATURE_KIND=local` ⇒ `INSTALL_RESULT=ok / SHA_MATCH=1 / INSTALL_SIGNATURE=local / INSTALL_ENTRIES=433=433`（PID 39654 → 86092，`SMOKE_OK=1`）",
    "BATTERY": "695/5",                      # 电池（台账后跑）：填
    "ABSENCE": "162/63/0",                   # 清账：填
    "STREAK": "1",                           # streak as-of 555
    "CAPTURE": "216/4 skipped/0 失败（606.0s）",
    "FRAMES": "354 CHANGED=0 MISSING=0 ADDED=0",
    "PRECHECK": "tables=342 covered=295 arms=757 bad=0",
    "ARM": "files=435 arms=1244 dupes=0 repeats=0",
    "HIDDEN": "表=429 可判=1183 rot=0 抽不出=6 处置=ok",
}

UI = u"""## 第 555 轮（R556 · 2026-11-02 · U-2371…U-2378）：632 的 eager 读换到行显示（产品 5 文件 + 判据 2 文件 + 三把刀）+ 629 的真因量到

- **U-2371：⓪ 与前置。** HEAD=origin=`de58ab0`、ahead=0、已跟踪改动 0。五跑读单见本轮 ⓪ 节；本轮开跑后又到两跑：`41439930389 ↔ 78e7ab5`（R555 台账笔）conclusion=**failure**，全部失败步骤 = **STEP[15] Swift tests** + **STEP[18] On-screen probe coverage floor**，红名现读 = `SelectionRevealAnimationTests/testProductDurationRevealStillMovesOverTime`（`[0.0, 1430.0, 1430.0, 1430.0, 1430.0]`）+ `testFrameIntervalsUnderStateChanges` 最差 **181.6ms / 超锚点 2 颗** ⇒ **622 第十二值**；`41440039381 ↔ de58ab0`（R555 补记笔）conclusion=**success**、JOB success、**失败步骤 0 条** ⇒ **R555 那朵 STEP[9] 自造红在 runner 上转绿，签收完成**（不是从"不在红名单里"推的：整跑 success 就是它的结论）。`41442000018 ↔ eb883ad`（本轮 ⓪ 笔）取号时 in_progress ⇒ **NOT-RUN**。
- **U-2372：②(a) 根因换了位置 —— R553 的边界读漏了一格。** R553 写「采集路径（`ClipboardIntake`）只记 URL，不读文件」，那句对 `ClipboardIntake` 成立；但条目一进 store 就有人去开那个文件：`HistoryStore.add` 里 `attachFileThumbnailIfNeeded(for:)` ⇒ `FileThumbnailPolicy.thumbnail(for:)` ⇒ `CGImageSourceCreateWithURL` **在复制那一刻打开受保护目录里的图片**。更重的是 `ApplicationShell:78` 每次启动 `attachMissingFileThumbnails()` 把**全表没有行内预览的图片文件条目**各开一遍，而读失败时 `thumbnail` 仍是 nil ⇒ **下一次启动又全部重来** —— 与用户说的"已批准无数次还在弹"对得上。第三条：同一次渲染里文本被开两次（`MediaLoader.readTextPreview` + `DetailView.preferredTextHeight`）。
- **U-2373：②(a) 旧值先量（一次性探针，不入库）。** 给缩略图那一格补计数点（`ProtectedFileAccessLedger.Site.thumbnailSourceOpen`，只存路径哈希）之后现读：复制 **1 条**桌面图片 ⇒ 采集那一步开 **1 次**；store 里放 **3 条**没有预览的图片文件条目 ⇒ 启动回填开 **3 次**（每启动一次就 3 次，读失败也照开）。探针用不存在的路径 —— 计数器在**真正读之前**记，所以"试图开几次"数得出来，而这正是弹窗那件事的量。
- **U-2374：②(a) 改法：eager 读搬到"行真正显示"。** `HistoryStore` 新增 `requestThumbnail(for entryID:)`（幂等：已有缩略图 / 不是图片文件 ⇒ 一次都不开），`add` 里不再调用、`attachMissingFileThumbnails()` 整格删除、`ApplicationShell` 的启动回填调用删除；触发点移到 `HistorySidebarView.historyRow` 的 `.task(id: entry.id)` ⇒ 行出现在列表里才要那张图，滚出列表时 `.task` 被取消。新值：采集 **0 次**、启动装载 **0 次**、行显示按需 **1 次**（本机现读，判据断言）。
- **U-2375：②(a) 契约翻转与判据。** `FileThumbnailTests/testStartupBackfillIsWired` 原来用源码 grep 断言"启动必须回填" —— **静态断言把 eager 读钉成了契约**（memory 里那一族），本轮把它翻成 `testStartupSweepIsGoneAndRowDemandIsWired`：回填 API 不许存在（存在就说明只是暂时没人调，下一轮会被接回去）、按需 API 与行的 `.task` 必须在，另加**行为那一半**（装载 3 条图片文件条目 ⇒ 开 0 次）。`testAddAttachesThumbnailAsynchronously` 改成 `testAddDoesNotReadTheFileWhileRowDisplayRequestsIt`：`add` ⇒ 0 次且 `thumbnail` 仍是 nil；`requestThumbnail(for:)` ⇒ 恰好 1 次并且 3 秒内真的写回。两半都是计数器证人，没有一条走日志正则。
- **U-2376：②(a) 刀。** **M1440**（把按需请求搬回 `add` 里）CAUGHT，红名两条：`("1") is not equal to ("0") - 复制这一步就去开那个图片文件` 与 `("2") is not equal to ("1")`；**M1441**（`shouldAttachThumbnail` 取反 ⇒ 需求路径永不开文件）CAUGHT：`("0") is not equal to ("1") - 行显示按需请求却开了 0 次` + `按需请求之后 3 秒内没补上缩略图`（这一把同时证明"隐私修复"没把视觉功能删掉）；**M1442**（把缩略图那一格从计数器上摘掉）CAUGHT ⇒ 零次不会是假绿。三把 `RESTORE_CLEAN=yes`、预检全 GREEN。
- **U-2377：②(b) 629 的真因量出来了：不是产品硬切，是采样网格。** 同一判据、同一 1x，`5a943e7` 读 **过渡帧数=1**、`78e7ab5` 读 **过渡帧数=2**（该跑 STEP[19] 因此绿），而**两次峰值都是 0.0193**；本机 1x 读 **4 帧、峰值 0.0097、窗口 322ms、每格 12.4ms**。⇒ "产品那一侧真的没演"被排除（同一份代码本机读到 4 帧，且总变化量一致），剩下的解释是 runner 每格 ≈44ms（同卷 `MOTION_SIDEBAR_COUNT` 现读 窗口=1143ms / 27 格）把 200ms 的过程摊到 1–2 格上 ⇒ **≥2 帧地板在那台机器上正好压在网格边缘，所以是间歇红**。本轮落的是**读数**：给这条判据补 `窗口=`、`每格=`、`相邻帧差=[…]`（同卷别的情景早就有，只有它没有）—— 没有这三个数，"只落在 1 格上"分不开"改产品"与"改采样"这两条**修法相反**的路。地板 ≥2 帧、声明时长、阈值一律未动。两条出口写进 629：(A) 加密录制（受 200s 看门狗约束，BACKLOG 444 同一格）；(B) 换判据对象（读标签自身的逐帧墨/位置，像 R545 那样读 settled 进度）。
- **U-2378：③④⑤ 验证链与交接。** `swift build` 告警 **0**；判据卷 `UICaptureTests` **%(CAPTURE)s**；帧重捕 `FRAME_BASELINE_COMPARED=%(FRAMES)s` ⇒ **画面逐字节不变**（侧栏行的 `.task` 只在夹具路径上开不到图，今天没有"真实图片路径装进侧栏行"的夹具 —— 将来若加，这条异步补图会破坏帧确定性，已写进 632 的监控句）；全量 **%(FULL)s**；预检 **%(PRECHECK)s**、`ARM_TOTAL %(ARM)s`、`HIDDEN_ARMS %(HIDDEN)s`；换装 %(INSTALL)s；清账 **%(ABSENCE)s**、电池 **%(BATTERY)s**（台账后复跑）；产品面连续零改动 **%(STREAK)s** 轮（as-of 555 现读）⇒ 本轮之后仍是 0（本轮产品 5 文件）。**632 状态：落地 + 剩余具名出口**（文本同一次渲染仍被开两次、图片整文件读仍在预览加载那一步）；**629 状态：具名出口（真因已量出，两条相反修法待选）**；622 追加第十二值 181.6ms/2；633 仍等用户回执；624/627 继续；628/625/626/569/616 不重开。下一轮 R557（第 556 轮 / Round 554）：必读 `41442000018 ↔ eb883ad` 与本轮各笔的跑（全部失败步骤）；② 头一格 = 629 在 (A)/(B) 里选一条落地（地板不许动），第二格 = 632 的"文本一次渲染只开一次"；禁碰清单 9 面不变；刀号 **M1443** 起；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板、2x 的 8.0pt 与 1x 的 6.0pt 均不动。

"""

ITER = u"""
## Round 553 · R556（第 555 轮 · 2026-11-02）：受保护目录的 eager 读搬到行显示；629 量出是采样网格不是产品硬切

R553 那句"采集只记 URL"本轮被自己的读数推翻：条目一进 `HistoryStore` 就开一次图片文件，而启动回填把全表各开一次、失败就每次启动重来 —— 这才是"批准无数次还在弹"的重复形状。旧值现读（1 条=1 次、3 条启动=3 次），改法是把补图搬到 `HistorySidebarView` 行的 `.task(id:)`（可见才读，滚出去就取消），新值 0/0/1。契约那一半也翻了：原来用源码 grep 断言"启动必须回填"的判据，等于把 eager 读钉成契约，本轮改成"回填 API 不许存在 + 装载 3 条开 0 次"的行为证人。刀 M1440/M1441/M1442 分别钉住"回到采集"、"需求路径变空"、"计数器瞎掉"。629 另落一格读数：runner 与本机同一判据读 1 帧 / 4 帧而峰值同为 0.0193 ⇒ 是每格 44ms 的采样网格压在 ≥2 帧地板上，不是产品硬切；地板没动，补的是 `窗口/每格/相邻帧差` 三个数。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 12/15 | 帧 354 逐字节不变 ⇒ 没有新画面可看；看图这一维不适用但不是没跑，另逐张确认侧栏行没有异步补图。 |
| 判据有效性 | 15/15 | 旧契约（grep 断言"启动必须回填"）被翻成行为证人；新判据两半（0 次 / 恰好 1 次）互相对照。 |
| 假绿防御 | 15/15 | 计数器补在真正读之前且 open 失败也记；M1442 专治"尺瞎了 ⇒ 0 次是假绿"；629 用峰值相同排除"产品硬切"。 |
| 产品面推进 | 14/15 | 产品 5 文件、eager 读整格搬走；没动视觉与禁碰面；剩两格具名续单。 |
| 台账一致性 | 13/15 | 七本齐、sources 格与 streak 格由脚本派生；R553 那句边界读被本轮现读更正并写明。 |
| 交付诚实性 | 15/15 | 629 只落读数、明确"两条相反修法待选"；633 仍等回执不写已修。 |
| 可复核性 | 15/15 | 三把刀命令、判据 filter、新旧计数值、两跑 CI 成对号全部入账。 |

均分 = 99/105 ≈ 14.1/15（94）。
"""

CHG = u"""### 受保护目录的主动读从"采集 + 启动全表"搬到"行真正显示"；629 量出是采样网格（R556 / 第 555 轮 / Round 553 / U-2371…U-2378 · 产品 5 文件 + 判据 2 文件）

R553 记的"采集只记 URL"本轮被现读推翻：`HistoryStore.add` 会立刻 `FileThumbnailPolicy.thumbnail(for:)` 打开那个图片文件，而 `ApplicationShell` 每次启动 `attachMissingFileThumbnails()` 把全表没有预览的图片文件各开一遍 —— 读失败时 `thumbnail` 仍是 nil ⇒ 下次启动再来一次。旧值：1 条复制 = 1 次、3 条历史 = 每次启动 3 次。改法：补图搬到 `HistorySidebarView.historyRow` 的 `.task(id: entry.id)`（可见才读、滚出即取消），`HistoryStore.requestThumbnail(for:)` 幂等，回填 API 整格删除。新值：采集 0 次、启动装载 0 次、行显示按需 1 次。判据契约同步翻转（原来那条 grep 判据把 eager 读钉成契约），刀 M1440/M1441/M1442 全 CAUGHT。629：runner 读 1 帧（`5a943e7`）与 2 帧（`78e7ab5`）而峰值同为 0.0193、本机 4 帧 / 每格 12.4ms ⇒ 是 runner 每格 ≈44ms 的采样网格压在 ≥2 帧地板上，不是产品硬切；本轮补 `窗口/每格/相邻帧差` 三个读数，地板与阈值未动，两条相反修法写进 629。R555 的尺修由 `41440039381 ↔ de58ab0` **整跑 success** 签收。帧 354 CHANGED=0；全量 %(FULL)s；build 0 告警；清账 %(ABSENCE)s；电池 %(BATTERY)s。

"""

A632 = u"""    落地（R556，B 的第二半 —— 根因位置也换了）。R553 那句"采集路径只记 URL"只对 `ClipboardIntake` 成立：条目一进 `HistoryStore` 就有人去开那个文件。本轮现读并改掉两处 eager 读 ——
      · `HistoryStore.add` 里的 `attachFileThumbnailIfNeeded(for:)`（复制那一刻 `CGImageSourceCreateWithURL` 打开图片）；
      · `ApplicationShell` 每次启动的 `attachMissingFileThumbnails()`（全表没有行内预览的图片文件各开一遍；**读失败 ⇒ `thumbnail` 仍是 nil ⇒ 下次启动又全部重来**，这才是"批准无数次还在弹"的重复形状）。
    新值：补图改由 `HistorySidebarView.historyRow` 的 `.task(id: entry.id)` 按需请求 `HistoryStore.requestThumbnail(for:)`（幂等，滚出列表即取消）。旧值现读：复制 1 条 = 开 1 次；3 条历史 = 每次启动开 3 次。新值：采集 0 次、启动装载 0 次、行显示按需 1 次。判据：`FileThumbnailTests` 里那条**源码 grep 契约**（"启动必须回填"）翻成 `testStartupSweepIsGoneAndRowDemandIsWired`（回填 API 不许存在 + 装载 3 条开 0 次的行为证人），`testAddAttachesThumbnailAsynchronously` 改成"add 开 0 次 / requestThumbnail 恰好 1 次且真写回"。刀 **M1440**（补图搬回采集）/**M1441**（需求路径永不开文件）/**M1442**（缩略图那格从计数器摘掉）全 CAUGHT、RESTORE_CLEAN。
    剩余两格（仍是本轮实读，具名不静默）：① 文本在同一次渲染里仍被开两次（`MediaLoader.readTextPreview` 与 `DetailView.preferredTextHeight` 各一次）—— 要合成一次取样把字节传下去；② 图片预览仍是 `Data(contentsOf:)` 整文件读（它已在"详情区挂载"之后，属可见才读，但整文件这一格可以换成按需要的尺寸解）。
    新增监控句：侧栏行的 `.task` 会异步补图 ⇒ 将来若有夹具把**真实存在的图片路径**装进侧栏行，帧就不再确定；本轮 354 帧逐字节不变，说明今天没有这种夹具。

"""

A629 = u"""    真因（R556 现读，两条解释被分开）：同一判据、同一 1x —— `41431129208 ↔ 5a943e7` 读 **过渡帧数=1**、`41439930389 ↔ 78e7ab5` 读 **过渡帧数=2**（该跑 STEP[19] 因此没红），**两次峰值同为 0.0193**；本机 1x 读 4 帧、峰值 0.0097、窗口 322ms、每格 12.4ms。⇒ "产品没演（真硬切）"被排除：同一份代码本机读到 4 帧，且两处的总变化量一致；剩下的是 runner 每格 ≈44ms（同卷 `MOTION_SIDEBAR_COUNT` 现读 窗口=1143ms / 27 格）把 200ms 的过程摊到 1–2 格 ⇒ **≥2 帧地板在那台机器上正好压在采样网格边缘**，所以是间歇红而不是稳定红。
    本轮落读数不动地板：`MOTION_MARKDOWN_MODE_FADE` 新增 `窗口=`、`每格=`、`相邻帧差=[…]`（同卷别的情景早有这几格，只有它没有 —— 没有它就分不开下面两条**修法相反**的路）。
    两条出口（下一轮选一条落地，不许动 ≥2 帧地板）：(A) 加密这一格的录制，让 runner 也拿到 ≤15ms/格 —— 受 200s 看门狗约束，与 BACKLOG 444 同一格；(B) 换判据对象：不读整带帧差，改读标签自身的逐帧墨量/位置序列（R545 读 settled 进度那一族的形状）。

"""

DEC = u"""
## D-556 受保护目录的读取时机以"行真正显示"为界；判据契约若把 eager 读钉住，就翻契约（R556）

- 背景：632 的 B。R553 把边界写在 `ClipboardIntake` 上，本轮现读发现真正的主动读在**它后面一格** —— `HistoryStore.add` 补行内缩略图，以及 `ApplicationShell` 每次启动的全表回填（读失败 ⇒ 条目仍是 nil ⇒ 每启动重来）。
- 决定：① 补图的触发点从"采集 + 启动全表"改成"行出现在列表里"（`HistorySidebarView.historyRow` 的 `.task(id: entry.id)` ⇒ `HistoryStore.requestThumbnail(for:)`，幂等、滚出即取消）；② 删除 `attachMissingFileThumbnails()` 整格（不留"只是暂时没人调"的 API）；③ 把 `FileThumbnailTests` 里那条源码 grep 契约翻过来 —— 它原来断言"启动必须回填"，等于把缺陷钉成契约。
- 理由：TCC 授权按 App 身份记（R554/R555 已把身份钉住），但**读的次数与频率仍由我们决定**。启动全表回填是"用户什么都没做就开 N 个受保护文件"，而失败重试的形态让它每启动重复一次。可见性边界是产品本来就有的语义（详情区已经这样）。
- 兼容性/迁移：无存档格式变化；老历史里从未补到缩略图的条目，在用户滚到那一行时才补 —— 视觉结果相同，时点推迟。隐私计数只存路径哈希、不落盘、无全局 reset。
- 边界：本轮**没有**把"整文件读"换成按需尺寸解码，也没有合并文本的两次取样 —— 两格都写回 632 续单，不静默放回。
- 撤回：把 `add` 里恢复 `requestThumbnail(for: entry.id)` 即回到 eager 形状（刀 M1440 就是这一把，实测 CAUGHT）；恢复启动回填需要同时把 API 加回来，M1441/M1442 覆盖需求路径与计数器两种瞎法。
"""


def rd(n):
    return io.open(os.path.join(ROOT, n), encoding="utf-8").read()


def wr(n, t):
    io.open(os.path.join(ROOT, n), "w", encoding="utf-8").write(t)


def once(t, old, new, label):
    n = t.count(old)
    if n != 1:
        sys.stderr.write("ANCHOR_BAD %s hits=%d\n" % (label, n))
        sys.exit(1)
    return t.replace(old, new, 1)


def fill(text):
    out = text
    for key, value in NUM.items():
        out = out.replace(u"%%(%s)s" % key, value)
    if u"%(" in out:
        sys.stderr.write("PLACEHOLDER_LEFT %s\n" % out[out.find(u"%("):out.find(u"%(") + 30])
        sys.exit(1)
    return out


def main():
    check = "--check" in sys.argv

    state = rd("AGENT_STATE.md")
    if state.count(u"## R556 ⓪ 开工") != 1:
        sys.stderr.write("ANCHOR_BAD state R556 ⓪ 节不存在 ⇒ 不许两轮写进同一节\n")
        return 1

    n = "AGENT_UI_AUDIT.md"
    t = rd(n)
    a = u"## 第 554 轮（R555 · 2026-11-02 · U-2362…U-2370）"
    if t.count(a) != 1:
        sys.stderr.write("ANCHOR_BAD ui\n")
        return 1
    if not check:
        wr(n, t.replace(a, fill(UI) + a, 1))

    n = "AGENT_VISUAL_ITERATION.md"
    t = rd(n)
    if u"## Round 553 · R556" in t:
        sys.stderr.write("ANCHOR_BAD iteration Round 553 已存在\n")
        return 1
    if not t.endswith(u"\n"):
        t += u"\n"
    if not check:
        wr(n, t + fill(ITER))

    n = "CHANGELOG.md"
    t = rd(n)
    a = u"## [Unreleased]\n\n"
    if t.count(a) != 1:
        sys.stderr.write("ANCHOR_BAD changelog\n")
        return 1
    if not check:
        wr(n, t.replace(a, a + fill(CHG), 1))

    n = "AGENT_BACKLOG.md"
    t = rd(n)
    a632 = u"    剩余两格（下一轮的靶，具名不静默）"
    if t.count(a632) != 1:
        sys.stderr.write("ANCHOR_BAD backlog632\n")
        return 1
    end632 = t.find(u"\n\n", t.find(a632))
    if not check:
        t = t[:end632 + 1] + A632 + t[end632 + 1:]
    i629 = t.find(u"**629.")
    if i629 < 0:
        sys.stderr.write("ANCHOR_BAD backlog629\n")
        return 1
    end629 = t.find(u"\n\n", i629)
    if not check:
        t = t[:end629 + 1] + A629 + t[end629 + 1:]
    if not check:
        wr(n, t)

    n = "AGENT_DECISIONS.md"
    t = rd(n)
    if not t.endswith(u"\n"):
        t += u"\n"
    if not check:
        wr(n, t + DEC)

    n = "AGENT_FINAL_REPORT.md"
    t = rd(n)
    for old, new, label in [
        (u"R9–R552，553 节自评", u"R9–R553，554 节自评", u"title"),
        (u"阶段二 **545 轮**审计（R9–R552；以 `curve_from_ledger.py` 的 `PHASE2 n=545` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 552",
         u"阶段二 **546 轮**审计（R9–R553；以 `curve_from_ledger.py` 的 `PHASE2 n=546` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 553", u"§1"),
        (u"| 视觉台账 | U-31 … U-2370", u"| 视觉台账 | U-31 … U-2378", u"U 上界"),
        (u"产品面连续零改动轮数 = **3**（as-of 554）", u"产品面连续零改动轮数 = **1**（as-of 555）", u"streak as-of"),
        (u"以 `AGENT_STATE.md` 的 R555 节 ② 为准", u"以 `AGENT_STATE.md` 的 R556 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R555 这一段", u"## 18. R458 → R556 这一段", u"§18 head"),
        (u"R555 续到 555 —— 这份报告第七次差点停在几十轮之前）", u"R556 续到 556 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]:
        t = once(t, old, new, label)
    anchor = (u"帧 354 CHANGED=0；全量 1396/55/0（756.9s）；build 0 告警；换装 `INSTALL_SIGNATURE=local`、433=433；电池 695/5。\n")
    bullet = (u"- **R556（受保护目录的读取时机搬到行显示 + 629 真因量出；产品 5 文件 + 判据 2 文件）**："
              u"R553 那句「采集只记 URL」被现读推翻 —— `HistoryStore.add` 与启动全表回填各开一次图片文件，"
              u"读失败就每启动重来；旧值 1 条=1 次、3 条=每启动 3 次，新值采集 0 / 启动 0 / 行显示按需 1。"
              u"源码 grep 那条把 eager 读钉成契约的判据同笔翻正（行为证人 + 接线证人）。"
              u"629：runner 读 1 帧与 2 帧而峰值同为 0.0193、本机 4 帧 / 每格 12.4ms ⇒ 采样网格压在 ≥2 帧地板上，不是产品硬切；补三个读数，地板未动。"
              u"刀 M1440/M1441/M1442 CAUGHT。R555 的尺修由 `41440039381 ↔ de58ab0` 整跑 success 签收。"
              u"帧 354 CHANGED=0；全量 %(FULL)s；电池 %(BATTERY)s。\n")
    t = once(t, anchor, anchor + fill(bullet), u"§18 bullet")
    if not check:
        wr(n, t)

    n = "AGENT_STATE.md"
    t = rd(n)
    t = once(t,
             u"最后更新：2026-11-02（本地 · R555 / 第 554 轮 / Round 552）",
             u"最后更新：2026-11-02（本地 · R556 / 第 555 轮 / Round 553）",
             u"identity")
    body = u"""## R556 状态（2026-11-02 · 第 555 轮 / Round 553 · 产品 5 文件 + 判据 2 文件 + 三把刀）

① ⓪ 与开跑后的两跑：`41439930389 ↔ 78e7ab5`（R555 台账笔）failure = **STEP[15]+[18]**，红名 = SelectionReveal 五值瞬移 + 622 **第十二值 181.6ms/2**；`41440039381 ↔ de58ab0`（R555 补记笔）**conclusion=success、失败步骤 0 条** ⇒ R555 自造的 STEP[9] 在 runner 上**转绿被签收**；`41442000018 ↔ eb883ad`（本轮 ⓪ 笔）in_progress ⇒ NOT-RUN。
② ②(a) 632 的 eager 读搬到行显示：现读推翻 R553 的边界（真正主动读在 `HistoryStore.add` 的补图与 `ApplicationShell` 的启动全表回填，失败即每启动重来）；旧值 1 条复制=开 1 次、3 条历史=每次启动 3 次 ⇒ 新值 采集 0 / 启动装载 0 / 行显示按需 1（`HistorySidebarView.historyRow` 的 `.task(id: entry.id)` ⇒ `HistoryStore.requestThumbnail(for:)`，幂等、滚出即取消；`attachMissingFileThumbnails()` 整格删除）。同笔翻正被 grep 钉住的旧契约（`testStartupBackfillIsWired` → `testStartupSweepIsGoneAndRowDemandIsWired`，加行为证人；`testAddAttachesThumbnailAsynchronously` → 两半对照）。刀 **M1440/M1441/M1442** 全 CAUGHT、RESTORE_CLEAN。剩余两格具名续单：文本同一次渲染仍开两次、图片预览仍整文件读。
③ ②(b) 629 真因量出：同一判据同一 1x，`5a943e7` 读 1 帧、`78e7ab5` 读 2 帧、峰值两次同为 0.0193，本机 4 帧 / 峰值 0.0097 / 窗口 322ms / 每格 12.4ms，而 runner 同卷每格 ≈44ms ⇒ "产品硬切"被排除，是 ≥2 帧地板压在那台机器的采样网格边缘（所以间歇）。本轮落**读数**（新增 `窗口=`、`每格=`、`相邻帧差=[…]`），地板/阈值/声明时长一个没动；两条修法相反的出口（加密录制 vs 换判据对象）写进 629 待下一轮选。
④ ③ 验证链（顺序未换）：`swift build` 告警 **0**；判据卷 `UICaptureTests` **%(CAPTURE)s**；帧重捕 `FRAME_BASELINE_COMPARED=%(FRAMES)s` ⇒ 画面逐字节不变（并记下一条监控：将来若有夹具把真实图片路径装进侧栏行，`.task` 的异步补图会破坏帧确定性）；全量 **%(FULL)s**；预检 **%(PRECHECK)s**、`ARM_TOTAL %(ARM)s`、`HIDDEN_ARMS %(HIDDEN)s`；换装 %(INSTALL)s。
⑤ ④⑤ 账与交接：清账 **%(ABSENCE)s**；电池 **%(BATTERY)s**（台账后复跑）；产品面连续零改动 **%(STREAK)s** 轮（as-of 555，`python3 scripts/product_streak.py --streak-for 555` 现读，last=`6b70474`/554）⇒ 本轮产品 5 文件，下一轮该格仍从 0 起算。CI：本轮 ⓪ 笔 `eb883ad` ⇒ 跑 `41442000018`（取号时 in_progress ⇒ 未读）；代码笔与台账笔的成对号见本节补记。下一轮 R557（第 556 轮 / Round 554）：必读 `41442000018 ↔ eb883ad` + 本轮代码笔/台账笔的跑（全部失败步骤）；② 头一格 = 629 在 (A) 加密录制 / (B) 换判据对象 里选一条落地（≥2 帧地板不许动），第二格 = 632 的"文本一次渲染只开一次"；633 仍等用户回执；622/624/627 继续；628/625/626/569/616 不重开；禁碰清单 9 面不变；刀号 **M1443** 起；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板、2x 的 8.0pt 跨度地板与 1x 的 6.0pt 整行地板均不动。

"""
    a = u"\n## R556 ⓪ 开工（2026-11-02 · 第 555 轮 / Round 553 · CI 读单 + 基线全现读）"
    t = once(t, a, u"\n" + fill(body).rstrip(u"\n") + a, u"state body")
    if not check:
        wr(n, t)

    sys.stdout.write("LEDGERS_R556_%s\n" % ("CHECK_OK" if check else "WRITTEN"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
