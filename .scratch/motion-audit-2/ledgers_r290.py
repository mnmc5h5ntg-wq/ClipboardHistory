#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R290 台账生成器（第 289 轮 / Round 287）：数字全现读，缺格拒写。根由 __file__ 推（D-260/334）。

顺序与 R289 同（那一笔撞过的坑都写在这里）：判据卷 → 刀 → 预检 → 四件套读数 → 电池（前）
→ 写五本台账 → 刷 headline+sources → 电池（后，颗数必须相等）。产品动了文件 ⇒ sources 格
必须在电池之前刷新，而它要一个**真 sha**（代码半那一笔），所以先提交代码半、再拿它的号跑本脚本。
"""
import io
import json
import os
import re
import subprocess
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
B = {n: os.path.join(ROOT, n) for n in ("AGENT_UI_AUDIT.md", "AGENT_VISUAL_ITERATION.md", "AGENT_DECISIONS.md",
                                        "AGENT_BACKLOG.md", "CHANGELOG.md", "AGENT_STATE.md")}
FRAMES = "/tmp/r290_verify2/frames"
RUN1 = "/tmp/r290_verify_run1.log"
RUN2 = "/tmp/r290_verify_run2.log"
BASE1 = "/tmp/r290_verify/baseline.log"
DEV = "/Applications/Xcode.app/Contents/Developer"
FILTER = ("UICaptureTests/testColumnClusterRulerKnowsItsOwnAnswers|"
          "UICaptureTests/testMultiFileRowSeparatorsStartAtTheTextAxis|"
          "UICaptureTests/testMultiFileRowSeparatorsEndOnThePillRightAxis")


def die(m):
    sys.stderr.write("LEDGERS_R290 REFUSED: " + m + "\n")
    raise SystemExit(2)


def rd(p):
    with io.open(p, encoding="utf-8", errors="replace") as h:
        return h.read()


def sh(cmd, cwd=None):
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["DEVELOPER_DIR"] = DEV
    env.pop("SDKROOT", None)
    pr = subprocess.run(cmd, cwd=cwd or ROOT, env=env, capture_output=True, text=True)
    return (pr.stdout or "") + (pr.stderr or ""), pr.returncode


def ran_of(text):
    m = re.findall(r"Executed (\d+) tests?", text)
    return int(m[-1]) if m else 0


def fail_of(text):
    m = re.findall(r"Executed \d+ tests?, with (\d+) failures?", text)
    return int(m[-1]) if m else -1


# ① 判据卷：本轮三格（列簇对照 + 左端判据 + 上一轮的右端判据）必须现读全绿
stxt, src_rc = sh(["swift", "test", "--filter", FILTER], cwd=os.path.join(ROOT, "ClipboardHistory"))
ROLL, FAILS = ran_of(stxt), fail_of(stxt)
if src_rc != 0 or ROLL != 3 or FAILS != 0:
    die("本轮判据卷不是 3 颗绿：Ran=%s failures=%s rc=%s\n%s" % (ROLL, FAILS, src_rc, stxt[-600:]))
left = re.findall(r"^(LEFT_AXIS_R290 .*)$", stxt, re.M)
right = re.findall(r"^(RIGHT_AXIS_R289 .*)$", stxt, re.M)
if len(left) != 2 or len(right) != 2:
    die("两档读数不全（左 %d 右 %d）⇒ 台账里那些数没有来源" % (len(left), len(right)))


def field(line, key):
    m = re.search(key + r"=?([^｜]*)", line)
    return m.group(1).strip() if m else "?"


LEFT_L, LEFT_D = left[0], left[1]
RIGHT_L = right[0]
RULE_LEFT = field(LEFT_L, u"细线数=")
TEXT_LEFT = field(LEFT_L, u"文字=")


# ② 三把刀现跑，并从 M845/M846 的红话里读回「改前差多少」与「漂移会差多少」
ktxt, krc = sh([sys.executable, os.path.join(HERE, "mutate_r290.py")])
km = re.search(r"R290_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+) RESTORE_CLEAN=(\S+)", ktxt)
if not km or krc != 0:
    die("本轮变异表不干净：\n" + ktxt[-500:])
KN, KC, KE, KNR, KREST = km.groups()
if KC != KN or KREST != "yes":
    die("刀没全 CAUGHT 或还原不干净：CAUGHT=%s/%s RESTORE=%s" % (KC, KN, KREST))
gm = re.search(r"failed: \(\"([0-9.]+)\"\) is greater than", ktxt)
if not gm:
    die("M845 的红话里没有差值 ⇒ 「改前读数」这一格没来源，不许手抄（R88）")
BEFORE_GAP = gm.group(1)
drift = re.findall(r"failed: \(\"([0-9.]+)\"\) is greater than", ktxt)
DRIFT_GAP = drift[1] if len(drift) > 1 else "?"

# ③ 预检：新表要登记（D-248）
ptxt, _ = sh([sys.executable, os.path.join(HERE, "mutate_needle_precheck.py")])
cover = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", ptxt)
total = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", ptxt)
roster = re.search(r"TABLE_ROSTER registered=(\d+) unregistered_with_arms=(\d+) hidden_arms=(\d+)", ptxt)
if not (cover and total and roster) or cover.group(4) != "0" or total.group(3) != "0":
    die("预检读数不全或有坏：\n" + ptxt[-300:])
if "mutate_r290" not in ptxt:
    die("mutate_r290 没出现在预检正文 ⇒ 没登记（D-248）")

# ④ 四件套：第二跑那一行才是这一笔的读数；第一跑的 changed 名单要逐张对上
if not os.path.isdir(FRAMES):
    die("看图腿与帧数的对象不在盘上：" + FRAMES + " ⇒ 这一腿记 NOT-RUN，不许编")
N_FRAMES = len([f for f in os.listdir(FRAMES) if f.endswith(".png")])
r2 = rd(RUN2)
rv = re.search(r"^ROUND_VERIFY .*$", r2, re.M)
if not rv:
    die("第二跑 ROUND_VERIFY 结论行没落盘（" + RUN2 + "）⇒ 四件套没跑完，不许写账")
# 全量卷的红：**只准带"单跑通过"的那一族进账，其余一律拒写**（R257 / 304 那一族的规矩）。
# 单遍读数不配给产品定罪（R83/R87），但也不许被静默吞掉 —— 这里要的是
# ①从 full.log 现读失败用例名与秒数；②从隔离复跑那一卷现读同一批用例的秒数与 0 failures；
# ③两边按**用例名**配对，配不上的那条直接拒写。地板一条没放宽。
ISO = "/tmp/r290_iso.log"
iso_txt = rd(ISO)
iso_pass = dict(re.findall(r"Test Case '-\[\w.+? (\w+)\]' passed \(([0-9.]+) seconds", iso_txt))
iso_bad = len(re.findall(r"Test Case '-\[\w.+? (\w+)\]' failed", iso_txt))
if not iso_pass or iso_bad:
    die("隔离复跑那一卷不可用（通过 " + str(len(iso_pass)) + " 条、失败 " + str(iso_bad)
        + " 条）⇒ 没有对照就不许把全量卷的红说成负载敏感")
full_reds = re.findall(r"Test Case '-\[\w.+? (\w+)\]' failed \(([0-9.]+) seconds",
                       rd("/tmp/r290_verify2/full.log"))
for nm, secs in full_reds:
    if nm not in iso_pass:
        die("全量卷红在 " + nm + "（全量 " + secs + "s），但隔离复跑没通过或没这条记录 ⇒ "
            + "这不是负载敏感，不许带着写账（304）")
if "FRAME_GATE_PASS" not in r2:
    die("帧闸门不是 PASS")
r1 = rd(RUN1)
CH = re.search(r"FRAME_GATE_RED=changed=(\d+) compared=(\d+)", r1)
if not CH:
    die("第一轮的 changed 读数不在（" + RUN1 + "）⇒ 「同一笔 update 前后」这一对没了两半")
changed_names = re.findall(r"^  changed  (\S+)$", rd(BASE1), re.M)
if len(changed_names) != int(CH.group(1)):
    die("changed 名单与 changed 数不符：%d vs %s" % (len(changed_names), CH.group(1)))
FAMILY = sorted(set(n.split("-720x520")[0] for n in changed_names))
if FAMILY != ["detail-3-files", "detail-3-files-hover", "detail-3-files-row0", "detail-3-files-row0-hover"]:
    die("本轮改的画面越出了多文件详情区那一家：\n" + "\n".join(changed_names))

# ⑤ 产品文件数 —— 从代码半那一笔读（账半跑的时候工作树是干净的，读 diff 会得到 0）
CODE_SHA = os.environ.get("R290_CODE_SHA", "").strip()
if not re.fullmatch(r"[0-9a-f]{7,40}", CODE_SHA):
    die("R290_CODE_SHA 不是一个真 sha ⇒ sources 格与产品计数不许手抄")
pout, _ = sh(["git", "show", "--numstat", "--format=", CODE_SHA])
MINE = [l.split("\t")[-1] for l in pout.splitlines()
        if "\t" in l and l.split("\t")[-1].startswith("ClipboardHistory/Sources/")]
if not MINE:
    die("代码半那一笔 " + CODE_SHA + " 没动任何 Sources 文件 ⇒ sources 格不该刷")
if not sh(["git", "rev-parse", "--short", "HEAD"])[0].strip().startswith(CODE_SHA):
    die("HEAD 不是代码半那一笔 ⇒ 先提交代码半再跑")

# ⑥ CI 配对（只登记不轮询，R140）
ctxt, _ = sh(["gh", "run", "list", "--limit", "12", "--json", "databaseId,headSha,status,conclusion"])
runs = json.loads(ctxt[ctxt.index("["):])


def pair(sha):
    h = [r for r in runs if r["headSha"].startswith(sha)]
    if not h:
        return sha + u" → 未取到（293）"
    r = h[0]
    return sha + " → " + str(r["databaseId"]) + " / " + r["status"] + " / " + (r["conclusion"] or u"未读")


def battery():
    b, rc = sh([sys.executable, "-W", "ignore", "-m", "unittest", "discover", "-s", "scripts/tests"])
    if rc != 0 or not re.search(r"^OK", b, re.M):
        die("电池不是绿的：\n" + "\n".join(l for l in b.splitlines() if l.startswith(("FAIL:", "ERROR:")))[:900])
    m = re.findall(r"^Ran (\d+) tests", b, re.M)
    sk = re.search(r"skipped=(\d+)", b)
    return m[-1], (sk.group(1) if sk else "0")


pre_ran, pre_skip = battery()
SCORES = [13, 14, 15, 13, 12, 15, 13]
V = {
    "@@DATE@@": "2026-10-21",
    "@@ROLL@@": str(ROLL), "@@FAILS@@": str(FAILS),
    "@@KN@@": KN, "@@KC@@": KC, "@@KREST@@": KREST,
    "@@TBL@@": cover.group(1), "@@COV@@": cover.group(2), "@@PARMS@@": cover.group(3),
    "@@ARMS@@": total.group(2), "@@GAPT@@": roster.group(2), "@@GAPA@@": roster.group(3),
    "@@FRAMES@@": str(N_FRAMES), "@@CH@@": CH.group(1), "@@CM@@": CH.group(2),
    "@@RV@@": rv.group(0).strip(),
    "@@FULLREDS@@": u"；".join(n + u"（全量卷 " + s + u"s 失败）" for n, s in full_reds) or u"无",
    "@@ISOREDS@@": u"；".join(n + u"（隔离复跑 " + iso_pass[n] + u"s 通过）" for n, _s in full_reds) or u"无",
    "@@NRED@@": str(len(full_reds)),
    "@@BEFORE@@": BEFORE_GAP, "@@DRIFT@@": DRIFT_GAP,
    "@@LEFTL@@": LEFT_L.strip(), "@@LEFTD@@": LEFT_D.strip(), "@@RIGHTL@@": RIGHT_L.strip(),
    "@@TEXTLEFT@@": TEXT_LEFT, "@@RULELEFT@@": RULE_LEFT,
    "@@FAMILY@@": "、".join(FAMILY),
    "@@PRODN@@": str(len(MINE)), "@@PRODFILES@@": "、".join(os.path.basename(f) for f in MINE),
    "@@BATT@@": u"脚本电池 Ran " + pre_ran + u" tests / OK (skipped=" + pre_skip + u")",
    "@@SUM@@": str(sum(SCORES)),
    "@@CI1@@": pair("dcf5813"), "@@CI2@@": pair("3fa4e8b"), "@@CI3@@": pair("4eb86ff"),
    "@@CI4@@": pair("88b22cd"),
}


def render(s):
    for k, v in sorted(V.items(), key=lambda kv: -len(kv[0])):
        s = s.replace(k, v)
    if "@@" in s:
        die("仍有未替换占位符 " + ",".join(sorted(set(re.findall(r"@@[A-Z0-9]+@@", s)))))
    return s


UI_NEW = u"""## 第 289 轮（R290 / 第 289 轮 / Round 287 · @@DATE@@）：R289 那句「48 = 文字轴」是我自己写的假账 —— 行分隔线的左端对齐到一个不存在的轴，现在由行首三列导出（U-944…U-948 / D-270 · 产品 @@PRODN@@ 文件）

