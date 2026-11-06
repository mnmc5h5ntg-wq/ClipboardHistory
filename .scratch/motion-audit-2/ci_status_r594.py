# -*- coding: utf-8 -*-
"""R594 的 ⓪ 取数：把 R593 那两跑的**全部**失败步骤逐条取出来，并判 R593 留下的五条预测。

两跑配对（现读，不预测）：
  · `42227982898 ↔ c08d432`（R593 主笔）
  · `42229089665 ↔ 22f1270`（R593 补记笔）

顺序与规矩（照 `read-own-ci-run` 那一技能，也照 R593 自己交的账）：
  ① 先成对拿 run↔sha，再列**全部**失败步骤（不截断、不只盯我新加那一步）；
  ② 取正文之前先测"按步骤名过滤这把尺这次灵不灵"（`UNKNOWN STEP` 就改走 emit 通道）；
  ③ 预测由 `PREDICTIONS_R594` 里那五条 lambda **真判**（它们已过 `prediction_block_guard`），
     通道不在就具名 `CI_CHANNEL_ABSENT` ⇒ 既不判中也不判不中（R590/R592 那一族）。
"""
from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys

TMP = "/tmp/r594"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAIN_RUN = "42227982898"
MAIN_SHA = "c08d432"
BUJI_RUN = "42229089665"
BUJI_SHA = "22f1270"

# 基准一律模块级定义（668 那一族：只写在 main() 局部 ⇒ 下一轮一调用就 NameError）。
# 出处逐字：STATE `## R593 状态` 主节 ⓪·1（run 42210166309 那一跑的 STEP[16] 红名 + STEP[9] 汇总行）。
KNOWN_RUNNER_REDS = (
    u"testActionableInkStaysAboveTheLegibilityFloor",
    u"testCaptionTextStaysOnTheSecondaryTier",
    u"testDetailAreaHasASingleLeftAxis",
    u"testDetailStatusBarShowsTheRealSourceAppIconOnlyWhenAttributed",
    u"testQuickPickKeyboardHintClearsTheContrastFloor",
    u"testDetailEmptyToContentCrossfadeIsMeasuredOrDeclaredBlind",
    u"testEmptyStateStillFadesWhenMotionIsReduced",
)
R593_RUNNER_RAN = 932      # R593 主笔那一跑的 STEP[9] 现读（本轮判"新增 python 格有没有被数到"的基准）
R594_LOCAL_RAN = 950       # R593 本地电池三趟都是 950；R594 新增 18+ 格 ⇒ runner 那一格要比 932 大

ANSI = re.compile(u"\x1b\\[[0-9;]*m")
TS = re.compile(u"^.*?\\d{2}:\\d{2}:\\d{2}\\.\\d+Z ")
CASE_FAILED = re.compile(u"Test Case '-\\[[^\\]]*? (\\w+?)\\]' failed")

STEP_CONTENT_GATE = u"Built bundle content gate (D-029 stubs, BACKLOG 620 second half)"
STEP_RELEASE_TESTS = u"Release script tests"
STEP_SWIFT_TESTS = u"Swift tests (executed-count gate)"
STEP_PROBE_FLOOR = u"On-screen probe coverage floor"


def sh(args, timeout=900):
    proc = subprocess.Popen(args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            universal_newlines=True)
    out, _ = proc.communicate(timeout=timeout)
    return out or u""


def run_status(run):
    raw = sh([u"gh", u"run", u"view", run, u"--json", u"status,conclusion,headSha"])
    try:
        d = json.loads(raw)[0] if isinstance(json.loads(raw), list) else json.loads(raw)
    except ValueError:
        return u"读不到（gh 返回不是 JSON）"
    return u"%s/%s sha=%s" % (d.get(u"status") or u"-", d.get(u"conclusion") or u"（未到数）",
                              (d.get(u"headSha") or u"")[0:7])


def jobs(run):
    """步骤清单走 `--json jobs` 再在 python 里格式化 —— jq 那一层每改一次就要重学一次方言，
    而这一张表是本轮第⓪条的第一证人（R592 那一跑就是因为 jq 写错读到空 job ⇒ 日志全空）。"""
    raw = sh([u"gh", u"run", u"view", run, u"--json", u"jobs"])
    try:
        return json.loads(raw).get(u"jobs", []) if isinstance(json.loads(raw), dict) \
            else json.loads(raw)
    except ValueError:
        return []


