# -*- coding: utf-8 -*-
"""R591 的 ⓪：两对现读 + `PREDICTIONS_R591` 由脚本判 + **skipped 的成因清单落到盘上给门去读**。

三件事，顺序不许换：
  ① 成对取 run↔commit 与 status/conclusion；`in_progress` ⇒ **未到数**（0 字节日志 = 通道还没内容，
     不是内容里没有；R590 ⑨·6 那一处就是这么判错的，本轮由 `到数` 的判据直接看 conclusion）。
  ② 到数之后：不只读"没红"，要读**那几条新通道在不在**（`SHAPE_GUARD2_EXIT rc=<数字>`、
     `CI_CHANNEL_GLUE_SCOPE … 粘连计=`、`CI_SKIPPED_CAUSES … 无声=`），并把 `STEP[9]` 的红名逐字列出来
     —— 本轮 ③ 那三条修好了没有，只能由**含本笔的那一跑**说。
  ③ 把 `jobs[].steps` 的逐步骤结论**落成盘上文件**，交给 `scripts/ci_skipped_causes.py --mode run` 判：
     每一个 `skipped` 都要在台账本轮那一节里有成因名字（`第③甲`=被上游红连带 / `第③乙`=跑了但本机没对象）。
     这一步是"把 skipped 从散文变成会红的门"的取数侧 —— 门在脚本里，不在我嘴里。

四条预测的标签与判法逐字接自 `ci_status_r590.py` 的 `PREDICTIONS_R591`（四格齐：主张 / 判法 /
正文从哪一步取 / 这条通道由哪一步以什么方式印出去），本文件只负责把**正文行**喂给判法，
不许目测对拍、也不许在取不到行时用 `True` 顶替（R587 ② 那一格恒真预测的同族）。
"""
from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

TMP = "/tmp/r591"
if not os.path.isdir(TMP):
    os.mkdir(TMP)

from ci_status_r590 import (sh, status_line, step_conclusions, fetch_log, lines_in_step,   # noqa: E402
                            WIRE_CHANNELS, PREDICTIONS_R591)
import ci_skipped_causes                                                                   # noqa: E402

PAIRS = [("42167592176", "abc20af", u"R590 主笔：兜底出声 + 扫描面报数 + 三条对象错位各配一把刀"),
         ("42167882874", "d211062", u"R590 补记笔：⓪ 成对号现取现写 + 落盘后门复算")]

# 本轮新印出来的通道（R591 靶 1+2 的外部证人就是这几条）
R591_CHANNELS = (u"SHAPE_GUARD2_EXIT", u"CI_CHANNEL_GLUE_SCOPE", u"CI_CHANNEL_GLUE_SCRIPT_ONLY",
                 u"CI_CHANNEL_GLUE_READING_PAREN", u"CI_CHANNEL_HYGIENE_RESULT",
                 u"CI_SKIPPED_CAUSES", u"CI_SKIPPED_NOT_JUDGED", u"CI_EVIDENCE_STEP_SKIPPABLE")

# 每条预测的**取处**：步骤名 + 要筛的通道前缀（判法读的是行，不是前缀名 —— R590 ⑨·6 第二处）
# ⚠ 第三格错了会造出**假中**：`WITNESS_SCAN_SCOPE`（R590 靶 1 的扫描面）被我一度映射到 `CI_CHANNEL_GLUE_SCOPE`
#    （R591 靶 2 的名字），两条通道毫无关系；而 ① 那条筛 `FAIL:` 时因为行首带 ANSI，
#    剥色之前 `startswith` 恒假 ⇒ 空集合让"红名少掉三条"变成**空真**。两处都在本文件里修掉了。
ROUTES = {
    0: (u"Release script tests", (u"FAIL:",)),                       # ① STEP[9] 的红名少没少
    1: (u"Release script tests", (u"SHAPE_GUARD_EXIT", u"IDENTICAL_WITNESS_EXIT",
                                  u"SHAPE_GUARD2_EXIT")),            # ② rc 值读不读得到
    2: (u"Release script tests", (u"WITNESS_",)),                    # ③ 靶 1 的扫描面（swift文件=）
    3: (u"Frame baseline vs working manifest", (u"FRAME_BASELINE_SCALE",)),   # ④ 那一步跑到没有
}


def steps_dump_to_file(run, path):
    """把 `jobs[].steps` 的逐步骤结论落成 `index conclusion name` —— 交给门判 skipped 的成因。"""
    rc, out, _e = sh([u"gh", u"run", u"view", run, u"--json", u"jobs", u"--jq",
                      u'.jobs[0].steps | to_entries | .[] | "\\(.key+1) \\(.value.conclusion) \\(.value.name)"'])
    if rc != 0 or not (out or u"").strip():
        return False
    io.open(path, u"w", encoding=u"utf-8").write(out)
    return True


def fail_names(lines):
    return [l for l in lines if l.startswith(u"FAIL:")]