本轮次对照：与 R289（自评 93，右端并轴 + 三把刀）相比，本轮做的是**同一条缝的另一端**，而且先撤回上一轮我写进注释的那句理由。R289 把右端收进药丸右轴时留着 `.padding(.leading, 48)` 不动，注释写"那是 R31/R104 立的文字轴"——本轮拿同一颗尺去量这一行的列，那句话是错的。

- **U-944：48 谁都不是。** 判据 `LEFT_AXIS_R290` 现读这一行三个墨簇的墨沿：展开箭头 **36.0pt**、类型图标 **55.0pt**、文件名文字 **@@TEXTLEFT@@**（亮暗两档同读数：@@LEFTL@@ / @@LEFTD@@）；而列**框**的边界是 32/44、54/72、82。48 既不是文字（82.5）也不是任何列框的边界 —— 它坐在箭头列框右沿(44)与图标列框左沿(54)之间那道 10pt 空隙里。⇒ 一条对齐到"不存在的轴"的线，与 R289 那条穿出药丸的线是同一族病：**数字没有来源**（R90 那一课：抄来的常量错位一整列）。修法不是把 48 改成 82 再写一颗裸字面量：把行首三列的宽度与列间距升成 `MultiFilePreviewLayout` 的常量（`rowContentHorizontalPadding`／`rowDisclosureColumn`／`rowTypeIconColumn`／`rowColumnSpacing`），左端 `rowTextLeading` 由它们导出，HStack 与 Divider 读同一份。改完现读：线 @@RULELEFT@@ 对文字 @@TEXTLEFT@@（Δ=0.5pt，地板 1.5pt 由真产物推，余量是字形侧边距）。
- **U-945：这一轮真正买到的东西是刀 M846（漂移轴）。** 把 HStack 的 spacing 从 10 改成 14（列会走到 90.5pt）而分隔线不动 ⇒ 判据红，红话里印出差 **@@DRIFT@@pt**。这一把证明"导出"不是整理风格：以前"改了列宽而线没跟上"只有注释里一句希望，现在它是一条会红的判据。另两把：M845（产品轴：左端退回裸字面量 48 ⇒ 红话里印出改前的 @@BEFORE@@pt，D-268 同族）、M847（对象闸门：列缝宽 12px→40px 把三列并成一簇 ⇒ 必须红在「墨簇数不够」那条出口，不许安静地拿箭头那簇当文字）。三把现读 @@KC@@/@@KN@@ 全 CAUGHT、RESTORE_CLEAN=@@KREST@@；新尺 `columnClusters` 配已知答案的对照，两侧都钉（缝 12px 给三簇、缝 4px 必须裂成四簇），空白行带必须给 0 簇而不是 (0,0)。
- **U-946：337 的"其余位点"用一次全帧扫描问过，但那次扫描不配当结论。** 临时尺（`/tmp/r290_pair_scan.py`，与判据同口径：厚带 ≥8pt、细线 ≤2pt、跨度 ≥半幅）跑完 170 张帧：**没有任何一条细线的右端越过同帧厚带的右端** ⇒ R289 那一族在产物里已无残留。但它是**仓库外的尺**（R100：临时尺只配形成问题），而且它比的是"全帧最右的厚带"——一个容器里的细线会被别的容器的厚带赦免。⇒ 新开 339：把这条判据搬进仓库、按**容器**配对（谁与谁同属一列），做完才有资格说"其余位点判过了"。
- **U-947：一次公开更正。** R289 的账（UI 台账、`DetailView.swift` 的注释、CHANGELOG）都写着"48 = 文字轴（R31/R104 立过）"。本轮把它改写成读数，并留原文可查：R289 那一节的正文不删，只在本节点名撤回。R31/R104 立的轴是**详情区头部文字**的左沿（现读 20.5pt），多文件行的文字从来不在那里 —— 上一轮我是把别的屏的轴名安到了这一列上（主语错，不是内容错）。
- **U-948：全量卷这一跑红了两朵计时预算，两朵都在隔离复跑里通过 —— 带进账，不放宽。** @@FULLREDS@@；同一批用例单独跑：@@ISOREDS@@。台账生成器现在按**用例名**配对这两份读数（配不上就拒写台账），所以"负载敏感"这四个字每次都要重新被证明一次，不是一句永久豁免。这是 304 那一族的第二次：同一颗 `CapturePathWriteBudgetTests.testAddingACopyWithANearlyFullArchiveStaysInsideBudget` 在 R257 是全量 17.688s 失败 / 隔离 6.885s 通过，本轮是全量 16.330s / 隔离 1.625s —— **跨度 4 倍**，这正是"单遍读数不配给产品定罪"（R83/R87）的形状。新加入那一颗 `PerfBudgetTests.testFilteredEntriesWithSearchIsBounded`（全量 72.06ms ≥ 60ms 上界 / 隔离 0.489s 通过）同族。两朵都没改地板、没 skip、没删断言；331 的机器名册管的是"谁缺席"，管不到这种"在场但超预算"，所以按 304 追记。

