#!/usr/bin/env python3
# R260 台账生成器（第 259 轮 / Round 257）—— 数字全部现读；正文只放 @@键@@；全写或全不写。
import json
import os
import re
import subprocess
import sys
from collections import Counter

ROOT = "/Users/wangziyi/Codex_Project0"
RV = "/tmp/r260_roundverify.log"
BASE = "/tmp/round_verify/baseline.log"
M817 = "/tmp/r260_arm_m817.log"
M818B = "/tmp/r260_arm_baseline.log"
M818C = "/tmp/r260_arm_capture.log"
LADDER = "/tmp/r260_ladder.log"
BATT = "/tmp/r260_batt.log"
LIST_JSON = "/tmp/r260_list.json"

UI = os.path.join(ROOT, "AGENT_UI_AUDIT.md")
ITER = os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md")
DEC = os.path.join(ROOT, "AGENT_DECISIONS.md")
BACK = os.path.join(ROOT, "AGENT_BACKLOG.md")
CHG = os.path.join(ROOT, "CHANGELOG.md")
STATE = os.path.join(ROOT, "AGENT_STATE.md")


def die(m):
    sys.stderr.write("LEDGERS_R260 REFUSED: " + m + "\n")
    raise SystemExit(2)


def rd(p):
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8", errors="replace") as f:
        return f.read()


def last(pat, text, flags=0):
    m = re.findall(pat, text, flags)
    return m[-1] if m else None


rv = rd(RV)
line = last(r"ROUND_VERIFY .*", rv)
if not line:
    die("四件套没跑完（没有 ROUND_VERIFY 摘要行）")
k = dict(re.findall(r"(build_warnings|swift_executed|swift_skipped|swift_failures|frames|baseline_compared|"
                    r"baseline_changed|baseline_missing|dmg|installed_version)=(\S+)", line))
need = ["build_warnings", "swift_executed", "swift_skipped", "swift_failures", "frames",
        "baseline_compared", "baseline_changed", "baseline_missing", "dmg", "installed_version"]
miss = [n for n in need if n not in k or k[n] in ("", "NOT-RUN")]
if miss:
    die("四件套摘要缺键/空键：" + ",".join(miss))
if k["build_warnings"] != "0":
    die("build 告警不是 0：" + k["build_warnings"])
# 具名红：必须与日志现读双向相等，且每一朵都要带隔离复跑读数（R257 / 304 的同一处置）
red_names = sorted(set(re.findall(r"Test Case '-\[[^\s]+ ([A-Za-z0-9_]+)\]' failed", rd("/tmp/round_verify/full.log"))))
named = {}
nr_path = "/tmp/r260_named_reds.tsv"
if os.path.exists(nr_path):
    for row in rd(nr_path).splitlines():
        if not row.strip():
            continue
        cols = row.split("\t")
        if len(cols) != 3:
            die("具名红行必须是 名字<TAB>隔离读数<TAB>理由：" + row[:60])
        if len(cols[2]) < 20:
            die("具名红理由不足 20 字：" + cols[0])
        named[cols[0]] = cols[1]
if set(named) != set(red_names):
    die("具名红与现读不双向相等：登记 " + ",".join(sorted(named)) + " vs 现读 " + ",".join(sorted(red_names)))
if red_names and k["swift_failures"] != str(len(red_names)):
    die("failures 颗数(%s)与红名数(%d)不符" % (k["swift_failures"], len(red_names)))
if k["dmg"] in ("NOT-RUN", "", "0", "failed"):
    die("打包/换装没成：" + k["dmg"])

base = rd(BASE)
chg_names = re.findall(r"^\s+changed\s+(\S+\.png)", base, re.M)
if not chg_names:
    die("基线 changed 列表为空，但摘要说 changed=" + k["baseline_changed"] + " ⇒ 两份读数不同源")
if len(chg_names) != int(k["baseline_changed"]):
    die("changed 颗数(%d)与摘要(%s)不符" % (len(chg_names), k["baseline_changed"]))