# R592 的 ⓪ 从这里接：四条各带判法与取处（四格齐：主张 / 判法 / 正文从哪一步取 / 这条通道由哪一步以什么方式印出去）。
# 本轮修的是 shell 语义与接线顺序 ⇒ 预测全部落在"那两行第一次印得出来"与"skipped 少掉四步"上；
# ②那一条的**反向读法**要写清：印不出来说明修法没生效，不是"又坏了"。
PREDICTIONS_R592 = [
    {u"主张": u"STEP[9] 里 `SHAPE_GUARD2_EXIT guard=… rc=<数字>` 恰好两行 ⇒ 本轮新接的两支守卫第一次在 runner 上有退出码读数",
     u"取处": u"步骤名 `Release script tests` 里以 SHAPE_GUARD2_EXIT 开头的行",
     u"判法": lambda g: len([l for l in g if re.search(r"rc=\d", l)]) == 2},
    {u"主张": u"STEP[9] 里 `IDENTICAL_WITNESS_EXIT=<数字>` 出现 ⇒ pipefail 那一支修好了（从前工具返回 2 时整步先死，"
              u"这一行从来没印过）；**印不出来=修法没生效**，不是『又坏了』",
     u"取处": u"步骤名 `Release script tests` 里以 IDENTICAL_WITNESS_EXIT 开头的行",
     u"判法": lambda g: len([l for l in g if re.search(r"=\d", l)]) >= 1},
    {u"主张": u"skipped 清单从 5 步缩到 1 步（只剩 `Info.plist gate`，它是硬门、故意不带 `if: always()`）⇒ "
              u"第③甲这一族在 runner 上确认少掉四步",
     u"取处": u"`jobs[].steps` 的逐步骤结论（不是 `steps` 视图，也不是日志）",
     u"判法": lambda g: len([l for l in g if u"skipped" in l]) <= 1},
    {u"主张": u"STEP[9] 里 `CI_CHANNEL_GLUE_SCOPE … 粘连计=` 与 `CI_SKIPPED_CAUSES … 无声=0` 各出现一次 ⇒ "
              u"两支守卫的**扫描面**在 runner 上是读数而不是散文",
     u"取处": u"步骤名 `Release script tests` 里以 CI_CHANNEL_GLUE_SCOPE / CI_SKIPPED_CAUSES 开头的行",
     u"判法": lambda g: (any(l.startswith(u"CI_CHANNEL_GLUE_SCOPE") for l in g)
                         and any(l.startswith(u"CI_SKIPPED_CAUSES ") and u"无声=" in l for l in g))},
]


def selfcheck():
    """已知答案喂一遍：带 ANSI 的 FAIL 行必须被看见，否则「红名少掉三条」会变成**空真**。

    R591 ⓪ 第一趟就是这么错的：`lines_in_step` 先 `strip()` 再剥色 ⇒ `startswith("FAIL:")` 恒假、
    集合为空、判法 `<= 0` 成立 ⇒ 报"中"。那条中不是读数，是尺盲。
    """
    d = os.path.join(TMP, "selfcheck.log")
    io.open(d, "w", encoding="utf-8").write(
        u"build-and-test\tRelease script tests\t2026-11-06T04:15:08.944Z \x1b[37;1m"
        u"FAIL: test_x (mod.Class.test_x)\x1b[0m\n")
    hits, _per, _how, lines = lines_in_step(d, u"Release script tests", (u"FAIL:",))
    if hits != 1 or not lines or not lines[0].startswith(u"FAIL:"):
        raise SystemExit(u"READER_SELFTEST=blind 命中=%d 行=%s ⇒ 读取器看不见带色码的行首，"
                         u"本轮所有按前缀筛出来的 0 都不算数" % (hits, lines))
    return u"READER_SELFTEST=seen 带 ANSI 的 FAIL 行命中=1"