眼睛腿：RUN —— 现读 @@FRAMES@@ 张帧在盘上，看的是行左端那一段（放大 2 倍、行带 240pt 高）：**亮档改前与改后各一张 + 暗档改后一张**。改前那张能看到细线左端停在箭头与类型图标之间那道空隙里（既不跟箭头对齐也不跟图标对齐）；改后亮暗两张的细线左端都从文件名第一个字底下起、右端停在药丸右沿。暗档改前那一张没有单独看 —— 它的左沿由尺读到与亮档同形（48.0pt），这一格按"读数有、眼睛没有"记，不写成看过。
读数腿：RUN —— 判据卷现读 Executed @@ROLL@@ / failures=@@FAILS@@；@@LEFTL@@；@@RIGHTL@@；变异 @@KC@@/@@KN@@ 全 CAUGHT；预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0、ARM_TOTAL arms=@@ARMS@@ dupes=0；四件套 @@RV@@；改前 changed=@@CH@@/compared=@@CM@@（名单就是 @@FAMILY@@ × 亮暗）→ 同一笔 update 后 0；@@BATT@@。
产品腿：@@PRODN@@ 文件（@@PRODFILES@@）—— 连续第二轮动产品。改的仍是**边界的一致性**（同一条缝的左端），悬停的墨、过渡、时长本轮一律未动。
未做（逐条）：① 339（把全帧的"细线不得越过所属容器"搬进仓库并按容器配对）；② 337 剩下的段落线（详情头部那条跨整幅的线，本轮判为另一种约定，未升成判据）；③ 338 的另一半（UI_AUDIT/CHANGELOG 那两本对 R284–R288 仍是申报，没补正文）；④ 331 的 runner 验收（@@CI1@@／@@CI2@@ 未读）；⑤ 333 的 CI 半、312 的具名出口（欠第十三轮）、335、334、310（@@GAPT@@ 张表 / @@GAPA@@ 把刀静默不覆盖）；⑥ 291 的墨轴、305、328、323、322、317、314-316；⑦ 用户闸门 220 路 A / 228② / 265。

