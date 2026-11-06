# -*- coding: utf-8 -*-
"""R588 的 ⓪：现读两跑 + 把 R587 交下来的三条预测**由脚本判** + 归因锚照抄不重跑。

三条规矩在这一跑上同时生效：
· **一个非空结论都没有 ⇒ 整格 NOT-RUN**（R557）：`STEP[11] 在不在失败列表` 不算到数，
  `conclusion=` 空 + `status=in_progress` ⇒ 四种出口（甲/乙/丙/丁）一条都不许选，
  三条预测也**一条都不判**（数没到就整格不选，不许先挑一条"看起来对"的出路）。
· **归因锚不重跑**：R587 补记 ⓪·3 ⑥ 那三跑已经逐字到手 ⇒ 这里只从台账里**现读那段原文**并带上
  「取值时刻=R587」，不去重新拉 3MB 日志（重跑一次就把「已到手」变成「今天又验了一遍」的假证人）。
· **forward 更正**：R587 补记 ⓪·2 那句 `RUN_UNFETCHED=这一笔落地时尚不存在` 从本笔起不成立
  （那一跑现在**已创建**，只是还没到数）⇒ 在新节里说，回头改 R587 那一格是禁的。
"""
import io
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TMP = "/tmp/r588"
PAIRS = [("42130898663", "f01ba38", u"R587 主笔：倍率报分布 + 词表一份真值 + 命令对账"),
         ("42131401738", "7abd77d", u"R587 补记笔：STATE 一本 + 六格读单")]
ANCHOR_FROM = u"## R587 补记"        # 归因锚抄这里，不重跑日志

# R587 写在 ci_status_r587.py 的 PREDICTIONS_R588 ⇒ 这里原样接过来（标签逐字，判法逐字）
PREDICTIONS = [
    (u"SCALE_NOT_RUN 是这一支唯一出口（不许出现第二条「不判」通道名）",
     lambda g: (not any(l.startswith(u"FRAME_BASELINE_SCALE_AMBIGUOUS") or
                        l.startswith(u"FRAME_BASELINE_SCALE_TIE_NOT_JUDGED") for l in g))
               and any(l.startswith(u"FRAME_BASELINE_SCALE_NOT_RUN=") for l in g)),
    (u"BAKE 那一行必须带四个新格子（倍率分布=/不一致帧数=/无尺寸段=/原因=）",
     lambda g: any(l.startswith(u"FRAME_BASELINE_BAKE ") and
                   all(k in g_line for k in (u"倍率分布=", u"不一致帧数=", u"无尺寸段=", u"原因="))
                   for g_line in g)),
    (u"既有字段含义一字未改：非并列批次的 capture_scale 仍等于该批众数（分布形如 <倍率>:N 且 原因=ok）",
     lambda g: any(l.startswith(u"FRAME_BASELINE_BAKE ") and
                   (u"原因=ok" in l or u"原因=（无）" in l) for l in g)),
]


def sh(args, timeout=900):
    proc = subprocess.Popen(args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            universal_newlines=True)
    out, err = proc.communicate(timeout=timeout)
    return proc.returncode, out, err


def anchor_verbatim():
    """从台账里现读归因锚那一格（照抄，不重跑）。"""
    text = io.open(os.path.join(ROOT, "AGENT_STATE.md"), encoding="utf-8").read()
    start = text.index(ANCHOR_FROM)
    seg = text[start:start + 12000]
    m = re.search(u"⑥\\s*\\*\\*归因锚[^\\n]*", seg)
    return m.group(0).strip() if m else u"（台账里读不到归因锚那一格 ⇒ 这一腿记未读到）"


def main():
    report = {}
    for run, sha, note in PAIRS:
        rc, steps, err = sh(["python3", "scripts/ci_read.py", "steps", run])
        rc2, latest, _e = sh(["python3", "scripts/ci_read.py", "latest", "--workflow", "CI"])
        head = next((l.strip() for l in (steps or u"").splitlines() if l.startswith("RUN=")), u"")
        concluded = [l for l in (steps or u"").splitlines()
                     if re.search(r"⇒\s*(failure|success|skipped)\s*$", l)]
        status = u""
        # `ci_read.py latest` 只打**最新那一笔** ⇒ 两跑里的旧笔永远匹配不上（这不是"没到数"，
        # 是取数通道只有一格宽）。所以逐跑用 `gh run view --json status,conclusion` 现读。
        rc3, one, _e3 = sh(["gh", "run", "view", run, "--json", "status,conclusion,headSha",
                            "--jq", '[.status,.conclusion,.headSha[0:7]]|join(" ")'])
        status = (one or u"").strip() or u"（gh 读不到 ⇒ 这一格记未读到）"
        item = {"sha": sha, "note": note, "head": head, "steps_raw": (steps or err).strip(),
                "结论行数": len(concluded), "status行": status,
                "latest通道那一行": next((l.strip()[:120] for l in (latest or u"").splitlines()
                                     if l.startswith("RUN=")), u"（latest 只打最新一笔 ⇒ 旧笔永远没有这一行）")}
        if concluded:
            item[u"到数"] = u"是"
            item[u"出口"] = u"到数 ⇒ 由 R588 之后的轮次按四种出口判（本脚本只在未到数时保持简单）"
            item[u"预测"] = [u"（到数了：请用带 gate 正文的版本判，别目测）" for _l, _t in PREDICTIONS]
        else:
            item[u"到数"] = u"否"
            item[u"出口"] = (u"整格 NOT-RUN：一个非空结论都没有（作业还在跑）⇒ 甲/乙/丙/丁 一条都不选；"
                             u"「STEP[11] 在不在失败列表」不算到数（R557）")
            item[u"预测"] = [u"%s=不判（数没到 ⇒ 三条一条都不挑，R557 那条「数没到就整格 NOT-RUN」照用）"
                             % label for label, _t in PREDICTIONS]
        report[run] = item
    report[u"归因锚"] = anchor_verbatim()
    with io.open(os.path.join(TMP, "ci_readings.json"), "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)

    for run, sha, note in PAIRS:
        item = report[run]
        print(u"RUN=%s ↔ %s 到数=%s 头行=%s status=%s" % (run, item["sha"], item[u"到数"],
                                                          item["head"], item["status行"]))
        print(u"  结论行数=%d ⇒ %s" % (item["结论行数"], item[u"出口"]))
        for line in item[u"预测"]:
            print(u"  预测=%s" % line)
    print(u"归因锚（照抄台账，取值时刻=R587）：%s" % report[u"归因锚"][:900])
    return 0


if __name__ == "__main__":
    sys.exit(main())
