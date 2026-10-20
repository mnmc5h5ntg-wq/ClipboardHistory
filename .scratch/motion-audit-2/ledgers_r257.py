#!/usr/bin/env python3
# R257 台账生成器 v2（补 R256 一整本 + 写 R257 本轮）
# 两条铁律：① 数字只从日志解析，抓不到就拒绝写盘；② 正文一律用 @@键@@ 占位，
#            不做字符串拼接 —— 上一版就是被 CJK 正文里的 ASCII 双引号断掉的。
import re
import sys
import os
import json
from collections import Counter

ROOT = "/Users/wangziyi/Codex_Project0"
FULL_LOG = "/tmp/r257_full.log"
BUILD_LOG = "/tmp/r257_build.log"
FRAMES_SUMMARY = "/tmp/r257_frames_summary.txt"
NAMED_REDS = "/tmp/r257_named_reds.tsv"
RUNS_JSON = os.path.join(ROOT, ".scratch", "motion-audit-2", "r257_runs.json")

UI = os.path.join(ROOT, "AGENT_UI_AUDIT.md")
ITER = os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md")
DEC = os.path.join(ROOT, "AGENT_DECISIONS.md")
BACK = os.path.join(ROOT, "AGENT_BACKLOG.md")
CHG = os.path.join(ROOT, "CHANGELOG.md")

ISO_LOG = "/tmp/r257_iso.log"


def die(msg):
    sys.stderr.write("LEDGERS_R257 REFUSED: " + msg + "\n")
    raise SystemExit(2)


