# -*- coding: utf-8 -*-
"""R592 的 ⓪：读 R591 那两跑（`42179047067 ↔ 40cccd4` / `42179425098 ↔ 906a875`）+ 判 `PREDICTIONS_R592`。

四条预测逐字接自 `ci_status_r591.py`，四格齐（主张 / 判法 / 正文从哪一步取 / 这条通道由谁印出去）。
两条读法上的规矩带着走：
  ① `in_progress` ⇒ 未到数，一条都不判（0 字节日志 = 通道还没内容，不是内容里没有）；
  ② 第③条的正文**不在日志里**，在 `jobs[].steps` 的逐步骤结论里 ⇒ 单独喂，不许拿日志行凑。
"""
from __future__ import annotations

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = "/tmp/r592"
if not os.path.isdir(TMP):
    os.mkdir(TMP)

sys.path.insert(0, HERE)
from ci_status_r591 import (sh, status_line, step_conclusions, fetch_log,   # noqa: E402
                            lines_in_step, steps_dump_to_file, fail_names,
                            WIRE_CHANNELS, R591_CHANNELS, PREDICTIONS_R592,
                            selfcheck)
import ci_skipped_causes                                                    # noqa: E402

# R593 的 ⓪ 从这里接：四条各带判法与取处（四格齐）。本轮改的是**产品几何**与**构建落点**，
# 所以预测全部落在"落点真改了没有"与"runner 那三朵红的集合有没有变大"上。
KNOWN_RUNNER_REDS = (
    u"testActionableInkStaysAboveTheLegibilityFloor",
    u"testCaptionTextStaysOnTheSecondaryTier",
    u"testDetailAreaHasASingleLeftAxis",
    u"testDetailStatusBarShowsTheRealSourceAppIconOnlyWhenAttributed",
    u"testQuickPickKeyboardHintClearsTheContrastFloor",
    u"testDetailEmptyToContentCrossfadeIsMeasuredOrDeclaredBlind",
    u"testEmptyStateStillFadesWhenMotionIsReduced",
)

# R591 那一跑 `42179047067` 的 STEP[9] 正文里 `Ran 918` 出现两次（取值时刻 19:01 那一趟，
# 出处 `/tmp/r592/log_42179047067.txt`）⇒ 它是"本轮有没有被数到"的分母，不是抄来的整数。
R591_RUNNER_RAN = 918

PREDICTIONS_R593 = [
    {u"主张": u"`Runtime launch smoke` 正文里 `SMOKE_TARGET=/tmp/时间剪史_bundle/时间剪史.app` ⇒ "
              u"构建落点那一改在 runner 上生效；印不出这一行 = 本笔没落地，不是『CI 又坏了』",
     u"取处": u"步骤名 `Runtime launch smoke (report-only)` 里以 SMOKE_TARGET 开头的行",
     u"判法": lambda g: any(u"_bundle" in l and u"Codex_Project0" not in l for l in g)},
    {u"主张": u"新硬步骤 `Repo root stays bundle-free …` 第一次有读数：`REPO_ROOT_BUNDLE_RESULT=ok` 且 "
              u"`READER_SELFTEST=seen`；若它 `not-run`，结论只能是「构建没落地」，不许读成「仓库根干净」",
     u"取处": u"步骤名 `Repo root stays bundle-free after make bundle (BACKLOG 620)` 的正文",
     u"判法": lambda g: (any(l.startswith(u"REPO_ROOT_BUNDLE_RESULT=ok") for l in g)
                         and any(u"READER_SELFTEST=seen" in l for l in g))},
    {u"主张": u"runner 那三朵红（STEP[15]/[17]/[19]）的红名集合**不超出**本轮记下的那 7 条 ⇒ 本笔没引入新红；"
              u"少掉一条也要写清楚是谁签的，不许顺手当成「修好了」",
     u"取处": u"三个步骤正文里 `Test Case … failed` 的用例名（去重后比对）",
     u"判法": lambda g: all(any(n in l for n in KNOWN_RUNNER_REDS) or u"failed" not in l for l in g)},
    {u"主张": u"`STEP[9]` 的电池汇总 `Ran <N>` 比 R591 那一跑的 `Ran 918` **多** ⇒ 本轮新增的 python 格在 runner 上"
              u"被数到（本机绿不算交付，R589 那条同形规矩）。口径：只加 python 侧那 14 格（11 + 3），"
              u"Swift 侧 10 格不进这一格的分母 ⇒ 拿 24 去对是跨通道对账（R565 那一族）。",
     u"取处": u"步骤名 `Release script tests` 里以 `Ran ` 开头的汇总行",
     u"判法": lambda g: (len([l for l in g if re.search(r"Ran \d+", l)]) >= 1
                         and max(int(re.search(r"Ran (\d+)", l).group(1))
                                 for l in g if re.search(r"Ran \d+", l)) > R591_RUNNER_RAN)},
    {u"主张": u"`STEP[9]` 里 `SKIP_ROSTER 键=github-runner` 那一行的 `名单外` 与 `名册未跳` **两边都不许**出现"
              u"`test_built_bundle_carries_no_app_delegate_stub` —— 本轮把它的对象从仓库根搬进暂存目录，"
              u"而 runner 的电池排在 `make bundle` 之前 ⇒ 照旧 skip、登记照旧命中。"
              u"**若报 `名册未跳=[那一格]`**：说明它在 runner 上开始真跑，正确的动作是删登记，"
              u"不是把登记留着当永久豁免（R565：豁免理由里写了退场不等于退场会发生）。",
     u"取处": u"步骤名 `Release script tests` 里以 `SKIP_ROSTER ` 开头的行",
     u"判法": lambda g: all(u"test_built_bundle_carries_no_app_delegate_stub" not in l
                           for l in g if u"名单外=[" in l or u"名册未跳=[" in l)},
]

