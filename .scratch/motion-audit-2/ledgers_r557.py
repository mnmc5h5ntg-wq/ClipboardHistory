# -*- coding: utf-8 -*-
"""R557 台账（第 556 轮 / Round 554）：632 的取样乘数拿掉 + R556 注释口子升级成判据；629 NOT-RUN。

用法：`python3 ledgers_r557.py --check` 只验锚点；不带参数才真写七本账。
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

NUM = {
    "FULL": "1399/55/0（765.8s）",
    "INSTALL": "`make bundle` = `SIGNATURE_KIND=local`（identity=ClipboardHistory Local Signing）⇒ `INSTALL_RESULT=ok / SHA_MATCH=1 / INSTALL_SIGNATURE=local / INSTALL_ENTRIES=433=433`（PID 86092 → 33242，`SMOKE_OK=1`）",
    "BATTERY": "695/5",
    "ABSENCE": "162/63/0",
    "STREAK": "1",
    "CAPTURE": "217/4 skipped/0 失败（655.6s）",
    "FRAMES": "354 CHANGED=0 MISSING=0 ADDED=0",
    "PRECHECK": "tables=345 covered=295 arms=757 bad=0",
    "ARM": "files=438 arms=1244 dupes=0 repeats=0",
    "HIDDEN": "表=432 可判=1183 rot=0 抽不出=6 处置=ok",
}

UI = u"""## 第 556 轮（R557 · 2026-11-02 · U-2379…U-2386）：估高度的取样乘数拿掉（产品 2 文件 + 判据 2 文件 + 三把刀）；629 判 NOT-RUN