def steps_table(run):
    out = []
    for job in jobs(run):
        out.append(u"  JOB %s ⇒ %s" % (job.get(u"name"), job.get(u"conclusion") or u"-"))
        for st in job.get(u"steps") or []:
            out.append(u"    STEP[%s] %s ⇒ %s" % (st.get(u"number"), st.get(u"name"),
                                                  st.get(u"conclusion") or u"-"))
    return u"\n".join(out)


def step_conclusion(run, step_name):
    for job in jobs(run):
        for st in job.get(u"steps") or []:
            if st.get(u"name") == step_name:
                return st.get(u"conclusion") or u"-"
    return u"step-not-found"


def step_body(log_text, step_name):
    """按步骤名切正文；**先看这把尺这次灵不灵**（UNKNOWN STEP ⇒ 整份日志都归不到步骤名）。"""
    fields = {}
    lines = log_text.split(u"\n")
    for line in lines:
        parts = ANSI.sub(u"", line).split(u"\t")
        if len(parts) >= 3:
            fields[parts[1]] = fields.get(parts[1], 0) + 1
    unknown = fields.get(u"UNKNOWN STEP", 0)
    if unknown and unknown >= max(1, len(lines) // 2):
        return None, u"UNKNOWN-STEP"
    hit = []
    for line in lines:
        parts = ANSI.sub(u"", line).split(u"\t")
        if len(parts) >= 3 and parts[1] == step_name:
            body = TS.sub(u"", parts[-1])
            hit.append(body)
    return hit, (u"named" if hit else u"named-empty")


def red_names(bodies):
    if bodies is None:
        return []
    return sorted(set(n for l in bodies for n in CASE_FAILED.findall(l)))


def judge(claim, bodies, need, fn):
    """四格齐的一条判定：通道在不在先问，再谈中/不中（`all()` 那种恒真空不许当命中）。"""
    if bodies is None:
        return [claim, u"未读到（步骤名不可用 ⇒ 改走 emit 通道）", u"-", u"-"]
    hits = [l for l in bodies if need.search(l)] if need else list(bodies)
    if not hits:
        return [claim, u"未读到（CI_CHANNEL_ABSENT：那一行在这一步的正文里出现 0 次）",
                u"（没取到）", u"0"]
    try:
        verdict = fn(hits)
    except BaseException as exc:                       # noqa: BLE001 —— 判法崩了必须说出来，不能算不中
        return [claim, u"判法崩了：%s：%s" % (type(exc).__name__, exc), hits[0][:120], str(len(hits))]
    return [claim, u"中" if verdict else u"不中", hits[0][:160], str(len(hits))]


def main():
    if not os.path.isdir(TMP):
        os.makedirs(TMP)
    report = {u"run": MAIN_RUN, u"sha": MAIN_SHA, u"补记笔": {}}
    for run, sha, tag in ((MAIN_RUN, MAIN_SHA, u"主笔"), (BUJI_RUN, BUJI_SHA, u"补记笔")):
        report[u"补记笔"][tag] = {u"配对": u"%s ↔ %s" % (run, sha),
                                  u"状态": run_status(run)}
    log = sh([u"gh", u"run", u"view", MAIN_RUN, u"--log"])
    io.open(os.path.join(TMP, u"log_%s.txt" % MAIN_RUN), u"w", encoding=u"utf-8").write(log)
    report[u"逐步骤"] = steps_table(MAIN_RUN)
    bodies = {}
    channel = {}
    for label, name, token in ((u"content_gate", STEP_CONTENT_GATE, u"BUNDLE_CONTENT"),
                               (u"release", STEP_RELEASE_TESTS, u"SKIP_ROSTER 键=|^Ran |PREDICTION_BLOCK"),
                               (u"swift", STEP_SWIFT_TESTS, u"Test Case"),
                               (u"probe_floor", STEP_PROBE_FLOOR, u"PROBE_COVERAGE_SUMMARY")):
        got, how = step_body(log, name)
        raw = [TS.sub(u"", ANSI.sub(u"", l)).split(u"\t")[-1]
               for l in log.split(u"\n") if re.search(token, l)]
        if how != u"named" or not got:
            got, how = (raw, u"emit-channel")      # 步骤名归不了 ⇒ 用判据自己印的串取正文（技能第 3 步）
        bodies[label], channel[label] = got, how
    bodies[u"all_red_names"] = red_names([TS.sub(u"", ANSI.sub(u"", l)).split(u"\t")[-1]
                                          for l in log.split(u"\n")])
    report[u"尺这次灵不灵"] = dict(channel)
    report[u"红名"] = {
        STEP_CONTENT_GATE: red_names(bodies[u"content_gate"]),
        STEP_RELEASE_TESTS: red_names(bodies[u"release"]),
        STEP_SWIFT_TESTS: red_names(bodies[u"swift"]),
        STEP_PROBE_FLOOR: red_names(bodies[u"probe_floor"]),
        u"整份日志去重（步骤名这次归不出来 ⇒ 只能给这一格）": bodies[u"all_red_names"],
    }
    readings = {}
    for token in (u"BUNDLE_CONTENT_GATE_RESULT", u"APP_DELEGATE_STUB", u"SKIP_ROSTER 键=",
                  u"Ran ", u"PROBE_COVERAGE_SUMMARY", u"REPO_ROOT_BUNDLE_RESULT"):
        readings[token] = [TS.sub(u"", ANSI.sub(u"", l)).split(u"\t")[-1]
                           for l in log.split(u"\n") if token in l][:6]
    report[u"读数"] = readings

    lines_content = bodies[u"content_gate"] or []
    lines_release = bodies[u"release"] or []
    lines_swift = bodies[u"swift"] or []
    report[u"预测"] = [
        judge(u"②新硬步骤第一次有读数", lines_content, re.compile(u"BUNDLE_CONTENT_GATE_RESULT"),
              lambda g: any(l.startswith(u"BUNDLE_CONTENT_GATE_RESULT=ok") for l in g)
              and any(u"APP_DELEGATE_STUB=absent" in l for l in g)),
        judge(u"③SKIP_ROSTER 读数行必须在 runner 上出现", lines_release, re.compile(u"SKIP_ROSTER 键="),
              lambda g: any(u"内层判=" in l for l in g)),
        judge(u"④STEP[16] 红名集合不超出那 7 条", lines_swift, re.compile(u"Test Case"),
              lambda g: bool(g) and all(any(n in l for n in KNOWN_RUNNER_REDS) for l in g)),
        judge(u"⑤STEP[19] 那一朵要么还在要么消失", bodies[u"probe_floor"] or [],
              re.compile(u"PROBE_COVERAGE_SUMMARY"),
              lambda g: any(u"PROBE_COVERAGE_SUMMARY" in l for l in g)),
        judge(u"⑥电池汇总 Ran 比 R593 那一跑的 %d 多" % R593_RUNNER_RAN, lines_release,
              re.compile(u"^Ran \\d"),
              lambda g: max([int(m.group(1)) for l in g
                             for m in [re.match(u"Ran (\\d+)", l)] if m] or [-1]) > R593_RUNNER_RAN),
    ]
    io.open(os.path.join(TMP, u"ci_readings.json"), u"w", encoding=u"utf-8").write(
        json.dumps(report, ensure_ascii=False, indent=1))
    for k in (u"配对", ):
        pass
    for tag, d in report[u"补记笔"].items():
        print(u"%s %s ⇒ %s" % (tag, d[u"配对"], d[u"状态"]), flush=True)
    print(u"尺这次灵不灵=%s" % report[u"尺这次灵不灵"], flush=True)
    print(report[u"逐步骤"], flush=True)
    for step, names in report[u"红名"].items():
        print(u"红名 %s（%d 行正文）：%s" % (step, len(names), u",".join(names) or u"（没有 Test Case failed 行）"),
              flush=True)
    for token, rows in readings.items():
        print(u"读数 %-26s：%s" % (token, rows[0] if rows else u"（0 行）"), flush=True)
    for row in report[u"预测"]:
        print(u"预测=%s ⇒ %s〔命中 %s 行〕%s" % (row[0], row[1], row[3], row[2][:110]), flush=True)
    return 0


# R595 的 ⓪ 从这里接：六条预测，每条四格齐（主张 / 判法 / 正文从哪一步取 / 这条通道由哪一步以什么方式印出去），
# 并且**必须**先过 `scripts/prediction_block_guard.py`（那条判法不许在空输入上为真，函数名不许举局部的东西）。
PREDICTIONS_R595 = [
    {u"主张": u"R594 主笔那一跑的 Swift 那一卷里 `COLUMN_EQUALIZE 展开三档` 必须出声，"
              u"且三档的「差」全是 0.0 ⇒ 等分不是本机那台屏幕的形状，runner 那台机器上也一样",
     u"取处": u"步骤名 `Swift tests (executed-count gate)` 的 **--log** 正文里以 `COLUMN_EQUALIZE` 开头的那一行"
              u"（这一步绿的时候正文不在 --log-failed 里 —— R580 那一课）",
     u"通道": u"`FoldGeometryReanchorTests.testColumnsFollowTheCurrentWindowWidthNotTheSpecConstant` "
              u"里 `CaptureReadings.emit` 印的那一行；**取不到就是未读到**，不许读成『过了』",
     u"判法": lambda g: any(u"COLUMN_EQUALIZE" in l and l.count(u"差=0.0") >= 3 for l in g)},
    {u"主张": u"靶 3 那两条新通道 `FOLD_MAINWINDOW_FULLSCREEN`（全屏对产品窗不可达的契约格）与 "
              u"`FOLD_ZOOM_MEMORY`（放大→折叠的记忆界）在 runner 上各出声一次 ⇒ 这两格真的被跑了，"
              u"不是在本机被 skip 掉的那一档",
     u"取处": u"同上那一步的 --log 正文里以这两个 token 开头的行（各一条）",
     u"通道": u"两格各自的 `CaptureReadings.emit`；判法要求**两个都在**，缺一个就不算这条中",
     u"判法": lambda g: (any(u"FOLD_MAINWINDOW_FULLSCREEN" in l for l in g)
                    and any(u"FOLD_ZOOM_MEMORY " in l for l in g))},
    {u"主张": u"STEP[9] 里 `PREDICTION_BLOCK` 那两行必须出现（本轮把它接进了判据卷 ⇒ runner 上应有回声）",
     u"取处": u"步骤名 `Release script tests` 里以 `PREDICTION_BLOCK_RESULT=` 开头的行",
     u"通道": u"python 判据卷的 stdout（unittest 的 -v 行不算通道）",
     u"判法": lambda g: any(l.startswith(u"PREDICTION_BLOCK_RESULT=ok") for l in g)},
    {u"主张": u"STEP[9] 的 `SKIP_ROSTER 键=github-runner` 那一行仍带内层结论（R593 挪 print 之后不许退回去）",
     u"取处": u"步骤名 `Release script tests` 里以 `SKIP_ROSTER 键=` 开头的行",
     u"通道": u"`test_skip_roster` 那格把所有门之前的 print 印到 stdout",
     u"判法": lambda g: any(u"内层判=" in l for l in g)},
    {u"主张": u"电池汇总 `Ran <N>` 比 R593 主笔那一跑的 %d 多（本轮新增 python 格被数到）" % R593_RUNNER_RAN,
     u"取处": u"步骤名 `Release script tests` 里以 `Ran ` 开头的汇总行",
     u"通道": u"内层电池自己的汇总行（不是台账里抄的数）；Swift 那几格不进这一格的分母",
     u"判法": lambda g: max([int(m.group(1)) for l in g
                             for m in [re.match(u"Ran (\\d+)", l)] if m] or [-1]) > R593_RUNNER_RAN},
    {u"主张": u"新硬步骤 `Built bundle content gate` 在 R594 那一跑继续出声（第一次出声之后不许悄悄掉回去）",
     u"取处": u"步骤名 `%s` 的正文" % STEP_CONTENT_GATE,
     u"通道": u"`bundle_content_gate.py` 自己 print 的行；步骤绿时正文在 --log 不在 --log-failed（R580 那一课）",
     u"判法": lambda g: any(u"BUNDLE_CONTENT" in l for l in g)},
]

ROUTES_R595 = {
    u"本轮不许代选的": [u"655 三条出路", u"656/657/658/659/660/661/662/663/664", u"666 三条", u"667 三条",
                        u"668 的仪器（本轮已做掉 ⇒ 待 runner 签收才谈结案）", u"Motion ≥2 帧地板",
                        u"SSH 成因", u"手感签字", u"批次 91.1/92/93 的人工动作"],
}

if __name__ == "__main__":
    sys.exit(main())