ROOT = os.path.dirname(os.path.dirname(HERE))

PAIRS = [("42179047067", "40cccd4", u"R591 主笔：skipped 拆甲乙 + 守卫接线 + 值槽划界"),
         ("42179425098", "906a875", u"R591 补记笔：⓪ 成对号现取现写 + 四扇门复算")]

# 每条预测的取处：(步骤名, 通道前缀)。第③条走 steps 视图，不在这里。
ROUTES = {
    0: (u"Release script tests", (u"SHAPE_GUARD2_EXIT",)),
    1: (u"Release script tests", (u"IDENTICAL_WITNESS_EXIT",)),
    3: (u"Release script tests", (u"CI_CHANNEL_GLUE_SCOPE", u"CI_SKIPPED_CAUSES")),
}


# R593 用得上：五条预测各自的取处（步骤名 + 通道前缀）。判法读的是**正文行**，不是前缀名。
ROUTES_R593 = {
    0: (u"Runtime launch smoke (report-only)", (u"SMOKE_TARGET",)),
    1: (u"Repo root stays bundle-free after make bundle (BACKLOG 620)",
        (u"READER_SELFTEST", u"BUNDLE_STAGED", u"REPO_ROOT_BUNDLE")),
    2: (u"Swift tests (executed-count gate)", (u"Test Case",)),
    3: (u"Release script tests", (u"Ran ",)),
    4: (u"Release script tests", (u"SKIP_ROSTER ",)),
}