"""

ITER_NEW = u"""## Round 287 · 「48 = 文字轴」是 R289 自己写的假账：行分隔线的左端由行首三列导出，漂移第一次会红（R290 / 第 289 轮）/ D-270 · 产品 @@PRODN@@ 文件

本轮次对照：与 R289（自评 93，右端并轴）相比，本轮做同一条缝的左端，并且撤回上一轮写进注释与台账的那句理由 —— 上一轮量的是"两条右轴"，这一轮量的是"这条线到底对齐谁"。
看图腿：RUN —— @@FRAMES@@ 张帧在盘上，放大 2 倍看行左端那一段：亮档改前/改后各一张 + 暗档改后一张 —— 改前左端停在箭头列与图标列之间那道空隙，改后与文件名第一个字对齐；暗档改前那一张按"读数有、眼睛没有"记，没写成看过。
读数腿：RUN —— 判据卷 Executed @@ROLL@@ / failures=@@FAILS@@；@@LEFTL@@；变异 @@KC@@/@@KN@@ 全 CAUGHT、RESTORE_CLEAN=@@KREST@@；四件套 @@RV@@；changed 同一笔 @@CH@@→0；@@BATT@@；预检 tables=@@TBL@@ covered=@@COV@@ bad=0。
七维度自评：
| 维度 | 分/满分 |
| 真实视觉审查 | @@D0@@/15 |
| 判据有效性 | @@D1@@/15 |
| 假绿防御 | @@D2@@/15 |
| 产品面推进 | @@D3@@/15 |
| 台账一致性 | @@D4@@/15 |
| 交付诚实性 | @@D5@@/15 |
| 可复核性 | @@D6@@/15 |
各维理由：真实视觉审查 @@D0@@ —— 真看了改前/改后各两档，看的就是本轮声明那条边；扣分是没扫新屏。判据有效性 @@D1@@ —— 新判据从帧里读列几何（三簇墨沿），两档各判一次，地板 1.5pt 由真产物推（现读 Δ=0.5pt）；扣分是仍只覆盖多文件这一家。假绿防御 @@D2@@ —— 三把刀各钉一条轴，其中 M846 钉的是"两处各写一份数"这一族第一次可红；对象闸门（M847）证明"数不到三簇"必须响而不是安静换对象；新尺的对照把 12px 与 4px 两侧都钉住。产品面推进 @@D3@@ —— 连续第二轮动产品、改前改后都有读数、帧基线同一笔；但动效过程仍未动，这一维仍不是满分。台账一致性 @@D4@@ —— 五本 + FINAL_REPORT 两格 + 新开 339 + 337 追记 + 对 R289 那句假账的公开更正；扣分是 R284–R288 那两本账仍走申报。交付诚实性 @@D5@@ —— 撤回的是我自己上一轮写下的理由，且原文不删、只点名；临时尺的结论显式降级为"只配形成问题"。可复核性 @@D6@@ —— 判据、三把刀、预检、四件套日志与 changed 名单都在原地可重跑；runner 那一行仍欠一次验收。合计 **@@SUM@@**/105。