def main():
    print(selfcheck())
    report = {}
    for run, sha, note in PAIRS:
        st = status_line(run)
        item = {u"sha": sha, u"备注": note, u"status行": st,
                u"到数": u"是" if u"in_progress" not in st else
                        u"否（status=in_progress ⇒ 未读；0 字节日志=通道还没内容，不是内容里没有）"}
        rc, steps, _e = sh([u"python3", u"scripts/ci_read.py", u"steps", run])
        item[u"失败步骤"] = [l.strip() for l in (steps or u"").splitlines() if u"⇒ failure" in l]
        item[u"逐步骤结论"] = step_conclusions(run)
        if item[u"到数"] != u"是":
            report[run] = item
            continue
        log = fetch_log(run, TMP)
        item[u"log_bytes"] = os.path.getsize(log) if os.path.exists(log) else 0
        if not item[u"log_bytes"]:
            item[u"通道三态"] = u"未读到（`CI_LOG_EMPTY=not-finished`）⇒ 一条不判"
            report[run] = item
            continue
        _h, per, how, lines = lines_in_step(log, u"Release script tests", WIRE_CHANNELS + R591_CHANNELS)
        item[u"通道计数"] = dict(per)
        item[u"取处"] = how
        item[u"STEP9_红名"] = fail_names(lines)
        preds = []
        for i, spec in enumerate(PREDICTIONS_R591):
            needle, prefixes = ROUTES[i]
            _h2, _per2, how2, plines = lines_in_step(log, needle, prefixes)
            ran = any(needle in k and v in (u"success", u"failure")
                      for k, v in item[u"逐步骤结论"].items())
            if not ran:
                preds.append([spec[u"主张"][:78],
                              u"未读到（`CI_STEP_NOT_RUN`：那一步没跑到 ⇒ 不判中/不中）",
                              u"%s ｜ %s" % (needle, how2)])
                continue
            try:
                ok = spec[u"判法"](plines)
            except Exception as exc:
                ok = u"判法抛了：%s" % exc
            if ok is False and u"rc=0" in spec[u"主张"]:
                glued = [l for l in plines if u"rc=" in l and not re.search(u"rc=\\d", l)]
                if glued:
                    ok = u"读不到值（值槽被日志通道打死：`%s`）⇒ 不判中/不中" % glued[0][:78]
            preds.append([spec[u"主张"][:78], (u"中" if ok is True else (u"不中" if ok is False else ok)),
                          u"%s ｜ %s" % (needle, how2)])
        item[u"预测"] = preds

        # ③ 把逐步骤结论落成盘上文件，交给门判 skipped 的成因（门在脚本里，不在我嘴里）
        dump = os.path.join(TMP, "steps_%s.txt" % run)
        if steps_dump_to_file(run, dump):
            skipped = [r for r in ci_skipped_causes.parse_steps_dump(io.open(dump, encoding=u"utf-8").read())
                       if r["conclusion"] == u"skipped"]
            item[u"skipped清单"] = [[r["index"], r["name"]] for r in skipped]
        else:
            item[u"skipped清单"] = u"（取不到 jobs[].steps ⇒ 这一格按未读到处理）"
        report[run] = item

    # 门：本轮台账那一节里，每个 skipped 都要有成因名字
    ledger = os.path.join(ROOT, "AGENT_STATE.md")
    tag = None
    if os.path.exists(ledger):
        t = io.open(ledger, encoding=u"utf-8").read()
        m = re.search(r"(?m)^## (R\d+) 状态（", t)
        tag = m.group(1) if m else None
    gate = []
    for run, item in report.items():
        dump = os.path.join(TMP, "steps_%s.txt" % run)
        if not os.path.exists(dump) or not tag:
            gate.append([run, u"（没对象：清单或台账节缺失 ⇒ 具名不判）"])
            continue
        rows = ci_skipped_causes.parse_steps_dump(io.open(dump, encoding=u"utf-8").read())
        sec = ci_skipped_causes.latest_section(io.open(ledger, encoding=u"utf-8").read(), tag)
        v = ci_skipped_causes.judge_run(rows, sec)
        gate.append([run, u"skipped=%d 未具名=%d %s" % (
            v["skipped"], len(v["unnamed"]),
            [u"步=%d %s" % (r["index"], r["name"][:40]) for r in v["unnamed"]])])
    report[u"_门"] = {u"节": tag or u"（读不到轮次）", u"逐跑": gate}

    out = []
    for run, it in report.items():
        if run == u"_门":
            continue
        out.append(u"RUN=%s ↔ %s 到数=%s status=%s" % (run, it[u"sha"], it[u"到数"], it[u"status行"]))
        out.append(u"  失败步骤=%s" % (u" | ".join(it.get(u"失败步骤", [])) or u"（没有/未读到）"))
        for nm in (u"Release script tests", u"Frame baseline vs working manifest (fixture-set gate)",
                   u"Surface left-axis ruler (BACKLOG 234, wired in R210; venv interpreter in R218)",
                   u"Swift tests (executed-count gate)"):
            out.append(u"  逐步骤结论 %-64s ⇒ %s" % (nm[:64], it[u"逐步骤结论"].get(nm, u"（读不到）")))
        if u"skipped清单" in it:
            out.append(u"  skipped 清单=%s" % (it[u"skipped清单"],))
        if u"通道计数" in it:
            out.append(u"  通道计数=%s" % json.dumps(it[u"通道计数"], ensure_ascii=False))
            out.append(u"  取处=%s" % it[u"取处"])
            out.append(u"  STEP[9] 红名（逐字）=%s" % (it[u"STEP9_红名"],))
        for pv in it.get(u"预测", []):
            out.append(u"  预测=%s ⇒ %s〔%s〕" % (pv[0], pv[1], pv[2]))
    out.append(u"门（ci_skipped_causes run 模式）节=%s" % report[u"_门"][u"节"])
    for run, line in report[u"_门"][u"逐跑"]:
        out.append(u"  %s ⇒ %s" % (run, line))
    text = u"\n".join(out)
    io.open(os.path.join(TMP, "ci_status.txt"), u"w", encoding=u"utf-8").write(text + u"\n")
    io.open(os.path.join(TMP, "ci_readings.json"), u"w", encoding=u"utf-8").write(
        json.dumps(report, ensure_ascii=False, indent=1))
    print(text)
    return 0


if __name__ == u"__main__":
    sys.exit(main())