def main():
    print(selfcheck())
    report = {}
    for run, sha, note in PAIRS:
        st = status_line(run)
        item = {u"sha": sha, u"备注": note, u"status行": st,
                u"到数": u"是" if u"in_progress" not in st else u"否（status=in_progress ⇒ 未读）"}
        rc, steps, _e = sh([u"python3", u"scripts/ci_read.py", u"steps", run])
        item[u"失败步骤"] = [l.strip() for l in (steps or u"").splitlines() if u"⇒ failure" in l]
        item[u"逐步骤结论"] = step_conclusions(run)
        if item[u"到数"] != u"是":
            report[run] = item
            continue
        log = fetch_log(run, TMP)
        item[u"log_bytes"] = os.path.getsize(log) if os.path.exists(log) else 0
        dump = os.path.join(TMP, "steps_%s.txt" % run)
        if steps_dump_to_file(run, dump):
            rows = ci_skipped_causes.parse_steps_dump(io.open(dump, encoding=u"utf-8").read())
            item[u"skipped清单"] = [[r["index"], r["name"]] for r in rows if r["conclusion"] == u"skipped"]
        else:
            rows, item[u"skipped清单"] = [], u"（取不到 jobs[].steps ⇒ 这一格按未读到处理）"
        if not item[u"log_bytes"]:
            item[u"通道三态"] = u"未读到（`CI_LOG_EMPTY=not-finished`）⇒ 一条不判"
            report[run] = item
            continue
        _h, per, how, lines = lines_in_step(log, u"Release script tests",
                                            WIRE_CHANNELS + R591_CHANNELS)
        item[u"通道计数"] = dict(per)
        item[u"取处"] = how
        item[u"STEP9_红名"] = fail_names(lines)
        preds = []
        for i, spec in enumerate(PREDICTIONS_R592):
            if i == 2:
                plines = [u"%d %s %s" % (r["index"], r["conclusion"], r["name"]) for r in rows]
                ran = bool(rows)
                how2 = u"jobs[].steps 逐步骤结论（%d 行）" % len(rows)
            else:
                needle, prefixes = ROUTES[i]
                _h2, _p2, how2, plines = lines_in_step(log, needle, prefixes)
                ran = any(needle in k and v in (u"success", u"failure")
                          for k, v in item[u"逐步骤结论"].items())
            if not ran:
                preds.append([spec[u"主张"],
                              u"未读到（`CI_STEP_NOT_RUN`：那一步没跑到 ⇒ 不判中/不中）", how2])
                continue
            try:
                ok = spec[u"判法"](plines)
            except Exception as exc:
                ok = u"判法抛了：%s" % exc
            preds.append([spec[u"主张"],
                          (u"中" if ok is True else (u"不中" if ok is False else ok)), how2])
        item[u"预测"] = preds
        report[run] = item

    # 本轮台账节还没写 ⇒ 这一趟只数 skipped 有几朵，成因那一维留给落盘后的第二趟
    gate = []
    for run, item in report.items():
        dump = os.path.join(TMP, "steps_%s.txt" % run)
        if not os.path.exists(dump):
            gate.append([run, u"（没对象：清单缺失 ⇒ 具名不判）"])
            continue
        rows = ci_skipped_causes.parse_steps_dump(io.open(dump, encoding=u"utf-8").read())
        v = ci_skipped_causes.judge_run(rows, u"")   # 本轮台账节还没写 ⇒ 只能数 skipped，成因留给落盘后
        gate.append([run, u"skipped=%d（成因待本轮台账落盘后由 --post-land 复算）" % v["skipped"]])

    out = []
    for run, it in report.items():
        out.append(u"RUN=%s ↔ %s 到数=%s status=%s" % (run, it[u"sha"], it[u"到数"], it[u"status行"]))
        out.append(u"  失败步骤=%s" % (u" | ".join(it.get(u"失败步骤", [])) or u"（没有/未读到）"))
        for nm in (u"Release script tests", u"Frame baseline vs working manifest (fixture-set gate)",
                   u"Surface left-axis ruler (BACKLOG 234, wired in R210; venv interpreter in R218)",
                   u"Swift tests (executed-count gate)", u"Motion coverage floor"):
            out.append(u"  逐步骤结论 %-64s ⇒ %s" % (nm[:64], it[u"逐步骤结论"].get(nm, u"（读不到）")))
        if u"skipped清单" in it:
            out.append(u"  skipped 清单=%s" % (it[u"skipped清单"],))
        if u"通道计数" in it:
            out.append(u"  通道计数=%s" % json.dumps(it[u"通道计数"], ensure_ascii=False))
            out.append(u"  取处=%s" % it[u"取处"])
            out.append(u"  STEP[9] 红名（逐字）=%s" % (it[u"STEP9_红名"],))
        for pv in it.get(u"预测", []):
            out.append(u"  预测=%s ⇒ %s〔%s〕" % (pv[0], pv[1], pv[2]))
    for run, line in gate:
        out.append(u"门（skipped 计数）%s ⇒ %s" % (run, line))
    text = u"\n".join(out)
    io.open(os.path.join(TMP, "ci_status.txt"), u"w", encoding=u"utf-8").write(text + u"\n")
    io.open(os.path.join(TMP, "ci_readings.json"), u"w", encoding=u"utf-8").write(
        json.dumps(report, ensure_ascii=False, indent=1))
    print(text)
    return 0


if __name__ == u"__main__":
    sys.exit(main())