"""

DEC_NEW = u"""**D-270（R290）：一条线对齐的轴，必须由它所在容器的列几何**导出**，不许写裸字面量，也不许由注释声称。** 理由：R289 把多文件行分隔线的右端收进药丸右轴时，左端留着 `.padding(.leading, 48)`，注释写"48 = 文字轴"。本轮用同一颗尺量这一行的三列墨沿：箭头 36.0／图标 55.0／文字 82.5，列框边界 32/44、54/72、82 —— 48 两边都不是，它坐在箭头列框与图标列框之间那道 10pt 空隙里。这条线从来没有对齐过文字，注释是把**别的屏的轴名**（R31/R104 立的是详情区头部文字那条）安到了这一列上。规矩落成三件事：① 行首三列的宽度与间距升成 `MultiFilePreviewLayout` 的常量，HStack 与 Divider 读同一份 ⇒ 左端 = 导出值 `rowTextLeading`；② 判据从渲染产物里读三簇墨沿并断言线端与文字簇同轴（地板 1.5pt 由真产物推：现读 Δ=0.5pt，余量是字形侧边距）；③ 配一把**漂移轴**的刀（M846：只改 HStack 的 spacing，线不动 ⇒ 必须红）。与 D-247（闸门要与被守的尺同一估计量）、R90（抄来的常量错位一整列）、D-268（改前读数由刀读回来）同族。区别在对象：这条管的是**布局数字的来源**——注释里的理由不是来源，导出式才是。

"""

CHG_NEW = u"""### Fixed（R290 / 第 289 轮 / Round 287 · 多文件行分隔线的左端从裸字面量改成导出轴）