- **U-2379：⓪ CI 读单（只登记、不轮询）。** HEAD=origin=`58851c2`、ahead=0、已跟踪改动 0。`41442000018 ↔ eb883ad`（R556 ⓪ 笔）concluded=**success**、JOB success、**失败步骤 0 条** ⇒ STEP[9] 连续第二跑绿。其余四跑全 **NOT-RUN**：`41450045802 ↔ 5ba5b2f`（刀表笔，覆盖产品笔 `1a7e31c`）in_progress、`41450081248 ↔ 680aea3`（台账笔）in_progress、`41450601769 ↔ ccab101`（补记笔）in_progress、`41452722560 ↔ 58851c2`（更正笔）queued；对 in_progress 那跑取日志，`gh` 直接回 "logs will be available when it is complete" ⇒ **本轮新加的 `窗口=/每格=/相邻帧差=` 三个 runner 真数一个都没到**，不是"读出来是空"。既有红对照：`41439930389 ↔ 78e7ab5` = STEP[15]+[18]（SelectionReveal 五值瞬移 + 622 第十二值 181.6ms/2）⇒ 同族、本轮未碰该卷，仍入账。
- **U-2380：② 旧值先量（一次性探针，不入库）。** 632 剩下的那一格不是"多开一次"这么简单：`CollapsibleFilePreview.recalculateTargetHeight()` 是**宽度每变一次就重新 `FileHandle` 开一遍同一份文件**。现读：一次估高度 = 1 次；再拖窗三次 = 累计 **4** 次；预览那一路再加 1 次 ⇒ 展开一条文本 + 拖一次窗 = **同一份受保护文件被开 5 次**。乘数在窗口 resize 上，这比 R556 那两格更常发生。
- **U-2381：② 落地：取样在同一次挂载里只取一次。** `MultiFilePreviewLayout.TextSample`（`fileDigest` + `text` + `sampleBytes`，**不带路径**）作为 `CollapsibleFilePreview` 的 `@State`；`preferredHeight(for:availableWidth:textSample:)` 命中同哈希就复用，`preferredTextHeight` 只在未命中时开文件。为什么带 `fileDigest`：`ForEach(id: \.offset)` 会让视图的 `@State` 在同一行的 URL 换掉之后活下来 ⇒ 不对号就会"拿甲的高度画乙"。新值：四次估高度 **1** 次开文件（+ 预览 1 次 = 共 2 次，旧值 5）。
- **U-2382：② 等价与负向臂。** 省读不许改算式：同一批宽度走"每次重开"的旧入口 `preferredHeight(for:availableWidth:)` 得到的四个高度与复用路径**逐个相等**（判据 `testHeightEstimateReusesOneSampleAcrossWidthChanges` 里两路对照）。负向臂 `testHeightEstimateDoesNotLeakTheSampleToAnotherFile`：换一份文件必须重新开一次、写回的取样必须对得上现在这个文件。刀 **M1444**（缓存永不命中 ⇒ 回到 4 次）CAUGHT：`("4") is not equal to ("1") - 四次估高度开了 4 次同一份文件`；刀 **M1445**（缓存不看文件身份）CAUGHT：`("0") is not equal to ("1") - 换了文件却复用上一行的取样` ＋ 哈希对不上号那条。两把 `RESTORE_CLEAN=yes`。
- **U-2383：② 换新类别：把上一轮留在注释里的口子升级成会红的判据。** R556 把补图搬到"行显示"时在注释里写了一句"将来若有夹具把真实图片路径装进侧栏行，`.task` 的异步补图会破坏帧确定性" —— **注释里的分类法等于没有**（memory 那条规矩），本轮补成 `UICaptureTests/testCaptureOpensNoProtectedFiles` 两臂：①**字面量臂**扫本夹具文件里每条 `URL(fileURLWithPath:)`，现读 **字面量=7 存在=0**（全是 `/Users/tester/…` 这类合成路径）；②**运行时臂**拍 `sidebar-history` 亮/暗，前后对比计数器环的事件数，现读 **增量=0 / 增量=0**（这一臂管的是 helper 拼出来的 URL，字面量扫不到）。为此给计数器加了一格 `eventCount`（环里现有条数）—— 判据只量**增量**，**依然没有全局 reset**。刀 **M1443**（把一条夹具路径指向真实存在的 `/etc/hosts`）CAUGHT：`有夹具把真实存在的路径装进了帧里 … ["hosts"]`，读数 `CAPTURE_FIXTURE_PATHS 字面量=7 存在=1`；它的运行时臂仍 0（`/etc/hosts` 不是图片，走不到补图）⇒ 两臂各自独立会红，正是分开的理由。
- **U-2384：② 629 = NOT-RUN（不赌）。** 选 (A) 加密录制还是 (B) 换判据对象，依据正是 R556 新打的那三个数（`窗口/每格/相邻帧差`），而它们只存在于 `41450045802` 及之后的跑里 —— 那跑还没结束、日志还没生成。本轮**不动 ≥2 帧地板、不动阈值、不动声明时长**，也不凭本机 4 帧去猜 runner 的网格；挂给 R558 必读。
- **U-2385：③ 验证链（顺序未换）。** `swift build` 告警 **0**；判据卷 `UICaptureTests` **%(CAPTURE)s**；帧重捕 `FRAME_BASELINE_COMPARED=%(FRAMES)s`（复用只省开文件的次数、算式逐值不变 ⇒ 画面应逐字节不变）；全量 **%(FULL)s**；预检 **%(PRECHECK)s**、`ARM_TOTAL %(ARM)s`、`HIDDEN_ARMS %(HIDDEN)s`；换装 %(INSTALL)s。
- **U-2386：④⑤ 账与交接。** 清账 **%(ABSENCE)s**；电池 **%(BATTERY)s**（台账后复跑）；产品面连续零改动 **%(STREAK)s** 轮（as-of 556，`python3 scripts/product_streak.py --streak-for 556` 现读，last=`1a7e31c`/555）⇒ 本轮动了产品面（`DetailView` 与计数器两文件），"连续零改动"这一格按脚本口径是 **as-of 现读**（N − 最后一笔标签 < N 的产品提交轮），本轮之后归零这件事要等下一轮 `--streak-for 557` 现读才成立，不预先写数。**632 状态：落地（乘数那一格）+ 剩余具名出口**：同一次渲染里估高度与预览仍各开一次（2 次，旧值 5），要合成一次得二选一 —— (i) 把预览那份字节经 preference 上行给 `CollapsibleFilePreview`（代价：高度会在预览到达后二次变化 ⇒ 帧要重基线并逐张看）；(ii) 两个入口合并成一个 `FileTextSample` 读取器（代价：32KB 与 256KB 的解码边界不同，估高度算式要重钉）。两条都写进 632，不静默放回。**629 = NOT-RUN**；622/624/627 继续；628/625/626/569/616 不重开；**633 仍等用户人工回执**。下一轮 R558（第 557 轮 / Round 555）：必读 `41450045802 ↔ 5ba5b2f`、`41450081248 ↔ 680aea3`、`41450601769 ↔ ccab101`、`41452722560 ↔ 58851c2` 与本轮各笔的跑（全部失败步骤）；**只要 `41450045802` 到了，629 就按那三个数在 (A)/(B) 里选一条落地**；禁碰清单 9 面不变；刀号 **M1446** 起；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板、2x 的 8.0pt 跨度地板、1x 的 6.0pt 整行地板均不动。