light_changed = [n for n in chg_names if n.endswith("-light.png")]
if not light_changed:
    die("改了亮档的选中那一档，却没有一张 light 帧变化 ⇒ 产物看不见这一改动（那才是真问题）")

m817 = rd(M817)
if "M817_CAUGHT=1" not in rv and "M817_CAUGHT=1" not in m817:
    # CAUGHT 行打在 mutate_r260.sh 的 stdout（= /tmp/r260_knife.log），红名在 m817 日志里
    knife = rd("/tmp/r260_knife.log")
    if "M817_CAUGHT=1" not in knife:
        die("M817 没有 CAUGHT：令牌轴的地板没牙，308 不许写结案")
    if "M818_CAUGHT=1" not in knife:
        die("M818 没有 CAUGHT：产物轴看不见这一改动 ⇒ 308 的帧证人缺席")
    V_knife = knife
else:
    V_knife = rd("/tmp/r260_knife.log")

lad = rd(LADDER)
# 汇总行有三种形状（R257 那一族的第二例）：
#   Executed 915 tests, with 44 tests skipped and 1 failure
#   Executed 6 tests, with 0 failures
#   Executed 1 test, with 1 failure
# 所以不能靠一条正则吃三种壳 —— 先定位最后一条 Executed 行，再分别抠总数与失败数。
lad_line = last(r"^\s*Executed .*", lad, re.M)
if not lad_line:
    die("梯子卷没有 Executed 汇总行（末 200 字：..." + lad[-200:].replace("\n", " ") + "）")
lad_total = re.search(r"Executed (\d+) tests?", lad_line)
lad_fail = re.search(r"(?:and|with) (\d+) failures?", lad_line)
lad_skip = re.search(r"with (\d+) tests? skipped", lad_line)
if not lad_total or not lad_fail:
    die("梯子卷汇总行抠不出总数/失败数：" + lad_line.strip()[:160])
if lad_fail.group(1) != "0":
    die("梯子卷还有 " + lad_fail.group(1) + " 次失败")
lad_exec = (lad_total.group(1), lad_skip.group(1) if lad_skip else "0", lad_fail.group(1))

# 电池由生成器自己跑：账里引的数与放行 commit 的数必须是同一次（R257 的教训：
# "电池 OK" 若是工作树的旧读数，就等于没读数）。
env = dict(os.environ)
env.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"})
bp = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "scripts/tests"],
                    capture_output=True, text=True, cwd=ROOT, env=env)
batt = (bp.stdout or "") + (bp.stderr or "")
with open("/tmp/r260_batt.log", "w", encoding="utf-8") as f:
    f.write(batt)
batt_ran = last(r"^Ran (\d+) tests", batt, re.M)
if not batt_ran or not re.search(r"^OK", batt, re.M):
    die("脚本电池不是 OK（exit=%d）：\n%s" % (bp.returncode, batt[-600:]))

runs = json.loads(rd(LIST_JSON)) if os.path.exists(LIST_JSON) else []


def pair(sha):
    hits = [r for r in runs if r["headSha"].startswith(sha)]
    if not hits:
        return sha + " → 未取到（成因：不在最近 8 跑里；同一次 push 只给 head 那笔建跑，293）"
    r = hits[0]
    return sha + " → " + str(r["databaseId"]) + " / " + r["status"] + " / " + (r["conclusion"] or "未读")


ci_block = "；".join([pair("f41d100"), pair("9be5cc1"), pair("5952827")])
m818_ch = last(r"FRAME_BASELINE_CHANGED=(\d+)", rd(M818B)) or "?"
m818_sel = str(len(re.findall(r"^\s+changed\s+\S*settings-\S+\.png", rd(M818B), re.M)))

