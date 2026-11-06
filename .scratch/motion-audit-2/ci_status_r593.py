# -*- coding: utf-8 -*-
"""R593 的 ⓪ 取数：把 `42210166309` 那一跑的**全部**失败步骤逐条取出来，并判 R592 留下的五条预测。

与上一轮同一族的两条规矩：
  ① 不许只看自己新加那一步 ⇒ 逐步骤结论 + 每一步的红名都落盘；
  ② **预测的判法不许在空输入上恒真** —— `all(...)` 对空清单是真，那是把"没有读数"读成"判中"。
     所以每条预测都先问"那一行在不在"，不在就整格按未读到处理（`CI_CHANNEL_ABSENT`），不判中/不中。
"""
from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys

TMP = "/tmp/r593"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAIN_RUN = "42210166309"
MAIN_SHA = "03b48b2"
BUJI_RUN = "42211799683"
BUJI_SHA = "5b20a61"

# R594 那一趟要用的两个基准，一律**在这一笔里定义**（从前它们只写在函数体里，
# PREDICTIONS_R594 的 lambda 举到模块级就得到 NameError —— 「印出来的出路做不到」那一族）。
# 出处逐字：STATE `## R593 状态` 主节 ⓪·1（run 42210166309 的 STEP[16] 红名 + 电池汇总行）。
KNOWN_RUNNER_REDS = (
    u"testActionableInkStaysAboveTheLegibilityFloor",
    u"testCaptionTextStaysOnTheSecondaryTier",
    u"testDetailAreaHasASingleLeftAxis",
    u"testDetailStatusBarShowsTheRealSourceAppIconOnlyWhenAttributed",
    u"testQuickPickKeyboardHintClearsTheContrastFloor",
    u"testDetailEmptyToContentCrossfadeIsMeasuredOrDeclaredBlind",
    u"testEmptyStateStillFadesWhenMotionIsReduced",
)
R592_LOCAL_RAN = 932      # 42210166309 STEP[9] 现读 `Ran 932 tests in 170.175s`

ANSI = re.compile(u"\x1b\\[[0-9;]*m")
TS = re.compile(u"^.*?\\d{2}:\\d{2}:\\d{2}\\.\\d+Z ")
CASE_FAILED = re.compile(u"Test Case '-\\[[^\\]]*? (\\w+?)\\]' failed")


def sh(args):
    proc = subprocess.Popen(args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            universal_newlines=True)
    out, _ = proc.communicate(timeout=600)
    return out or u""


def run_status(run):
    return sh([u"gh", u"run", u"view", run, u"--json", u"status,conclusion",
               u"-q", u'(.status // "-") + "/" + (.conclusion // "（conclusion 空 ⇒ 未到数）")']).strip()


def step_body(log_path, step_name):
    out = []
    for line in io.open(log_path, encoding=u"utf-8", errors=u"replace"):
        parts = line.rstrip(u"\n").split(u"\t")
        if len(parts) >= 3 and parts[1] == step_name:
            out.append(TS.sub(u"", ANSI.sub(u"", parts[2])))
    return out


def step_conclusions(run):
    js = sh([u"gh", u"run", u"view", run, u"--json", u"jobs", u"-q",
             # 字段名是 `number`，不是 `index`（这台 gh 上写 `.index` 静默得到 null ⇒
             # 每一步都变成 "null success …"，红名单就数不出来）。
             u'.jobs[].steps[] | [(.number|tostring), (.conclusion // "-"), .name] | join(" ")'])
    rows = []
    for line in js.splitlines():
        m = re.match(u"(\\d+) (\\S+) (.*)", line.strip())
        if m:
            rows.append({u"index": int(m.group(1)), u"conclusion": m.group(2), u"name": m.group(3)})
    return rows