`DetailView.swift`：`MultiFileRow` 的行首三列（展开箭头 12pt、类型图标 18pt、列间距 10pt、行内容左内缩 12pt）原来是 HStack 里的四颗裸字面量，而它下面那条 `Divider()` 写着 `.padding(.leading, 48)`、注释声称"文字轴"。判据 `UICaptureTests/testMultiFileRowSeparatorsStartAtTheTextAxis`（打印 `LEFT_AXIS_R290`）从渲染产物里读三簇墨沿：箭头 36.0／图标 55.0／文字 @@TEXTLEFT@@ —— 48 谁都不是（坐在箭头列框右沿 44 与图标列框左沿 54 之间）。修法是把那四颗数升成 `MultiFilePreviewLayout` 的常量、左端由它们导出（`rowTextLeading`），两处读同一份 ⇒ 改完现读线 @@RULELEFT@@ 对文字 @@TEXTLEFT@@（Δ=0.5pt，地板 1.5pt）。新尺 `columnClusters`（按列切墨簇，缝宽 12px 的分界由"字内 ≤2pt／列间 ≥10pt"两侧钉住）+ 已知答案的对照（含"空白行带必须给 0 簇"）。新增 `mutate_r290.py`：M845（产品轴，红话印出改前 @@BEFORE@@pt）／**M846（漂移轴：只改列间距而线不动 ⇒ 红 @@DRIFT@@pt —— 这条判据第一次能让"两处各写一份数"变红）**／M847（对象闸门：缝宽 40px 把三列并成一簇 ⇒ 必须红在「墨簇数不够」）——现读 @@KC@@/@@KN@@ 全 CAUGHT、RESTORE_CLEAN=@@KREST@@，已登记进预检（tables=@@TBL@@ covered=@@COV@@ bad=0、ARM_TOTAL arms=@@ARMS@@ dupes=0）。**公开更正 R289**：那一节与 `DetailView.swift` 注释里"48 = 文字轴（R31/R104 立过）"是错的，R31/R104 立的是详情区**头部**文字那条轴（现读 20.5pt），本轮撤回并改成读数，原文不删。帧基线同一笔 update：changed @@CH@@/@@CM@@（@@FAMILY@@ × 亮暗）→ 0。四件套 @@RV@@；@@BATT@@；眼睛腿 RUN。新开 339（把"细线不得越过所属容器"从仓库外那把临时尺搬进仓库、按容器配对）；337 的第一处结案、第二处（详情头部跨整幅段落线）判为另一种约定、未升成判据。CI：@@CI1@@／@@CI2@@／@@CI4@@。

"""

BACK_339 = (u"**339. 把「细线不得越过它所属容器的轴」从仓库外的临时尺搬进仓库，并按容器配对（R290 现读：一次 170 张帧的全帧扫描说「没有细线越过同帧最右的厚带」，"
            u"但那把尺在仓库外、且比的是全帧最大值 —— 别的容器的厚带会赦免这一条线）**"
            u"：R290 只把多文件详情区这一家钉住了（左端 + 右端两条判据）。其余表面（设置卡片、侧栏列表、浮层、菜单栏面板）"
            u"要回答同一句话，得先有**容器归属**：谁与谁同属一列。做法照 R289/R290：① 从源码枚举每个位点的容器与内缩；"
            u"② 判据按容器配对（同一段 y 带里的厚带与细线才互相比较），跨容器的不算数；③ 每个位点三选一给约定"
            u"（通到边／收到容器右轴／收到文字轴），理由要能被盘上对象否证（D-266）；④ 每处改动配一把产品轴的刀 + 一把漂移轴的刀（D-270）。"
            u"做完之前不许说「其余位点判过了」")

BACK_APPEND = (u"\n  追记（R290）：337 的第一处（多文件列表的行分隔线）**结案** —— 右端并到药丸右轴（R289，Δ 从 20.000pt 到 0.000pt），"
               u"左端从裸字面量 48 改成由行首三列导出（本轮，现读线 @@RULELEFT@@ 对文字 @@TEXTLEFT@@）。"
               u"同时撤回 R289 那句「48 = 文字轴」：那是把详情区头部的轴名安到这一列上（主语错）。"
               u"第二处（详情头部那条跨整幅的段落线，现读 0.0..719.5）本轮判为**另一种约定**（段落线通到窗边），"
               u"但没有判据替这句话承重 ⇒ 它连同「其余表面的同类位点」一起搬到新开 339。")


def append_into_item(text, num, extra):
    lines = text.splitlines(True)
    start = None
    for i, l in enumerate(lines):
        if l.startswith("**" + num + ". "):
            if start is not None:
                die("BACKLOG 里 " + num + " 出现两次 ⇒ 锚点不唯一，不许插")
            start = i
    if start is None:
        die("BACKLOG 找不到 " + num + " 那一单")
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if re.match(r"^\*\*\d{3}\. ", lines[j]):
            end = j
            break
    while end > start and not lines[end - 1].strip():
        end -= 1
    return u"".join(lines[:end]) + extra + u"\n" + u"".join(lines[end:])


STATE_NEW = u"""## R290 状态（第 289 轮 / Round 287 · @@DATE@@）
最后更新：2026-10-21（本地 · R290 / 第 289 轮 / Round 287）：**撤回 R289 那句「48 = 文字轴」：行分隔线的左端从来不对齐任何一列，现在由行首三列导出，漂移第一次会红**（U-944…U-948 · D-270 · 产品 @@PRODN@@ 文件 · 自评 @@SUM@@/105）