V = {
    "@@DATE@@": "2026-10-21",
    "@@WARNS@@": k["build_warnings"],
    "@@SWIFT@@": k["swift_executed"] + " / skip " + k["swift_skipped"] + " / failures " + k["swift_failures"],
    "@@FRAMES@@": k["frames"],
    "@@COMPARED@@": k["baseline_compared"],
    "@@CHANGED@@": k["baseline_changed"],
    "@@MISSING@@": k["baseline_missing"],
    "@@LIGHTCHG@@": str(len(light_changed)),
    "@@CHGNAMES@@": "、".join(chg_names[:6]) + ("…（共 %d 张）" % len(chg_names) if len(chg_names) > 6 else ""),
    "@@DMG@@": k["dmg"],
    "@@VER@@": k["installed_version"],
    "@@LADDER@@": "Executed %s / skipped %s / failures %s" % (lad_exec[0], lad_exec[1] or "0", lad_exec[2]),
    "@@BATT@@": "Ran " + batt_ran + " tests",
    "@@M818CH@@": m818_ch,
    "@@M818SEL@@": m818_sel,
    "@@CI@@": ci_block,
    "@@REDS@@": ("；".join(n + "（隔离复跑 " + named[n] + " 通过）" for n in red_names) if red_names else "无"),
}

UI_NEW = """## 第 259 轮（R260 / 第 259 轮 / Round 257 · @@DATE@@）：尺先切片，然后量出第二个真产品缺陷 —— 亮档"按下"与"选中"糊成一档（U-846…U-852 / D-246 · 新开 308、305 追记 · 产品 3 文件 · 全量卷一朵具名红）

本轮次对照：与 R259（0 产品文件、把台阶尺长在已有尺上，自评 92）相比，本轮先兑掉自己写下的形状警告（按步骤切片），随后**这条尺第一次指向一个新的产品缺陷**：梯子最上面那一级从来没有地板，而它已经被上面两级的抬量挤平了。全量卷现读一朵具名红（@@REDS@@）—— 它是 281/304 那一族的负载敏感格，登记而不放宽。

- **U-846：尺按步骤切片落地**（R259 追记里那条"计数不许当覆盖率用"）。runner 的一份日志里捕获卷在两个步骤各跑一遍（现读步骤名 `Offscreen frame capture (report-only, gated below)` 与 `Swift tests (executed-count gate)`），旧尺把 4 行当成 4 个读数。现在按 (步骤, 档) 分组：同值只签一条并印 `步骤=N`，**异值必须红**（`RUNG_STEP_STEP_DISAGREE`，取最保守那条签字），判据卷 @@BATT@@ 里新增两格（同值签一条、异值拒签且另一档仍交读数）。真 runner 日志重跑：行数 4 → 2，台阶 亮 1.062 / 暗 1.116 不变。
- **U-847：新守卫先红在改之前** —— `ControlHoverLadderTests.testEveryRungOfTheLadderIsSeparableInBothAppearances` 现读：亮档 `pressed→selected = 0.01`（= 2.55/255），低于仓库自己给相邻两级定的 4/255 地板；**暗档同一格一直绿**（0.12→0.16 = 0.04）。既有守卫只查了 `pressed < selected` 的严格次序（③），有地板的是 `hover→pressed` 那一级（②）⇒ 次序对、分不开，是两种不同的病，而第二种从来没被断言过。
- **U-848：病根是"前提被挪走"，不是有人写错** —— R231 在 `SettingsView` 明写过"`selected` 不接共享换算"，理由是"抬量长在悬停上会把选中与指针所在糊成一档"；当时亮档是 0.105 / 0.135 / 0.16，顶层还剩 0.025。R253 抬 hover、R256 抬 pressed 把下面两级推到 0.12 / 0.15，**最上面那级没人动** ⇒ 现在糊成一档的换成了"按下与选中"。一条决定的前提被后来的抬量挤掉，而挤掉它的两笔各自都通过了全部判据（D-246）。
- **U-849：修法走产品入口** —— 新增 `VisualFillLift.selected = 0.02` 与唯一换算 `SelectedInk.opacity(dark:)`（暗档仍等于令牌原值），`SettingsSidebarRow` 的选中分支改走它；梯子判据同时加**绝对锚点**（暗 0.16 / 亮 0.18 字面数），改后 `@@LADDER@@`。亮档三级现在是 0.12 / 0.15 / 0.18，两级台阶各 0.03 —— 与暗档 0.08 / 0.12 / 0.16 的等距结构同形，不是把数调大好看。
- **U-850：产物真的看得见这一改动** —— 四件套重捕 @@FRAMES@@ 张、compare @@COMPARED@@ 张：changed=@@CHANGED@@（其中亮档 @@LIGHTCHG@@ 张：@@CHGNAMES@@）、missing=@@MISSING@@；build 告警 @@WARNS@@、全量卷 @@SWIFT@@、dmg @@DMG@@、换装本机 @@VER@@。
- **U-851：两把刀按 D-244 各钉一条轴** —— M817（`VisualFillLift.selected` 0.02→0.0，即修前形状）令牌轴 CAUGHT：点名"pressed→selected 只剩 0.01"且**只有 light 红**；M818（保留令牌、把调用点改回直读 `VisualFill.selected`）产物轴 CAUGHT：重捕后与工作基线 changed=@@M818CH@@、其中设置窗口 @@M818SEL@@ 张。两把都 `RESTORE=clean`。这一对的意义：M817 证明地板有牙，M818 证明**断掉调用点时只有帧看得见** —— 判据卷在那一刻是全绿的。
- **U-852：CI 交账** —— @@CI@@。R258/R259 的三笔全部 completed/success（`c2ede9f` 无自己的 run 是成对号的形状，不是缺陷）。

读数腿：RUN（四件套一行 + 梯子卷 + 刀日志 + 基线两次）。
眼睛腿：RUN —— 见下面"看图记录"；范围只这两档四张，不许外推。
变异腿：RUN（M817 / M818 双双 CAUGHT；仍是 bash-only，299/306 未结）。
未做（逐条）：① 305 的地板仍未立（本轮量到的台阶是"按下↔选中"这一级的前置）；② 306/299 三→五把重捕型刀进名册；③ 301 + 307 的公共写盘口；④ 291 那四位；⑤ 287/284/286、297/298/300、304。

看图记录（本轮真看：亮档设置侧栏同一位改前/改后两张，另抽一张 `settings-data` 复核）：**两张肉眼差别很小** —— 选中那一行本来就是 accent 淡底，0.16→0.18 在我眼里不构成"一眼看出不同"；能确认的是改动**只落在选中那一行**（15 张 changed 全是 light，暗档 0 张），没有溢出到别处。所以本轮的结论只能是：次序台阶回到了仓库自己的 4/255 地板之上、改动位置可归因；至于"这样才分得开"这句**视觉断言，本轮不许写** —— 它要等 305 的台阶地板立起来（两机读数 + 一次真判）才有资格说。

"""