def judge(pred_name, lines, need, fn):
    """先问通道在不在，再谈中/不中。`need` 是"这一格要读到的那一行"的正则。"""
    if not lines:
        return [pred_name, u"未读到（CI_CHANNEL_ABSENT：那一步的正文一行都没取到）", u"（没取到）"]
    hits = [l for l in lines if re.search(need, l)]
    if not hits:
        return [pred_name, u"未读到（CI_CHANNEL_ABSENT：那一行在本步正文里 0 次 ⇒ 不是"
                           u"「没红」，是这一维今天没人印）", u"命中 0 行"]
    try:
        ok = fn(hits)
    except Exception as exc:
        return [pred_name, u"判法抛了：%s" % exc, u"命中 %d 行" % len(hits)]
    return [pred_name, (u"中" if ok is True else (u"不中" if ok is False else ok)), u"命中 %d 行" % len(hits)]


# R594 的 ⓪ 从这里接：五条预测各带四格（主张 / 判法 / 正文从哪一步取 / 这条通道由哪一步印出去）。
# 本轮改的是**产品的不变量另一半** + **四支守卫** + **CI 新硬步骤** ⇒ 预测全部落在"新步步骤有没有出声"
# 与"那一行 SKIP_ROSTER 读数下一次到底印不印得出来"上。
PREDICTIONS_R594 = [
    {u"主张": u"新硬步骤 `Built bundle content gate (D-029 stubs, BACKLOG 620 second half)` 第一次有读数："
              u"`BUNDLE_CONTENT_GATE_RESULT=ok` 且正文里 `APP_DELEGATE_STUB=absent` ⇒ 产物内容那一维在 runner 上出声了",
     u"通道": u"步骤 `Built bundle content gate (D-029 stubs, BACKLOG 620 second half)` 的 stdout：`bundle_content_gate.py` 自己 print 的那两行（`if: always()` ⇒ 上游红也出声；步骤绿时正文只在 --log）",
             u"取处": u"步骤名 `Built bundle content gate (D-029 stubs, BACKLOG 620 second half)` 的正文",
     u"判法": lambda g: (any(l.startswith(u"BUNDLE_CONTENT_GATE_RESULT=ok") for l in g)
                         and any(u"APP_DELEGATE_STUB=absent" in l for l in g))},
    {u"主张": u"`STEP[9]` 里出现 `SKIP_ROSTER 键=github-runner … 内层判=` 那一行（本轮把 print 挪到了所有门之前）"
              u"⇒ 这一维在 runner 上从此有读数。⚠ 反向读法：**还不出现 = print 又被挪回门后面**，"
              u"不是『runner 又坏了』，也不是『这一维没人判是对的』",
     u"通道": u"步骤 `Release script tests` 的 stdout：`test_skip_roster` 把这一行印在**所有会崩的门之前**（R593 修的那一处）",
             u"取处": u"步骤名 `Release script tests` 里以 `SKIP_ROSTER 键=` 开头的行",
     u"判法": lambda g: any(u"内层判=" in l for l in g)},
    {u"主张": u"`STEP[16]` 的红名集合**不超出**本轮记下的那 7 条 ⇒ R592 那朵我自己加的判据红"
              u"（`testARestoredOffRatioWindowIsLiftedOntoTheSpecRatio`）被本轮的夹具前提修掉了",
     u"通道": u"步骤 `Swift tests (executed-count gate)` 的 --log-failed 正文里 `Test Case … failed` 行：由 gh 的日志通道给、不是判据自己印 ⇒ 取不到就是**未读到**，不是「没红」",
             u"取处": u"步骤正文里 `Test Case … failed` 的用例名（去重后比对）",
     u"判法": lambda g: bool(g) and all(any(n in l for n in KNOWN_RUNNER_REDS) for l in g)},
    {u"主张": u"`STEP[19]`（On-screen probe coverage floor）那一朵 `testFrameIntervalsUnderStateChanges` "
              u"**要么还在要么消失**：还在 ⇒ (乙)「runner 采样/负载」这一解释拿到第二个真数；"
              u"消失 ⇒ 与 R591 两跑同形，本轮那朵就是间歇。两种都不许写成『修好了』或『没事』",
     u"通道": u"步骤 `On-screen probe coverage floor` 的 stdout：`PROBE_COVERAGE_SUMMARY` 由判据 print；失败行在 --log-failed",
             u"取处": u"步骤名 `On-screen probe coverage floor` 正文里 `PROBE_COVERAGE_SUMMARY` 那一行 + `FAILED testFrame…` 行",
     u"判法": lambda g: any(u"PROBE_COVERAGE_SUMMARY" in l for l in g)},
    {u"主张": u"`STEP[9]` 的电池汇总 `Ran <N>` 比基准 `Ran 932` 多 ⇒ 本轮新增的 python 格在 runner 上被数到；"
              u"基准的出处=本轮 ⓪ 现读的 R592 主笔那一跑 `42210166309` 的 STEP[9] 汇总行（逐字在 STATE 主节 ⓪·1）；"
              u"口径：只加 python 侧那 18 格（6+5+3+4），Swift 那 3 格不进这一格的分母",
     u"通道": u"步骤 `Release script tests` 的 stdout：内层电池自己的 `Ran <N>` 汇总行（不是台账里抄来的数）",
             u"取处": u"步骤名 `Release script tests` 里以 `Ran ` 开头的汇总行",
     u"判法": lambda g: max([int(m.group(1)) for l in g
                             for m in [re.match(u"Ran (\\d+)", l)] if m] or [-1]) > R592_LOCAL_RAN},
]