def rd(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


if not os.path.exists(FULL_LOG):
    die("全量卷日志不在盘上")
full = rd(FULL_LOG)
if "TEST_EXIT=" not in full:
    die("全量卷还没结束")

test_exit = int(re.findall(r"TEST_EXIT=(\d+)", full)[-1])
# 取末命中：内层 suite 也有 Executed 行
ex = re.findall(r"Executed (\d+) tests?(?:, with (\d+) tests? skipped)? and (\d+) failures?", full)
if not ex:
    die("抓不到 Executed 汇总行（宁可不写，也不写空键）")
total, skipped, failures = (int(x if x else 0) for x in ex[-1])

red_names = sorted(set(re.findall(r"Test Case '-\[[^\s]+ ([A-Za-z0-9_]+)\]' failed", full)))
red_secs = {}
for nm, sec in re.findall(r"Test Case '-\[[^\s]+ ([A-Za-z0-9_]+)\]' failed \(([0-9.]+) seconds\)", full):
    red_secs[nm] = sec

build_warnings = rd(BUILD_LOG).count("warning:") if os.path.exists(BUILD_LOG) else -1
if build_warnings == -1:
    die("build 日志不在盘上")

# 登记红必须有具名理由，且与解析到的红名双向相等（不许放宽成出口）
if not os.path.exists(NAMED_REDS):
    die("具名红登记文件不在盘上：" + NAMED_REDS)
named = {}
reasons = {}
for line in rd(NAMED_REDS).splitlines():
    if not line.strip():
        continue
    parts = line.split("\t")
    if len(parts) != 3:
        die("具名红行必须是 名字<TAB>隔离读数<TAB>理由（三段）：" + line[:60])
    named[parts[0]] = parts[1]
    reasons[parts[0]] = parts[2]
    if len(parts[2]) < 20:
        die("具名红理由不足 20 字：" + parts[0])
if set(named) != set(red_names):
    die("具名红名单与实际红名不双向相等：登记 " + ",".join(sorted(named)) + " vs 现读 " + ",".join(sorted(red_names)))

iso = {}
if os.path.exists(ISO_LOG):
    for nm, sec in re.findall(r"Test Case '-\[[^\s]+ ([A-Za-z0-9_]+)\]' passed \(([0-9.]+) seconds\)", rd(ISO_LOG)):
        iso[nm] = sec

# 帧基线
if not os.path.exists(FRAMES_SUMMARY):
    die("帧摘要不在盘上")
fs = rd(FRAMES_SUMMARY)
keys = {}
for k in ("BASELINE_STATUS", "FRAMES_TOTAL", "FRAME_BASELINE_COMPARED", "FRAME_BASELINE_CHANGED",
          "FRAME_BASELINE_MISSING", "FRAME_BASELINE_CHANGED_RAW"):
    m = re.findall("^" + k + r"=(.*)$", fs, re.M)
    if not m:
        die("帧摘要缺键 " + k)
    keys[k] = m[-1].strip()
for k in ("BASELINE_STATUS", "FRAMES_TOTAL", "FRAME_BASELINE_COMPARED", "FRAME_BASELINE_CHANGED", "FRAME_BASELINE_MISSING"):
    if keys[k] == "":
        die("帧摘要键 " + k + " 有键无值")
raw = keys["FRAME_BASELINE_CHANGED_RAW"].replace("|", " ")[:110]
changed_names = re.findall(r"[A-Za-z0-9_\-]+\.png", raw)
chg_name = changed_names[0] if changed_names else "未点名（原文见 baseline.log）"

# CI 成对号
if not os.path.exists(RUNS_JSON):
    die("run id 只能从 gh 取，而 r257_runs.json 不在盘上")
runs = json.loads(rd(RUNS_JSON))
ci_lines = []
for sha in ("c7d8385", "c1dfd4b", "df2fd71", "359a261", "a01d17e", "c4fc11a"):
    hits = [r for r in runs if r["headSha"].startswith(sha)]
    if not hits:
        ci_lines.append(sha + " → gh 列表里没有（未取到，成因：不在最近 30 跑里）")
        continue
    r = hits[0]
    concl = r["conclusion"] if r["conclusion"] else "未读（" + r["status"] + "）"
    ci_lines.append(sha + " → " + str(r["databaseId"]) + " / " + r["status"] + " / " + concl)
ci_block = "；".join(ci_lines)

red_block = "、".join(
    nm + "（全量卷 " + red_secs.get(nm, "?") + "s 失败 / 隔离复跑 " + iso.get(nm, "未复跑") + "s 通过）理由：" + reasons[nm]
    for nm in red_names) if red_names else "无"

V = {
    "@@DATE@@": "2026-10-21",
    "@@TOTAL@@": str(total),
    "@@SKIPPED@@": str(skipped),
    "@@FAILURES@@": str(failures),
    "@@EXIT@@": str(test_exit),
    "@@WARNS@@": str(build_warnings),
    "@@RED@@": red_block,
    "@@REDNAMES@@": "、".join(red_names) if red_names else "无",
    "@@STATUS@@": keys["BASELINE_STATUS"],
    "@@FRAMES@@": keys["FRAMES_TOTAL"],
    "@@COMPARED@@": keys["FRAME_BASELINE_COMPARED"],
    "@@CHANGED@@": keys["FRAME_BASELINE_CHANGED"],
    "@@MISSING@@": keys["FRAME_BASELINE_MISSING"],
    "@@CHGNAME@@": chg_name,
    "@@CI@@": ci_block,
}

UI_A = """## 第 255 轮（R256 / 第 255 轮 / Round 253 · @@DATE@@）：「修等式」那一笔只有代码没有账 —— 产品 1 文件、五本台账 0 行、门只读 python 电池就把编译错的红树 push 了（U-825…U-827 / 新开 301、302 · 297/298/300 全部仍开 · 产品 1 文件）【R257 补记】

本节是**补记**：R256 五本台账一行没落，代码却已进 main。与 R255（把四件套脚本化，自评 84）相比，那一轮选的是 300 的「修等式」分支 —— 抬 VisualFillLift.pressed 把台阶修回 ≥4/255，并把真值表里那格把缺陷钉成契约的 0.085 改判成 0.10。

- **U-825：现读 git show --stat c7d8385 = 2 个文件**（Utilities/VisualTokens.swift 6 行、Tests/…/ControlHoverLadderTests.swift 11 行），而 UI_AUDIT / ITERATION / DECISIONS / BACKLOG / CHANGELOG 命中 0 行 ⇒ 「账与代码分两笔」第一次退化成「账整本缺席」。commit message 写得比台账还细不算证据：它不进任何守卫，也不进曲线。
- **U-826：那一笔是带着 TARGETED_EXIT=1 push 的**。提交链的门只 grep python 电池里那行 FAILED，Swift 自己的退出码从来没进过那条命令链 —— D-241 上一轮才立（改了产品视觉量的轮次，全量卷绿是收口的前置），一轮就破，而且破在同一句话上。这条不是「我忘了看日志」，是「链条里根本没有那个读点」。
- **U-827：红不是等式算错，是编译不过** —— /tmp/r256_targeted2.log 现读 ControlHoverLadderTests.swift:89:134 error: expected ',' separator：我把失败消息写成两个相邻的 Swift 字符串字面量，而 Swift 没有相邻字面量拼接。代价分级比想象的大：编译错把所有断言的机会一起拿走 ⇒ 全量卷从「4 failures」退化成「0 条断言跑过」，这是比放宽阈值更坏的假绿通道，因为它连「红」都不给你看。

读数腿：RUN（R257 现读补）—— 编译修好后第一次拿到完整卷：Executed @@TOTAL@@ tests, with @@SKIPPED@@ skipped and @@FAILURES@@ failures（TEST_EXIT=@@EXIT@@）。
眼睛腿：NOT-RUN —— R256 没看图，本轮也没补看图；那 0.03 的 pressed 抬量没有帧可依据 ⇒ 开 302。
变异腿：NOT-RUN —— R256 没插刀；本轮不替它补证（旧代码上得到的 CAUGHT 不能替新代码作证）。
未做（逐条）：① 301；② 302；③ 297/298/300 在判据能跑之前根本没有资格谈结案。

"""

UI_B = """## 第 256 轮（R257 / 第 256 轮 / Round 254 · @@DATE@@）：把「红得看不见」修回能红的形状，并补齐 R256 整本账 —— 全量卷现读 @@TOTAL@@ tests / @@SKIPPED@@ skipped / @@FAILURES@@ failures，帧基线 @@STATUS@@（changed=@@CHANGED@@ missing=@@MISSING@@）（U-828…U-833 / D-242、D-243 · 新开 301、302、303、304 · 产品 0 文件）

本轮次对照：与 R256（改了产品但判据根本没机会跑，且整本账缺席）相比，本轮 0 产品文件，换来三件实在东西：一份能跑的全量卷读数、一份能对的帧基线读数、上一轮那本缺失的账。它暴露的比它修的多 —— 一条门、一种编译级假绿、一处 pressed 覆盖缺口、一朵新的负载敏感红。

- **U-828：修法 = 失败消息压成一行，长理由搬进注释**，并把注释里那句已经过期的「亮档 0.085」同笔改判成 0.10（R256 只改了字面数没改注释 ⇒ 注释会变成第二份假账）。swift build 现读告警 @@WARNS@@ 颗。
- **U-829：300 的「修等式」分支第一次拿到完整卷判决** —— Executed @@TOTAL@@ / skipped @@SKIPPED@@ / failures @@FAILURES@@，红名：@@REDNAMES@@。R255 那两格梯子等式（testLightLadderClearsTheFloorAndKeepsTheStep、testFillOpacityTruthTableBothAppearances）不再出现 ⇒ 0.12 / 0.15 / 台阶 7.65/255 这套数在既有判据下自洽。但**这只是「等式不再冲突」，不是「那 0.04 那一步没改坏画面」**：那句话要 302 的帧与刀来答。
- **U-830：同一件事在 runner 上的回答（run id 全部从 gh 现取，未编造）** —— @@CI@@。那笔编译错不只红在本机：c7d8385 那一跑 CI 自己就是 failure，而我当时的门看不见它。步骤正文本轮未读（预算只剩最后几笔）。
- **U-831：帧基线腿第一次给出可对照的读数** —— 重捕 @@FRAMES@@ 张、compare @@COMPARED@@ 张：changed=@@CHANGED@@ missing=@@MISSING@@，变了的那张是 @@CHGNAME@@。注意这条结论的边界：现有夹具里**没有 pressed 态位点**，所以 changed 这一格无论多少都**不能**读成「那 0.03 没改坏画面」—— 量不到不是清白（与 291 同族），302 因此要的是能供电 isPressed 的捕获键，不是再一次 compare。
- **U-832：门缺口具名化** —— 「动过 Swift ⇒ 提交前必须有一条会红的退出码读点」这一轮仍然只存在于我手写的命令链里，不在仓库里。301 的形状写死：由 scripts/round_verify.sh 自己落 stamp（当前树 + swift 退出码 + 帧目录），判据读不到或不匹配就 exit 1；动手前先答三条嫌疑（stamp 落哪、跨机会不会分叉、会不会被 253 那条 skip 通道喂饱）。
- **U-833：一朵新红，没有放宽、也没有当成已通过** —— @@RED@@。处置：登记成 304（预算贴着墙钟的判据在负载下会翻面，两种相反成因还没分开），本轮**不**改它的阈值，也**不**因为「隔离能过」就把它写成已通过；全量卷的 failures=@@FAILURES@@ 就按 @@FAILURES@@ 记。

读数腿：RUN（全量卷 + 帧基线 @@STATUS@@ + 隔离复跑各一条）。
眼睛腿：NOT-RUN —— 本轮没有看帧；R253/R256 两笔产品改动累计欠改前/改后对照（302）。
变异腿：NOT-RUN —— 本轮 0 产品文件、无新刀；R256 那笔至今无刀（302）。
未做（逐条）：① 301 的 stamp 门；② 302 的刀与看图与 pressed 捕获键；③ 303 的 STATE ⓪ 与 FINAL_REPORT 计数器；④ 304 那朵红的分辨实验；⑤ 297/298/300 全部仍开，CI 步骤正文未读。

"""

ITER_A = """## Round 253 · 亮档 pressed 抬量 0.015→0.03：300 选「修等式」那一支（R256 / 第 255 轮）/ 产品 1 文件【R257 补记，不计分】

补记，不是当轮自评 —— R256 当时没写这张表。为了不让曲线掺进事后打分，这一节只列事实不列分：全量卷未跑（只有 TARGETED_EXIT=1，事后证明是编译错）、看图未做、变异刀未插、五本台账 0 行。分数留给下一个真实轮次（Round 254）。

## Round 254 · 把编译级假绿修回能红的形状 + 补齐 R256 整本账（R257 / 第 256 轮）/ D-242、D-243 · 新开 301、302、303、304 · 产品 0 文件

本轮次对照：与 R256（改产品但判据跑不了）相比，本轮 0 产品文件，换来 Executed @@TOTAL@@ 的真实读数、一份 changed=@@CHANGED@@ 的帧基线，和一条被具名化的门缺口。
看图腿：读数腿 @@STATUS@@（重捕 @@FRAMES@@ 张 compare，changed=@@CHANGED@@ missing=@@MISSING@@，变的那张 @@CHGNAME@@）；眼睛腿 NOT-RUN（本轮没看图，债在 302）。
七维度自评：
| 维度 | 分/满分 |
| 真实视觉审查 | 7/15 |
| 判据有效性 | 13/15 |
| 假绿防御 | 15/15 |
| 产品面推进 | 5/15 |
| 台账一致性 | 11/15 |
| 交付诚实性 | 15/15 |
| 可复核性 | 13/15 |
各维理由：真实视觉审查 7 —— 帧基线第一次有可对照读数，但眼睛缺席且承认 pressed 在夹具里根本没有位点；判据有效性 13 —— 判据从「跑不了」恢复成「跑得出 @@FAILURES@@ 次失败」，这是本轮唯一实质能力增量；假绿防御 15 —— 三件事同时做到：编译级假绿写进 D-243、登记红要双向相等且理由 ≥20 字、changed 读数不许被写成「没改坏」；产品面推进 5 —— 本轮 0 产品文件，上一轮那 1 个文件至今没有帧与刀；台账一致性 11 —— 补齐 R256 一整本，代价是第一次出现「事后补记不计分」这种形状；交付诚实性 15 —— pushed 红树、CI failure、一朵未定性新红、四条腿缺席逐条写；可复核性 13 —— 每个数都标了来源日志与解析式。合计 **79**/105。

"""

DEC_A = """**D-242（R257）：改过 Swift 的轮次，提交链必须读 Swift 自己的退出码，而不是只看 python 电池 —— 「电池绿 + Swift 红」不是假设，是 R256 真实 push 出去的状态。** 理由：那一笔带着 TARGETED_EXIT=1 进 main，同一笔的 runner CI（run 39492493661）也是 failure，而当时我的门只覆盖 python 腿。门只覆盖一条腿，就等于把另一条腿的验收外包给下一轮才读得到的 CI。与 D-241 同族但主语不同：那条要求「跑」，这条要求「链条里有一个会红的读点」。

**D-243（R257）：Swift 没有相邻字符串字面量拼接 ⇒ 判据的失败消息只许写成一行；要写长理由就写进注释。更深一层的规矩：编译错是一种特殊假绿，它把所有断言的机会一起拿走，所以「全量卷有读数」本身要成为被检查的前提。** 理由：R256 把消息拆成两行，于是「完整卷怎么看 0.12/0.15 这套数」这个问题两轮里都没被回答过，而链条当时给的是「电池 OK」。附属修正：注释里过期的数（亮档 0.085）要同笔改掉，否则注释变成第二份账。同一族也解释了我这次写台账生成器的失败方式 —— 正文里的 ASCII 双引号断掉的是生成器，改法一样：把注入从拼接换成占位符，并让 ast.parse 排在执行之前。

"""

BACK_A = """**301. 把「本轮动过 Swift ⇒ 提交前必须有一条会红的退出码读点」从手写的命令链变成仓库里的东西（R257 新开）**：形状 —— scripts/round_verify.sh 已经把四件套压成一行摘要，但它不写「这份树被验过」的戳；需要一个由被测脚本自己落的 stamp（当前树 + swift test 退出码 + 帧目录），加一条会红的判据：动过 Sources/ 或 Tests/ 而 stamp 与当前树不符 ⇒ exit 1。动手前先写清三条嫌疑：① stamp 落哪（.local/ 不入库 vs 入库会跨机分叉）；② 与 253 那条「CI 不给 CLIPBOARD_HISTORY_UI_SHOTS 就走 skip」的通道会不会互相喂饱；③ 判定要读脚本自己打的那一行，不许调用方重扫（R98）。

**302. R256 的产品改动（亮档 VisualFillLift.pressed 0.015→0.03，台阶回到 7.65/255）没有变异刀、没有看图，而且现有夹具里根本没有 pressed 态位点（R257 新开）**：所以本轮 changed=@@CHANGED@@ 这个数**不许**读成「没改坏画面」，只能读成覆盖缺口（与 291 同族）。要补三件：① 一个能按 isPressed 供电的捕获键（与 hoveredForCapture / hoveredRowForCapture 同族，别自绘状态）；② 一把按 D-240「重捕型」跑法的刀，证明台阶读数确实来自那 0.03；③ 改前/改后同一位两张真看图。在此之前 300 不许结案、297 保持仍开。

**303. 交接债：AGENT_STATE.md 第 ⓪ 条与 AGENT_FINAL_REPORT.md 计数器仍停在 R255（R257 新开）**：STATE ⓪ 要写成本轮新笔的 run↔commit 成对号（run id 只能从 gh run list --json databaseId,headSha,status,conclusion 取，取不到就写「未取到 + 成因」，见 293）；FINAL_REPORT 三处要改并与 git log 对账 —— U 区间上界（现读 U-833）、轮次数、「最后一次动到 Sources/ 的轮次」（现读应为 R256 / c7d8385，R257 是 0 产品文件）。

**304. 一朵新登记的红：CapturePathWriteBudgetTests.testAddingACopyWithANearlyFullArchiveStaysInsideBudget 在全量卷里失败（@@RED@@），但没有放宽它，也没写成已通过（R257 新开）**：分辨实验欠的是「同一台机器、同一棵树、两跑对照」——现在只有「全量卷 1 次失败 / 隔离 1 次通过」两个单遍读数，按 R87 的规矩单遍读数不配给产品定罪，两种相反成因（这台机器负载 vs 该判据的墙钟预算本来就贴边）还没被分开。要做的第一步：把这条判据的预算量成相对量（同一次运行内的比值），并在注释里写清它量的是墙钟还是写盘次数。

"""

CHG_A = """### Fixed（R257 / 第 256 轮 / Round 254 · 修回能红的形状：判据从「编译不过」恢复成「跑得出读数」）

R256 把一条失败消息写成两个相邻 Swift 字面量 ⇒ ControlHoverLadderTests.swift:89:134 error: expected ',' separator，于是两整轮的「全量卷」其实是 0 条断言跑过。本轮把消息压成一行、理由搬进注释，并同步把注释里过期的亮档 0.085 改判成 0.10。
现读：Executed @@TOTAL@@ tests, with @@SKIPPED@@ skipped and @@FAILURES@@ failures（红名 @@REDNAMES@@，TEST_EXIT=@@EXIT@@）；swift build 告警 @@WARNS@@ 颗；帧基线 @@STATUS@@（重捕 @@FRAMES@@ 张、compare @@COMPARED@@、changed=@@CHANGED@@、missing=@@MISSING@@，变的那张 @@CHGNAME@@）。
CI 成对号（gh 现取）：@@CI@@。
补账：R256 那一轮五本台账 0 行，本轮以【R257 补记】形状补齐，事后补记不计分以保曲线量纲。新开 301（提交链里的 Swift 退出码读点）、302（那 0.03 的刀与 pressed 捕获键）、303（STATE ⓪ 与 FINAL_REPORT 计数器）、304（那朵负载敏感的红）；297/298/300 全部仍开。

### Changed（R256 / 第 255 轮 / Round 253 · 亮档 pressed 抬量 0.015→0.03：300 选「修等式」那一支）

VisualFillLift.hover 抬到 0.04 之后，controlHover 那一档的 hover→pressed 台阶被压成 0.015（= 3.82/255 < 地板 4/255）⇒ 抬 pressed 到 0.03：台阶 7.65/255，次序仍是 hover(0.12) < pressed(0.15) < selected(0.16)。
真值表同步改判：亮档 hover 0.105→0.12、pressed 0.135→0.15、行那一档 0.085→0.10 —— 旧字面数把缺陷钉成了契约，而 1.171 < 1.20 正是它换来的那一格。
代价（R257 现读，见 D-242/D-243）：那一笔没有台账、没有刀、没看图，且带着编译错 push；CI c7d8385 → 39492493661 为 failure。

"""


def fill(s):
    for k, v in V.items():
        s = s.replace(k, v)
    return s


for nm in sorted(V):
    for src in (UI_A, UI_B, ITER_A, DEC_A, BACK_A, CHG_A):
        pass
leftover = [m for blk in (UI_A, UI_B, ITER_A, DEC_A, BACK_A, CHG_A) for m in re.findall(r"@@[A-Z]+@@", blk) if m not in V]
if leftover:
    die("占位符没有对应读数：" + ",".join(sorted(set(leftover))))
if re.search(r"@@[A-Z]+@@", fill(UI_A + UI_B + ITER_A + DEC_A + BACK_A + CHG_A)):
    die("渲染后仍有未替换占位符")

ui_old = rd(UI)
mark = "## 第 254 轮"
if mark not in ui_old:
    die("UI_AUDIT 找不到锚点")
idx = ui_old.index(mark)
ui_new = ui_old[:idx] + fill(UI_A) + fill(UI_B) + ui_old[idx:]

iter_new = rd(ITER).rstrip("\n") + "\n\n" + fill(ITER_A)
dec_new = rd(DEC).rstrip("\n") + "\n\n" + fill(DEC_A)
back_new = rd(BACK).rstrip("\n") + "\n\n" + fill(BACK_A)
chg_old = rd(CHG)
head = "## [Unreleased]\n"
if head not in chg_old:
    die("CHANGELOG 找不到 [Unreleased]")
chg_new = chg_old.replace(head, head + "\n" + fill(CHG_A), 1)


def must_preserve(old, new, name):
    co, cn = Counter(old.splitlines()), Counter(new.splitlines())
    lost = [l for l, c in co.items() if cn[l] < c]
    if lost:
        die(name + " 插入过程弄丢了 " + str(len(lost)) + " 行原文（插入实为替换）：" + " | ".join(lost[:2])[:160])


must_preserve(ui_old, ui_new, "AGENT_UI_AUDIT.md")
must_preserve(chg_old, chg_new, "CHANGELOG.md")
for old_s, new_s, nm in ((rd(ITER), iter_new, "AGENT_VISUAL_ITERATION.md"),
                         (rd(DEC), dec_new, "AGENT_DECISIONS.md"),
                         (rd(BACK), back_new, "AGENT_BACKLOG.md")):
    if not new_s.startswith(old_s.rstrip("\n")):
        die(nm + " 不是纯追加（升序那本只能追加）")

ids = [int(x) for x in re.findall(r"- \*\*U-(\d+)", UI_A + UI_B)]
if ids != list(range(825, 834)):
    die("本轮 U 号不连续或数量不对：" + str(ids))
for blk, lo, hi in ((UI_A, 825, 827), (UI_B, 828, 833)):
    title = blk.splitlines()[0]
    if ("U-" + str(lo) + "…U-" + str(hi)) not in title:
        die("节标题 U 区间与正文定义不符：" + title[:90])
dup = [k for k, c in Counter(re.findall(r"- \*\*U-(\d+)", ui_new)).items() if c > 1 and int(k) >= 825]
if dup:
    die("本轮 U 定义重复：" + ",".join(dup))
if iter_new.count("| 真实视觉审查 |") != rd(ITER).count("| 真实视觉审查 |") + 1:
    die("七维表多写或少写")
rows = [l for l in iter_new.split("## Round 254 ·")[1].splitlines() if l.startswith("| ")]
if len(rows) != 8:
    die("七维表形状不是表头+7 行，现读 " + str(len(rows)))
for num in ("301", "302", "303", "304"):
    if re.search(r"^(?:\*\*)?" + num + r"\. ", rd(BACK), re.M):
        die("BACKLOG " + num + " 已存在，先查重")
if failures == 0 and red_names:
    die("failures=0 却有红名，解析与日志不一致")

for path, text in ((UI, ui_new), (ITER, iter_new), (DEC, dec_new), (BACK, back_new), (CHG, chg_new)):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

print("LEDGERS_R257 OK swift=" + str(total) + "/" + str(skipped) + "/" + str(failures) +
      " exit=" + str(test_exit) + " warnings=" + str(build_warnings) +
      " frames=" + V["@@STATUS@@"] + " compared=" + V["@@COMPARED@@"] +
      " changed=" + V["@@CHANGED@@"] + " missing=" + V["@@MISSING@@"] +
      " reds=" + V["@@REDNAMES@@"] + " U=825..833 D=242..243 BACKLOG=301..304")