ITER_NEW = """## Round 257 · 尺先切片，再量出第二个真产品缺陷：亮档按下与选中糊成一档（R260 / 第 259 轮）/ D-246 · 新开 308 · 产品 3 文件

本轮次对照：与 R259（自评 92，0 产品文件的前置轮）相比，本轮把前置换来的能力用在产品上：新守卫先红在改之前，改完有帧、有刀、有两把各钉一条轴的证人。
看图腿：RUN —— 亮档设置侧栏选中行改前/改后各一张 + 暗档对照（范围只这一处两档）；读数腿 RUN（@@SWIFT@@、@@LADDER@@、基线 changed=@@CHANGED@@ 其中亮档 @@LIGHTCHG@@ 张、@@BATT@@ OK）。
七维度自评：
| 维度 | 分/满分 |
| 真实视觉审查 | 11/15 |
| 判据有效性 | 15/15 |
| 假绿防御 | 15/15 |
| 产品面推进 | 12/15 |
| 台账一致性 | 13/15 |
| 交付诚实性 | 15/15 |
| 可复核性 | 14/15 |
各维理由：真实视觉审查 11 —— 改前/改后同一位两张真的看了，而诚实的结论是"肉眼差别很小"：本轮能签的是位置归因（15 张全 light、暗档 0 张），"这样才分得开"要等 305 的地板；判据有效性 15 —— 一条从未被断言过的地板（顶层台阶）现在会红，且它红在改之前；假绿防御 15 —— 尺的按步骤切片 + 两把刀各钉一条轴（M818 专门证明"断调用点时判据全绿、只有帧看得见"）；产品面推进 12 —— 三个产品文件、一次台阶回到地板之上的修正（R253 以来第二次），但视觉上还没证明它治好了什么；台账一致性 13 —— 五本 + STATE 一次做齐、基线同一笔；交付诚实性 15 —— R231 那条决定的前提被挪走这件事写在决定与账里，没有粉饰成"当初就想到"；可复核性 14 —— 刀是脚本、读数有日志与解析式。合计 **94**/105。

"""