ROUTES_R594 = {
    0: (u"Built bundle content gate (D-029 stubs, BACKLOG 620 second half)",
        (u"BUNDLE_CONTENT_GATE_RESULT", u"BUNDLE_TARGET", u"BUNDLE_CONTENT")),
    1: (u"Release script tests", (u"SKIP_ROSTER ",)),
    2: (u"Swift tests (executed-count gate)", (u"Test Case",)),
    3: (u"On-screen probe coverage floor", (u"PROBE_COVERAGE_SUMMARY", u"FAILED")),
    4: (u"Release script tests", (u"Ran ",)),
}

def main():
    log = os.path.join(TMP, u"log_%s.txt" % MAIN_RUN)
    if not os.path.exists(log):
        io.open(log, u"w", encoding=u"utf-8").write(sh([u"gh", u"run", u"view", MAIN_RUN, u"--log"]))
    rows = step_conclusions(MAIN_RUN)
    io.open(os.path.join(TMP, u"steps_%s.txt" % MAIN_RUN), u"w", encoding=u"utf-8").write(
        u"\n".join(u"%d %s %s" % (r[u"index"], r[u"conclusion"], r[u"name"]) for r in rows) + u"\n")

    report = {u"run": MAIN_RUN, u"sha": MAIN_SHA,
              u"status": run_status(MAIN_RUN),
              u"补记笔那一跑": run_status(BUJI_RUN),
              u"逐步骤": [{u"index": r[u"index"], u"conclusion": r[u"conclusion"], u"name": r[u"name"]}
                          for r in rows],
              u"红名": {}, u"预测": [], u"读数": {}}

    for r in rows:
        if r[u"conclusion"] != u"failure":
            continue
        body = step_body(log, r[u"name"])
        reds = sorted(set(CASE_FAILED.findall(u"\n".join(body))))
        report[u"红名"][u"STEP[%d] %s" % (r[u"index"], r[u"name"])] = {u"红用例": reds, u"行数": len(body)}

    battery = step_body(log, u"Release script tests")
    smoke = step_body(log, u"Runtime launch smoke (report-only)")
    rootstep = step_body(log, u"Repo root stays bundle-free after make bundle (BACKLOG 620)")
    swift = step_body(log, u"Swift tests (executed-count gate)")

    report[u"读数"][u"电池汇总"] = [l for l in battery if re.match(u"^(Ran |FAILED|OK)", l)]
    # 只认**读数行**（带 `内层Ran=` 那一串），不认正文里提到这个名字的账行/注释行 ——
    # 第一版就是被台账里 U-957 那一行喂成了"有读数"，那是把引用读成观测（R580 那一族）。
    report[u"读数"][u"SKIP_ROSTER"] = [l for l in battery if re.match(u"^SKIP_ROSTER 键=", l)]
    report[u"读数"][u"SMOKE_TARGET"] = [l for l in smoke if l.startswith(u"SMOKE_TARGET=")]
    report[u"读数"][u"REPO_ROOT"] = [l for l in rootstep if l.startswith(u"REPO_ROOT_BUNDLE=")]
    report[u"读数"][u"READER_SELFTEST"] = [l for l in rootstep if l.startswith(u"READER_SELFTEST=")]
    report[u"读数"][u"RESULT"] = [l for l in rootstep if l.startswith(u"REPO_ROOT_BUNDLE_RESULT=")]

    ran_max = [int(m.group(1)) for l in report[u"读数"][u"电池汇总"] for m in [re.match(u"Ran (\\d+)", l)] if m]
    known = KNOWN_RUNNER_REDS

    report[u"预测"].append(judge(
        u"②SMOKE_TARGET 指向暂存目录", smoke, u"^SMOKE_TARGET=",
        lambda g: any(u"_bundle" in l and u"Codex_Project0" not in l for l in g)))
    report[u"预测"].append(judge(
        u"③新硬步骤第一次有读数", rootstep, u"^REPO_ROOT_BUNDLE_RESULT=",
        lambda g: (any(l.startswith(u"REPO_ROOT_BUNDLE_RESULT=ok") for l in g)
                   and any(u"READER_SELFTEST=seen" in l for l in step_body(log,
                       u"Repo root stays bundle-free after make bundle (BACKLOG 620)")))))
    all_reds = sorted({n for v in report[u"红名"].values() for n in v[u"红用例"]})
    report[u"预测"].append(judge(
        u"④三朵红的集合不超出那 7 条", [n for n in all_reds], u".",
        lambda g: all(any(k in n for k in known) for n in g)))
    report[u"预测"][-1][2] = u"红名去重后 %d 条：%s" % (len(all_reds), u",".join(all_reds))
    report[u"预测"].append(judge(
        u"⑤电池 Ran 比 R591 的 918 多", report[u"读数"][u"电池汇总"], u"^Ran \\d",
        lambda g: max(int(m.group(1)) for l in g for m in [re.match(u"Ran (\\d+)", l)] if m) > 918))
    report[u"预测"].append(judge(
        u"⑥SKIP_ROSTER 读数行两边都不许含那一格", report[u"读数"][u"SKIP_ROSTER"],
        u"SKIP_ROSTER 键=.+ 内层Ran=",
        lambda g: all(u"test_built_bundle_carries_no_app_delegate_stub" not in l for l in g)))

    io.open(os.path.join(TMP, u"ci_readings.json"), u"w", encoding=u"utf-8").write(
        json.dumps(report, ensure_ascii=False, indent=1))
    out = [u"RUN=%s ↔ %s status=%s" % (MAIN_RUN, MAIN_SHA, report[u"status"]),
           u"补记笔 %s ↔ %s status=%s" % (BUJI_RUN, BUJI_SHA, report[u"补记笔那一跑"])]
    for r in rows:
        out.append(u"  STEP[%d] %-70s ⇒ %s" % (r[u"index"], r[u"name"][:70], r[u"conclusion"]))
    for k, v in report[u"红名"].items():
        out.append(u"  红名 %s（正文 %d 行）：%s" % (k, v[u"行数"], u",".join(v[u"红用例"]) or u"（没有 Test Case failed 行）"))
    for key, lines in report[u"读数"].items():
        out.append(u"  读数 %-16s：%s" % (key, (lines[0][:150] if lines else u"（0 行）")))
    for pv in report[u"预测"]:
        out.append(u"  预测=%s ⇒ %s〔%s〕" % (pv[0], pv[1], pv[2]))
    text = u"\n".join(out)
    io.open(os.path.join(TMP, u"ci_status.txt"), u"w", encoding=u"utf-8").write(text + u"\n")
    print(text)
    return 0


if __name__ == u"__main__":
    sys.exit(main())