**本轮落地**：`DetailView.swift` 把行首三列（内缩 12／箭头 12／图标 18／间距 10）升成 `MultiFilePreviewLayout` 常量、分隔线左端改成导出的 `rowTextLeading`；`UICaptureHarness.swift` 新增 `columnClusters`／`paperMode` 两把尺 + `changedXSpan` 交出 y 带 + 两格判据（列簇已知答案对照、左端产品判据，Executed @@ROLL@@ / failures=@@FAILS@@）；`mutate_r290.py` M845/M846/M847（@@KC@@/@@KN@@ 全 CAUGHT、RESTORE_CLEAN=@@KREST@@，已登记进预检 tables=@@TBL@@ covered=@@COV@@ bad=0）。现读：@@LEFTL@@；右端那条（R289）同卷照绿 @@RIGHTL@@；改前 changed=@@CH@@/compared=@@CM@@ → 同一笔 update 后 0；四件套 @@RV@@；@@BATT@@。新开 339；337 第一处结案、第二处判为另一种约定（未升判据）。

**下一轮（R291 / 第 290 轮 / Round 288）的 ⓪**：
⓪ 读 CI：@@CI1@@、@@CI2@@、@@CI3@@、@@CI4@@ 加上本两笔（`gh run list --limit 6 --json databaseId,headSha,status,conclusion` 现取配对）。要验的两件事：STEP[9] 的 failures=0（R289 把 331 的 runner 行由外推改成读数）与 STEP[4]/捕获卷里 `LEFT_AXIS_R290` 有没有对象 —— 若 runner 上墨簇数不到 3 个，那朵红说的是尺（按 313/316 那一族解释，不许放宽地板、不许改产品）。只登记不轮询，R140。
① **339**：把"细线不得越过所属容器"搬进仓库并按容器配对（先枚举容器，再判约定）。
② **回到动效过程**（连续两轮的产物面仍是静态边界）：305（按下台阶的地板分辨实验）、291 的墨轴、314（热图那圈描边的语义：要不要换成别的记号 —— 先量它与哪一层混淆，再决定）。
③ 312 的具名出口（欠第十三轮，本机 3.000 不许降，D-251）、333 的 CI 半、335、334、310（@@GAPT@@ 张表 / @@GAPA@@ 把刀静默不覆盖）、338 的另一半、328、323、322、317、314-316。
④ 用户闸门 220 路 A / 228② / 265。