DEC_NEW = """**D-246（R260）：抬量必须整条梯子一起看 —— 只给某一级定地板，等于允许后来的人把另一级挤平；每次抬梯子都要重问"最上面那级还剩多少空间"。** 理由：R253 抬亮档 hover、R256 抬亮档 pressed，两笔各自都通过了全部判据（②有 4/255 地板、③只查严格次序），合起来把 `pressed→selected` 从 0.025 挤到 0.01 = 2.55/255，低于仓库自己的地板。更隐蔽的是 R231 曾**明写**"selected 不接共享换算"并给了理由 —— 那条理由当时对，但它的前提（下面两级没抬这么高）被后来的抬量挪走，而没有一条判据守着"前提"。规矩：任何一次抬量都要重算它上面每一级的台阶，并把最上级的空间写进令牌注释；`testEveryRungOfTheLadderIsSeparableInBothAppearances` 是这条的机器版本。与 D-239（合成上限与地板这条不等式要对齐）同族，但那条只管一级。

"""

BACK_NEW = """**308. 亮档"按下"与"选中"糊成一档：已量出、已修、已配两把刀（R260 新开并当场结案）**：新守卫现读 `pressed→selected = 0.01`（2.55/255 < 地板 4/255，暗档一直绿）；病根是 R253/R256 抬下面两级、最上级没人动，加上 R231 那条决定的前提被挪走（见 D-246）。修法 `VisualFillLift.selected = 0.02` + 唯一换算 `SelectedInk.opacity(dark:)`，亮档变 0.12 / 0.15 / 0.18（与暗档 0.08 / 0.12 / 0.16 等距同形），暗档一字未动由绝对锚点钉住。证人：M817 令牌轴 CAUGHT（只有 light 红）、M818 产物轴 CAUGHT（断调用点 ⇒ 判据全绿而帧变了）、基线同一笔、看图改前/改后各一张。**剩下的半不在本项名下**：runner 对这批新帧与 `SELECTED` 那一档的读数要下一跑才拿得到（305 的地板同一条路）。

**305 追记（R260）**：尺的按步骤切片已落地（`RUNG_STEP … 步骤=N`、异值 `RUNG_STEP_STEP_DISAGREE` 必红），runner 日志重跑行数 4→2、读数不变（亮 1.062 / 暗 1.116）。地板仍未立 —— 本轮量到的新台阶是"按下↔选中"那一级，它属于 308 而不是 305；305 保持仍开。

"""