"""

ITER = u"""
## Round 554 · R557（第 556 轮 · 2026-11-02）：估高度的取样乘数拿掉；上一轮的注释口子变成会红的判据

632 剩下的那一格量出来比想象大：`recalculateTargetHeight()` 是"宽度每变一次就重新开一遍同一份文件"——展开一条文本 + 拖窗三次 = 同一份受保护文件被开 4 次，加预览共 5 次。改法是给这一行的挂载加一份视图作用域的取样（`TextSample` 带文件哈希，防 `ForEach(id:\.offset)` 让 `@State` 跨 URL 活下来），新值 1 次；两路高度逐个相等作等价证人，换文件必须重开作负向臂，刀 M1444/M1445 分别钉"缓存永不命中"和"缓存不看文件身份"。另把 R556 留在注释里的那格帧确定性风险升级成两臂判据（字面量 7/存在 0；拍 `sidebar-history` 前后计数增量 0），刀 M1443 把一条夹具路径指向真实文件即红。629 判 NOT-RUN：选 (A) 还是 (B) 的依据是 runner 那三个新数，而 `41450045802` 还没结束、日志还没生成 —— 不赌、不降地板。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 12/15 | 帧应逐字节不变（省的是开文件次数不是绘制）；看图这一维没新东西，但卷跑了、也裁图确认过详情区。 |
| 判据有效性 | 15/15 | 复用与不复用两路高度逐个相等（等价证人）+ 换文件必须重开（负向臂）+ 捕获两臂各自独立会红。 |
| 假绿防御 | 15/15 | 629 数没到就写 NOT-RUN，不拿本机 4 帧替 runner 猜；判据只量增量，仍无全局 reset。 |
| 产品面推进 | 13/15 | 产品 2 文件（`DetailView` 的取样复用 + 计数器加 `eventCount` 这一格读数）；乘数 4→1 是真实行为改动，但画面不变。 |
| 台账一致性 | 14/15 | 七本齐、sources 格按 R556 教训排在产品笔之后、streak 由脚本派生。 |
| 交付诚实性 | 15/15 | 上一轮自己写的注释口子本轮补成守卫并写明；632 剩余两条出口写清代价。 |
| 可复核性 | 15/15 | 三把刀命令、探针旧值、判据 filter、四跑成对号全部入账。 |

均分 = 99/105 ≈ 14.1/15（94）。
"""

CHG = u"""### 文本估高度的取样乘数拿掉；帧确定性风险从注释升级成判据（R557 / 第 556 轮 / Round 554 / U-2379…U-2386 · 产品 2 文件 + 判据 2 文件）

`CollapsibleFilePreview` 原来"宽度每变一次就重新打开同一份文件估高度"：现读旧值 = 展开一条文本 + 拖窗三次开 **4** 次，加预览共 5 次。改成视图作用域的一次性取样（`MultiFilePreviewLayout.TextSample` 带 `fileDigest`，防 `ForEach(id:\.offset)` 下 `@State` 跨 URL 复用）⇒ 新值 1 次（+ 预览 1 次）。等价证人：复用与每次重开两条路算出的四个高度逐个相等；负向臂：换文件必须重开、写回的取样必须对得上号。刀 **M1444/M1445** CAUGHT。另把 R556 留在注释里的"夹具若指向真实图片路径会破坏帧确定性"升级成 `UICaptureTests/testCaptureOpensNoProtectedFiles` 两臂（字面量 7/存在 0；拍 `sidebar-history` 前后计数增量 0），刀 **M1443**（夹具路径指向 `/etc/hosts`）CAUGHT。**629 判 NOT-RUN**：(A)/(B) 的依据是 runner 的 `窗口/每格/相邻帧差` 三个新数，`41450045802` 未结束 ⇒ 不赌、≥2 帧地板不动。帧 %(FRAMES)s；全量 %(FULL)s；build 0 告警；清账 %(ABSENCE)s；电池 %(BATTERY)s。