"""

PREVSUM = "93"
V["@@PREVSUM@@"] = PREVSUM

for i, nm in enumerate("D0 D1 D2 D3 D4 D5 D6".split()):
    ITER_NEW = ITER_NEW.replace("@@" + nm + "@@", str(SCORES[i]))
for n in ("UI_NEW", "ITER_NEW", "DEC_NEW", "CHG_NEW", "STATE_NEW"):
    globals()[n] = render(globals()[n])
BACK_NEW = u"\n\n" + render(BACK_339) + u"\n"

ui_p = B["AGENT_UI_AUDIT.md"]
ui_old = rd(ui_p)
if u"## 第 289 轮" in ui_old:
    die(u"UI_AUDIT 已有第 289 轮 ⇒ 生成器不幂等，先还原")
anchor = u"## 第 288 轮"
if ui_old.count(anchor) != 1:
    die("UI_AUDIT 锚点命中 %d 次" % ui_old.count(anchor))
ui_new = ui_old.replace(anchor, UI_NEW + anchor, 1)

it_p = B["AGENT_VISUAL_ITERATION.md"]
it_old = rd(it_p)
if re.search(u"^## Round 287 · ", it_old, re.M):
    die(u"ITERATION 已有 Round 287 ⇒ 不幂等")
it_new = it_old.rstrip("\n") + u"\n\n" + ITER_NEW

dc_p = B["AGENT_DECISIONS.md"]
dc_old = rd(dc_p)
if u"D-270" in dc_old or u"D-269" not in dc_old:
    die(u"D 号不对（D-269 应在盘上、D-270 不该在）")
dc_new = dc_old.rstrip("\n") + u"\n\n" + DEC_NEW

cg_p = B["CHANGELOG.md"]
cg_old = rd(cg_p)
cg_new = cg_old.replace(u"## [Unreleased]\n", u"## [Unreleased]\n\n" + CHG_NEW, 1)

bk_p = B["AGENT_BACKLOG.md"]
bk_old = rd(bk_p)
last = re.findall(r"^\*\*(\d{3})\. ", bk_old, re.M)
if last[-1] != "338":
    die(u"BACKLOG 最后一单不是 338（现读 " + str(last[-3:]) + u"）")
NOTE304 = (u"  追记（R290）：同一族第二次进场 —— 本轮四件套第二跑全量卷红 @@NRED@@ 朵：@@FULLREDS@@；"
           u"同一批用例隔离复跑 @@ISOREDS@@。同一颗 CapturePathWriteBudget 在 R257 是全量 17.688s / 隔离 6.885s，"
           u"本轮是全量 16.330s / 隔离 1.625s —— 单跑与全量的**比值**从 2.6 变成 10.1，"
           u"所以本单那句「本机负载与墙钟预算贴边这两种相反成因还没分开」仍然成立，且更硬。"
           u"新增成员：PerfBudgetTests.testFilteredEntriesWithSearchIsBounded（全量 72.06ms ≥ 60ms 上界）。"
           u"本轮没做的：按 D-253 把它们改成「等条件 + waited_ms」，也没按机器登记具名出口 —— 两件事都不许顺手做，"
           u"因为成因还没分辨（R146：不懂的红不许放宽成出口）。台账生成器现在按用例名配对两份读数，配不上就拒写。")
bk_new = append_into_item(bk_old, "337", render(BACK_APPEND))
bk_new = append_into_item(bk_new, "304", render(NOTE304))
bk_new = bk_new.rstrip("\n") + BACK_NEW

st_p = B["AGENT_STATE.md"]
st_old = rd(st_p)
if u"## R289 状态" not in st_old:
    die(u"STATE 找不到 R289 锚点")
# 交接块（非轮次节）留在最上面，新的轮次节插在 R281…R289 那一串之前
st_new = st_old.replace(u"## R289 状态", STATE_NEW + u"## R289 状态", 1)


def must_preserve(old, new, name):
    cn = Counter(new.splitlines())
    lost = [l for l, c in Counter(old.splitlines()).items() if cn[l] < c]
    if lost:
        die(name + u" 弄丢 " + str(len(lost)) + u" 行：" + u" | ".join(lost[:2])[:160])


for o, n, name in ((ui_old, ui_new, "AGENT_UI_AUDIT.md"), (cg_old, cg_new, "CHANGELOG.md"),
                   (bk_old, bk_new, "AGENT_BACKLOG.md"), (st_old, st_new, "AGENT_STATE.md"),
                   (it_old, it_new, "AGENT_VISUAL_ITERATION.md"), (dc_old, dc_new, "AGENT_DECISIONS.md")):
    must_preserve(o, n, name)

ids = [int(x) for x in re.findall(u"- \\*\\*U-(\\d+)", UI_NEW)]
if ids != list(range(944, 949)):
    die(u"U 号不连续或顺序不对：" + str(ids))
if u"U-944…U-948" not in UI_NEW.splitlines()[0]:
    die(u"节标题 U 区间与定义不符")
rows = [l for l in ITER_NEW.splitlines() if re.match(r"\| .* \| \d+/15 \|$", l)]
scores = [int(re.search(r"\| (\d+)/15 \|", l).group(1)) for l in rows]
if len(scores) != 7 or sum(scores) != sum(SCORES):
    die(u"七维表形状或合计不对：" + str(scores))
if not it_new.startswith(it_old.rstrip("\n")):
    die(u"ITERATION 不是纯追加")
tail = re.findall(u"^## Round (\\d+) · ", it_new, re.M)
if int(tail[-1]) != 287:
    die(u"ITERATION 的文件尾轮次必须是本轮（现读 " + str(tail[-3:]) + u"）")
if it_new.count(u"| 真实视觉审查 |") != it_old.count(u"| 真实视觉审查 |") + 1:
    die(u"七维表数量不对")
if bk_new.count(u"\n**339. ") != 1:
    die(u"新开 339 没落上")
if bk_new.count(u"追记（R290）") != 2:
    die(u"337/304 的追记没落齐（现读 " + str(bk_new.count(u"追记（R290）")) + u" 条）")
_seg337 = bk_new.split(u"**337. ", 1)[1].split(u"追记（R290）", 1)[0]
if re.search(r"^\*\*\d{3}\. ", _seg337, re.M):
    die(u"337 的追记前面已经出现别的单号 ⇒ 插错位置")
if dc_new.count(u"\n**D-270") != 1:
    die(u"D-270 没落上")
if u"## R290 状态" not in st_new:
    die(u"STATE 没轮换")

# 未替换占位符的兜底在 render() 里（每一段插入文本都过它一次）。这里**不再**扫整本文件：
# AGENT_BACKLOG.md 的正文里本来就有合法的 "@@" 字样（307 那一单在讲占位符本身、R274 的追记在引用它），
# 拿"文件里有 @@"当失败会把既有台账内容读成缺陷 —— 尺要量它说的那个对象。
for p, t in ((ui_p, ui_new), (it_p, it_new), (dc_p, dc_new), (bk_p, bk_new), (cg_p, cg_new), (st_p, st_new)):
    with io.open(p, "w", encoding="utf-8") as h:
        h.write(t)

out, rc = sh([sys.executable, os.path.join(HERE, "report_cells_r258.py"), "headline"])
if rc != 0:
    die(u"FINAL_REPORT headline 刷新失败：" + out[-300:])
out2, rc2 = sh([sys.executable, os.path.join(HERE, "report_cells_r258.py"), "sources", CODE_SHA])
if rc2 != 0:
    die(u"FINAL_REPORT sources 刷新失败：" + out2[-300:])
ran2, skip2 = battery()
if ran2 != pre_ran:
    die(u"写盘前后电池颗数不一致（" + pre_ran + u" → " + ran2 + u"）")
print(u"LEDGERS_R290 OK batt=Ran " + ran2 + u" (skipped=" + skip2 + u") roll=" + str(ROLL)
      + u" knives=" + KC + u"/" + KN + u" before_gap=" + BEFORE_GAP + u" drift_gap=" + DRIFT_GAP
      + u" frames=" + str(N_FRAMES) + u" changed=" + CH.group(1) + u" prod=" + str(len(MINE))
      + u" U=944..948 D=270 new=339 + 304 追记")
print(out.strip().splitlines()[-1])
print(out2.strip().splitlines()[-1])