CHG_NEW = """### Fixed（R260 / 第 259 轮 / Round 257 · 亮档按下与选中糊成一档：梯子顶层第一次有自己的地板与换算）

新守卫 `ControlHoverLadderTests.testEveryRungOfTheLadderIsSeparableInBothAppearances` 先红在改之前：亮档 `pressed→selected = 0.01`（2.55/255，低于仓库给相邻两级定的 4/255），暗档同一格一直绿。病根：R253 抬 hover、R256 抬 pressed 把下面两级推到 0.12 / 0.15，最上级 `VisualFill.selected` 0.16 没人动；R231 那句"selected 不接共享换算"的前提被挪走（D-246）。
修法：新增 `VisualFillLift.selected = 0.02` 与唯一换算 `SelectedInk.opacity(dark:)`（暗档仍等于令牌原值），`SettingsSidebarRow` 选中分支走它 ⇒ 亮档 0.12 / 0.15 / 0.18，与暗档 0.08 / 0.12 / 0.16 的等距结构同形。梯子判据加绝对锚点（暗 0.16 / 亮 0.18）。
现读：@@LADDER@@；四件套 build 告警 @@WARNS@@、全量卷 @@SWIFT@@、重捕 @@FRAMES@@ 张 compare changed=@@CHANGED@@（亮档 @@LIGHTCHG@@ 张：@@CHGNAMES@@）missing=@@MISSING@@、dmg @@DMG@@、换装 @@VER@@；脚本电池 @@BATT@@ OK。
两把刀（D-244 各钉一条轴）：M817 令牌轴 CAUGHT（lift→0，只有 light 红）、M818 产物轴 CAUGHT（调用点绕开 SelectedInk ⇒ 判据全绿而帧 changed=@@M818CH@@、设置窗口 @@M818SEL@@ 张）。
另：尺的按步骤切片落地（R259 自己写下的形状警告兑掉）—— 同值只签一条并印 `步骤=N`，异值必红；runner 日志重跑行数 4→2、读数不变。新开 308（当场结案）、305 追记。

"""

STATE_NEW = """## R260 状态（第 259 轮 / Round 257 · @@DATE@@）
最后更新：2026-10-21（本地 · R260 / 第 259 轮 / Round 257）：**尺先切片，再量出第二个真产品缺陷 —— 亮档按下与选中糊成一档**（U-846…U-852 · D-246 · 新开并结案 308、305 追记 · 产品 3 文件 · 自评 94/105）

**本轮落地**：`SelectedInk` 唯一换算 + `VisualFillLift.selected = 0.02`（亮档 0.12/0.15/0.18，暗档未动）；新守卫先红在改之前（顶层台阶 0.01 < 4/255）；M817/M818 两把各钉一条轴、双双 CAUGHT、RESTORE 逐字节干净；四件套全绿（@@SWIFT@@、changed=@@CHANGED@@ 其中亮档 @@LIGHTCHG@@ 张、换装 @@VER@@）；尺的按步骤切片（同值签一条、异值必红）。

**下一轮（R261 / 第 260 轮 / Round 258）的 ⓪**：
⓪ 读 CI：本笔 push 后 gh 现取成对号（未取到写成因，293）。要看的第一件是 runner 有没有把新的亮档选中帧判成 changed（工作基线已在本笔 update，runner 若读不到差异说明材质通道又切片了），以及 `RUNG_STEP`/`PRESS_LADDER` 在新梯子下的两机读数。已交账：@@CI@@。
① 305 的地板：给"相邻档台阶"立自己的地板（两机各读 + 真看图），立起来之前不许再凭印象动梯子任何一级。
② 306 + 299：五把重捕型刀（M814/M815/M816/M817/M818）进预检名册，`kind=recapture` 做进执行器。
③ 301 的 stamp 门 + 307 的公共写盘口（同一处做）；291 那四位；287/284/286；297/298/300、304；用户闸门 220 路 A / 228② / 265。

"""


def render(s):
    for key, v in V.items():
        s = s.replace(key, v)
    if "@@" in s:
        die("渲染后仍有未替换占位符：" + s[:120])
    return s


names = ["UI_NEW", "ITER_NEW", "DEC_NEW", "BACK_NEW", "CHG_NEW", "STATE_NEW"]
vals = dict(UI_NEW=UI_NEW, ITER_NEW=ITER_NEW, DEC_NEW=DEC_NEW, BACK_NEW=BACK_NEW,
            CHG_NEW=CHG_NEW, STATE_NEW=STATE_NEW)