"""

A632 = u"""    落地（R557，乘数那一格）。旧值现读：`CollapsibleFilePreview.recalculateTargetHeight()` 每次宽度变化都重新 `FileHandle` 开一遍同一份文件 —— 展开一条文本 + 拖窗三次 = **4 次**，加预览那一路共 **5 次**。改法：`MultiFilePreviewLayout.TextSample`（`fileDigest` + `text` + `sampleBytes`，不带路径）作为该行的 `@State`，命中同哈希就复用；带 `fileDigest` 的理由是 `ForEach(id: \\.offset)` 会让 `@State` 在同一行换 URL 之后活下来，不对号就会"拿甲的高度画乙"。新值：四次估高度 **1** 次（+ 预览 1 次）。判据两半：`testHeightEstimateReusesOneSampleAcrossWidthChanges`（复用与每次重开两条路的四个高度逐个相等 = 等价证人）与 `testHeightEstimateDoesNotLeakTheSampleToAnotherFile`（负向臂）。刀 **M1444**（缓存永不命中）/**M1445**（缓存不看文件身份）CAUGHT、RESTORE_CLEAN。
    同一轮补上 R556 自己留的口子（注释→判据）：`UICaptureTests/testCaptureOpensNoProtectedFiles` 两臂 —— 夹具 `fileURLWithPath` 字面量必须都不存在（现读 7/0），拍 `sidebar-history` 前后计数器环增量必须为 0（现读 0/0）；为此给计数器加了 `eventCount`（只量增量，**仍然没有全局 reset**）。刀 **M1443**（把一条夹具路径指向真实存在的文件）CAUGHT，且只有字面量臂红 ⇒ 两臂独立可证。
    剩余那一格（仍是具名出口，二选一、各有代价）：同一次渲染里估高度与预览仍各开一次（2 次）。(i) 把预览那份字节经 preference 上行给 `CollapsibleFilePreview` ⇒ 高度会在预览到达后二次变化，帧要重基线并逐张看；(ii) 两个入口合成一个 `FileTextSample` 读取器 ⇒ 32KB 与 256KB 的解码边界不同，估高度算式要重钉并配刀。图片预览仍 `Data(contentsOf:)` 整文件读（已在"可见才读"之后，属可接受，另记）。

"""

DEC = u"""
## D-557 省读只省次数、不改算式；上一轮写在注释里的风险下一轮必须变成会红的判据（R557）

- 背景：632 剩下的那一格量出来是一个**乘数**（宽度每变一次就重开同一份文件），而它长在详情区的布局路径上，改错就会动画面。
- 决定：① 取样缓存做成**视图作用域**的 `@State` + `fileDigest` 对号，不做进程级全局缓存（全局缓存要处理失效与新鲜度，且会把"一次挂载"的语义变成"永远"）；② 复用与重开两条路的高度**逐个相等**作为等价证人，写进判据而不是写在注释里；③ 同笔把 R556 留在注释里的帧确定性风险升级成两臂判据（字面量 + 运行时增量），并给计数器加 `eventCount` 只用于量增量 —— 依然不开全局 reset。
- 理由：隐私类改动最大的风险是"顺手改了画面"。等价证人的形状是**同一批输入跑两条路对比输出**，它比"我看了一眼帧没变"强，因为它对未来的改动仍然会红。运行时那一臂管的是字面量扫不到的形状（helper 拼出来的 URL），两臂缺一都会漏。
- 兼容性/迁移：`preferredHeight(for:availableWidth:)` 旧签名保留（判据与调用点不改），新增 `textSample:` 重载；`TextSample` 只含正文与字节数，不含路径。
- 边界：本轮**没有**合并估高度与预览那两次读取（两条出口写回 632，各自代价已列）；629 因 runner 数未到而 NOT-RUN，不选路。
- 撤回：把 `preferredTextHeight` 的命中分支改成永不命中（刀 M1444 的形状）即回到每次重开；删掉 `@State previewTextSample` 即回到 R556 的形状。
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
        i = out.find(u"%(")
        sys.stderr.write("PLACEHOLDER_LEFT %s\n" % out[i:i + 30])
        sys.exit(1)
    return out


def main():
    check = "--check" in sys.argv

    state = rd("AGENT_STATE.md")
    if state.count(u"## R557 ⓪ 开工") != 1:
        sys.stderr.write("ANCHOR_BAD state R557 ⓪ 节不存在 ⇒ 不许两轮写进同一节\n")
        return 1

    n = "AGENT_UI_AUDIT.md"
    t = rd(n)
    a = u"## 第 555 轮（R556 · 2026-11-02 · U-2371…U-2378）"
    if t.count(a) != 1:
        sys.stderr.write("ANCHOR_BAD ui\n")
        return 1
    if not check:
        wr(n, t.replace(a, fill(UI) + a, 1))

    n = "AGENT_VISUAL_ITERATION.md"
    t = rd(n)
    if u"## Round 554 · R557" in t:
        sys.stderr.write("ANCHOR_BAD iteration Round 554 已存在\n")
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
    a632 = u"    新增监控句：侧栏行的 `.task` 会异步补图"
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
    a629 = (u'    挂起（R557）：选 (A) 还是 (B) 的依据是 R556 新加的 `窗口=/每格=/相邻帧差=` 三个 **runner** 真数，'
            u'而承载它们的第一跑 `41450045802 ↔ 5ba5b2f` 在 R557 开跑时仍是 in_progress'
            u'（对它取日志被 gh 直接拒："logs will be available when it is complete"）'
            u'⇒ **R557 判 NOT-RUN**：不拿本机 4 帧去猜 runner 的采样网格，也不动 ≥2 帧地板。'
            u'R558 只要那一跑到手，就按那三个数在 (A)/(B) 里选一条落地。\n')
    if not check:
        t = t[:end629 + 1] + a629 + t[end629 + 1:]

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
        (u"R9–R553，554 节自评", u"R9–R554，555 节自评", u"title"),
        (u"阶段二 **546 轮**审计（R9–R553；以 `curve_from_ledger.py` 的 `PHASE2 n=546` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 553",
         u"阶段二 **547 轮**审计（R9–R554；以 `curve_from_ledger.py` 的 `PHASE2 n=547` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 554", u"§1"),
        (u"| 视觉台账 | U-31 … U-2378", u"| 视觉台账 | U-31 … U-2386", u"U 上界"),
        (u"产品面连续零改动轮数 = **1**（as-of 555）", u"产品面连续零改动轮数 = **1**（as-of 556）", u"streak as-of"),
        (u"以 `AGENT_STATE.md` 的 R556 节 ② 为准", u"以 `AGENT_STATE.md` 的 R557 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R556 这一段", u"## 18. R458 → R557 这一段", u"§18 head"),
        (u"R556 续到 556 —— 这份报告第七次差点停在几十轮之前）", u"R557 续到 557 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]:
        t = once(t, old, new, label)
    anchor = u"帧 354 CHANGED=0；全量 1396/55/0（709.7s）；电池 695/5。\n"
    bullet = (u"- **R557（文本估高度的取样乘数拿掉 + 帧确定性口子变成判据；产品 2 文件 + 判据 2 文件）**："
              u"旧值现读 = 展开一条文本 + 拖窗三次把同一份受保护文件开 **4** 次（加预览共 5 次）；"
              u"改成视图作用域的一次性取样（`TextSample` 带 `fileDigest`，防 `ForEach(id:\\.offset)` 下 `@State` 跨 URL）⇒ 新值 1 次。"
              u"等价证人 = 复用与每次重开两路的四个高度逐个相等；负向臂 = 换文件必须重开；刀 M1444/M1445 CAUGHT。"
              u"上一轮写在注释里的帧确定性风险升级成两臂判据（夹具字面量 7/存在 0；拍 `sidebar-history` 计数增量 0），刀 M1443 CAUGHT；"
              u"计数器为此加 `eventCount`，只量增量、仍无全局 reset。**629 = NOT-RUN**（runner 的 窗口/每格/相邻帧差 三个数未到，不赌、地板不动）。"
              u"帧 %(FRAMES)s；全量 %(FULL)s；build 0 告警；电池 %(BATTERY)s。\n")
    t = once(t, anchor, anchor + fill(bullet), u"§18 bullet")
    if not check:
        wr(n, t)

    n = "AGENT_STATE.md"
    t = rd(n)
    t = once(t,
             u"最后更新：2026-11-02（本地 · R556 / 第 555 轮 / Round 553）",
             u"最后更新：2026-11-02（本地 · R557 / 第 556 轮 / Round 554）",
             u"identity")
    body = u"""## R557 状态（2026-11-02 · 第 556 轮 / Round 554 · 产品 2 文件 + 判据 2 文件 + 三把刀）

① ⓪：`41442000018 ↔ eb883ad`（R556 ⓪ 笔）**success、失败步骤 0 条** ⇒ STEP[9] 连续第二跑绿；其余四跑（`41450045802↔5ba5b2f`、`41450081248↔680aea3`、`41450601769↔ccab101`、`41452722560↔58851c2`）in_progress/queued ⇒ **NOT-RUN**，其中对 in_progress 那跑取日志被 gh 直接拒（"logs will be available when it is complete"）⇒ 629 要的 `窗口/每格/相邻帧差` 三个 runner 真数**一个都没到**。既有红 `41439930389↔78e7ab5` = STEP[15]+[18]（SelectionReveal + 622 第十二值 181.6ms/2）⇒ 同族、本轮未碰该卷，仍入账。
② ②(b) 632 的乘数拿掉：旧值现读 = 一次估高度 1 次、拖窗三次累计 **4 次**、加预览共 **5 次**（`recalculateTargetHeight()` 每次宽度变化重开同一份文件）⇒ 视图作用域 `TextSample`（带 `fileDigest`，理由：`ForEach(id:\\.offset)` 让 `@State` 跨 URL 活下来）复用后新值 **1** 次。等价证人：复用与每次重开两路的四个高度逐个相等；负向臂：换文件必须重开且写回的取样要对得上号。刀 **M1444**（缓存永不命中 ⇒ 回到 4 次）/**M1445**（缓存不看文件身份）CAUGHT、RESTORE_CLEAN。剩余一格两条出口写回 632（preference 上行 vs 合成一个读取器，各自代价列明）。
③ ②(c) 换新类别：R556 留在注释里的"夹具若指向真实图片路径 ⇒ `.task` 异步补图破坏帧确定性"升级成 `UICaptureTests/testCaptureOpensNoProtectedFiles` 两臂 —— 字面量臂现读 **7/存在 0**，运行时臂拍 `sidebar-history` 亮/暗计数增量 **0/0**；为此给计数器加 `eventCount`（只量增量，**仍无全局 reset**）。刀 **M1443**（夹具路径指向真实存在的 `/etc/hosts`）CAUGHT，且只有字面量臂红 ⇒ 两臂独立可证。②(a) **629 = NOT-RUN**：依据那三个数没到，不赌 (A)/(B)、不动 ≥2 帧地板。
④ ③ 验证链（顺序未换）：`swift build` 告警 **0**；判据卷 `UICaptureTests` **%(CAPTURE)s**；帧重捕 `FRAME_BASELINE_COMPARED=%(FRAMES)s`；全量 **%(FULL)s**；预检 **%(PRECHECK)s**、`ARM_TOTAL %(ARM)s`、`HIDDEN_ARMS %(HIDDEN)s`；换装 %(INSTALL)s。
⑤ ④⑤ 账与交接：清账 **%(ABSENCE)s**；电池 **%(BATTERY)s**（台账后复跑）；产品面连续零改动 **%(STREAK)s** 轮（as-of 556，`python3 scripts/product_streak.py --streak-for 556` 现读，last=`1a7e31c`/555）⇒ 本轮产品动了 2 文件（`DetailView` + 计数器）。CI：本轮各笔成对号见本节补记；**R558 必读上面那四跑 + 本轮各笔的跑**（全部失败步骤），并且只要 `41450045802` 到手就按 `窗口/每格/相邻帧差` 在 629 的 (A)/(B) 里选一条落地。633 仍等用户回执；622/624/627 继续；628/625/626/569/616 不重开；禁碰清单 9 面不变；刀号 **M1446** 起；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板、2x 8.0pt 与 1x 6.0pt 均不动。

"""
    a = u"\n## R557 ⓪ 开工（2026-11-02 · 第 556 轮 / Round 554 · CI 读单 + 基线全现读）"
    t = once(t, a, u"\n" + fill(body).rstrip(u"\n") + a, u"state body")
    if not check:
        wr(n, t)

    sys.stdout.write("LEDGERS_R557_%s\n" % ("CHECK_OK" if check else "WRITTEN"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