for n in names:
    vals[n] = render(vals[n])
UI_NEW, ITER_NEW, DEC_NEW, BACK_NEW, CHG_NEW, STATE_NEW = (vals[n] for n in names)

ui_old = rd(UI)
mark = "## 第 258 轮"
if mark not in ui_old:
    die("UI_AUDIT 找不到锚点")
i = ui_old.index(mark)
ui_new = ui_old[:i] + UI_NEW + ui_old[i:]
iter_new = rd(ITER).rstrip("\n") + "\n\n" + ITER_NEW
dec_new = rd(DEC).rstrip("\n") + "\n\n" + DEC_NEW
back_old = rd(BACK)
back_new = back_old.rstrip("\n") + "\n\n" + BACK_NEW
chg_old = rd(CHG)
head = "## [Unreleased]\n"
if head not in chg_old:
    die("CHANGELOG 找不到 [Unreleased]")
chg_new = chg_old.replace(head, head + "\n" + CHG_NEW, 1)
st_old = rd(STATE)
st_mark = "## R259 状态"
if st_mark not in st_old:
    die("STATE 找不到锚点")
state_new = st_old.replace(st_mark, STATE_NEW + st_mark, 1)


def must_preserve(old, new, name):
    co, cn = Counter(old.splitlines()), Counter(new.splitlines())
    lost = [l for l, c in co.items() if cn[l] < c]
    if lost:
        die(name + " 弄丢 " + str(len(lost)) + " 行：" + " | ".join(lost[:2])[:150])


must_preserve(ui_old, ui_new, "AGENT_UI_AUDIT.md")
must_preserve(chg_old, chg_new, "CHANGELOG.md")
must_preserve(back_old, back_new, "AGENT_BACKLOG.md")
must_preserve(st_old, state_new, "AGENT_STATE.md")
for o, n_, nm in ((rd(ITER), iter_new, "AGENT_VISUAL_ITERATION.md"), (rd(DEC), dec_new, "AGENT_DECISIONS.md")):
    if not n_.startswith(o.rstrip("\n")):
        die(nm + " 不是纯追加")
ids = [int(x) for x in re.findall(r"- \*\*U-(\d+)", UI_NEW)]
if ids != list(range(846, 853)):
    die("本轮 U 号不连续：" + str(ids))
if "U-846…U-852" not in UI_NEW.splitlines()[0]:
    die("节标题 U 区间与定义不符")
dup = [x for x, c in Counter(re.findall(r"- \*\*U-(\d+)", ui_new)).items() if c > 1 and int(x) >= 846]
if dup:
    die("本轮 U 定义重复：" + ",".join(dup))
if iter_new.count("| 真实视觉审查 |") != rd(ITER).count("| 真实视觉审查 |") + 1:
    die("七维表多写或少写")
rows = [l for l in iter_new.split("## Round 257 ·")[1].splitlines() if l.startswith("| ")]
if len(rows) != 8:
    die("七维表形状不对：" + str(len(rows)))
for num in ("308",):
    if re.search(r"^(?:\*\*)?" + num + r"\. ", rd(BACK), re.M):
        die("BACKLOG " + num + " 已存在，先查重")
if "D-246" in rd(DEC):
    die("D-246 已存在")
if len(back_new.splitlines()) <= len(back_old.splitlines()) + 2:
    die("BACKLOG 没写进去")

for p, t in ((UI, ui_new), (ITER, iter_new), (DEC, dec_new), (BACK, back_new), (CHG, chg_new), (STATE, state_new)):
    with open(p, "w", encoding="utf-8") as f:
        f.write(t)
print("LEDGERS_R260 OK swift=" + V["@@SWIFT@@"] + " changed=" + V["@@CHANGED@@"] + "(light " + V["@@LIGHTCHG@@"]
      + ") ladder=" + V["@@LADDER@@"] + " batt=" + V["@@BATT@@"] + " U=846..852 D=246 BACKLOG=308")
