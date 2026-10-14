#!/usr/bin/env python3
"""动效覆盖地板的闸门：**掉了哪一臂、为什么掉，必须有人报**（R46 / BACKLOG 66 / U-72）。

来历（这一步原来的形状）：`.github/workflows/ci.yml` 的 `Motion coverage floor`
只问一句 `judged < 2 ⇒ 红`。R45 读 CI 时发现 run 38514753036 的读数是
`MOTION_RESOLVE_SUMMARY judged=3/4 not-run=notice-banner-dismiss`，
而 R42 / R42b / R43 三次都是 `judged=4/4 not-run=-` —— **一臂掉了，这一步仍然绿**。
更糟的是控制台上看不到原因：报告那一步用
`grep -E "MOTION_(SUMMARY|…|NOT_RUN)" /tmp/motion.log | head -24` 打读数，
而 `head -24` 把真正要紧的那行挤掉了（我是把三次 run 的日志拉下来人肉对比才发现的）。
⇒ "CI 绿" 与 "读数没退" 是两件事，而后者以前没有任何东西在守。

判什么（除最后一条 `THIN` 之外，每一条都会红，且各自红在不同形状上）：
  NO_RESOLVE      跑完了（`Executed N>0 tests`）却没有结论行 ⇒ 红。
                  原来这一步在这里 `exit 0`（"旧版判据没有这一行"）——
                  那是一张免检牌：本仓库现在每条都打这一行，缺了就是坏了。
                  **R52 补的那一半**：这一格以前只说"没有读数"，不说为什么没有。
                  run 38543090198 就是这样：整族一条 MOTION 都没打，而 CI 那一步的
                  `grep MOTION_NOT_RUN=` 抓不到 XCTest 层的 skip 原因（`XCTSkipUnless` 打的是
                  中文句子，不带 `MOTION_NOT_RUN=` 前缀）⇒ 红是红了，没人知道为什么。
                  现在这里会把 `Test Case … skipped - <原因>` 逐条打出来（最多 4 条）。
  MISSING_KEY     `MOTION_SUMMARY` 的键集合 ≠ 清单里的场景全集 ⇒ 红。
                  `MotionFilmstripTests` 自己的注释就说过为什么：
                  "少一个键会让下游把『没测』读成『测了且为 0』"。
  UNREGISTERED    某臂 not-run，而清单里**没有**这条登记 ⇒ 红（新的盲区必须被写明理由才许通过）。
  REASONLESS      某臂在 resolve 行的 not-run 名单里，但日志里没有一行
                  `MOTION_NOT_RUN=<reason> <arm>` 说为什么 ⇒ 红。
                  "没测到"可以接受，"没测到且说不清为什么"不行。
  BAD_REASON      not-run 的理由不在这一臂登记过的集合里 ⇒ 红（同一臂换了一种坏法 = 新缺陷）。
  UNDERCOVERED    judged < 清单里 `must_judge` 的臂数 ⇒ 红（这就是"地板"）。
  STALE           登记为"今天判不了"（`must_judge=false`）的臂这次**判到了** ⇒ 红。
                  这是好消息，但清单必须跟着删一行，否则它会慢慢变成一堆免检牌
                  （BACKLOG 63 那一族："规矩不许停在口头/登记上"）。
  THIN（**不红**） R52 新增：登记表里某一族臂（`thin_warnings`）这次**全部** not-run，
                  而它们缺席的理由都在登记之内 ⇒ 不红，但必须打一行。
                  为什么不红：这是两台机器今天都做不到的事（横幅那两臂声明 150/120ms，
                  而事件段内最粗的一次采样实测 73–101ms，粗过 0.5×声明这条分辨率线），
                  拿它当硬门就是 R39 那一族"恒红的守卫最后被人删掉"。
                  为什么又要打：不写下来的话，"这一族今天完全没被看"会变成没人知道的常态。
                  红的是**新形状**（换了理由 / 清单外的臂 / 少了一臂的键），不是这条已知事实。

**明确不判的**：`MOTION_SUMMARY <arm>=<帧数>` 里的那个帧数。
R2 已经把这件事证伪过一次 —— 同一份代码本机实测跑过 `2 / 3 / 2`，
因为帧数由采样相位决定；拿它当判据就是在判采样，不是判产品
（`MotionFilmstripTests.changedRunElapsedMilliseconds` 开头那一段是原始记录）。
所以本闸门只判**形状**：谁在、谁不在、不在的理由是什么。

用法：`python3 scripts/motion_floor_gate.py <motion.log> --expectations scripts/motion_floor_expectations.json`

退出码：
  0  一切都在登记之内（含"跑完了但 suite 没跑完 ⇒ SKIPPED"这一条）
  1  上面任何一条红
  2  日志或清单读不到（读不到 ≠ 通过）
"""
import argparse
import json
import re
import sys

RESOLVE = re.compile(r"MOTION_RESOLVE_SUMMARY\s+judged=(\d+)/(\d+)\s+not-run=(\S*)")
SUMMARY = re.compile(r"MOTION_SUMMARY\s+(.*)")
NOT_RUN_LINE = re.compile(r"MOTION_NOT_RUN=([A-Za-z0-9._-]+)[ ：:]\s*([A-Za-z0-9._-]+)?")
EXECUTED = re.compile(r"Executed (\d+) tests?")
# XCTest 层的 skip：`…/MotionFilmstripTests.swift:2402: -[Class testFoo] : Test skipped - <原因>`。
# 这一类原因**不带** `MOTION_NOT_RUN=` 前缀（`XCTSkipUnless` 打的是人话），
# 所以 CI 那一步的 grep 抓不到它 —— 整族一条读数都没打的时候，这是唯一的线索。
SKIP_LINE = re.compile(r"-\[[A-Za-z0-9_.]+ ([A-Za-z0-9_]+)\][^\n]*?: Test skipped - (.+)")


def parse(text: str) -> dict:
    """把一份 motion 日志读成结构化事实。找不到结论行不是异常，是一种事实。"""
    resolve = None
    for line in text.splitlines():
        match = RESOLVE.search(line)
        if match:
            # 取**最后**一条：CI 会把 suite 的 echo 再打一遍，第一版按第一条读，
            # 于是"重打的那一遍"会盖掉真读数。
            resolve = match
    judged, total, not_run = (None, None, set())
    if resolve:
        judged, total = int(resolve.group(1)), int(resolve.group(2))
        raw = resolve.group(3).strip()
        not_run = set() if raw in ("", "-") else {name for name in raw.split(",") if name}

    summary_arms = {}
    for line in text.splitlines():
        match = SUMMARY.search(line)
        if match:
            for pair in match.group(1).split():
                if "=" in pair:
                    name, _, value = pair.partition("=")
                    if value.isdigit():
                        summary_arms[name] = int(value)
            break        # 结论行只有一条，多余的键（如 MOTION_SUMMARY_EXTRA=）不算场景

    # `MOTION_NOT_RUN=<reason> <arm>：…`：reason 里可能带中文冒号，arm 后面也可能没有 arm
    # （`MOTION_NOT_RUN=app-not-active：NSTableView …` 就是没有臂名的那一种）。
    reasons = {}
    for line in text.splitlines():
        match = NOT_RUN_LINE.search(line)
        if match and match.group(2):
            reasons.setdefault(match.group(2), set()).add(match.group(1))

    executed = [int(m.group(1)) for m in EXECUTED.finditer(text)]
    skips = []
    for line in text.splitlines():
        match = SKIP_LINE.search(line)
        if match and (match.group(1), match.group(2)) not in skips:
            skips.append((match.group(1), match.group(2)))
    return {
        "judged": judged,
        "total": total,
        "not_run": not_run,
        "summary_arms": summary_arms,
        "reasons": reasons,
        "skips": skips,
        "executed": executed[-1] if executed else 0,
    }


def verdicts(facts: dict, expectations: dict) -> list:
    """返回 [(标记, 消息, 是否红)]。全绿时只有一条 OK。"""
    arms = expectations.get("arms", {})
    scenarios = expectations.get("scenarios", [])
    must_judge = {name for name, spec in arms.items() if spec.get("must_judge")}
    out = []

    if facts["executed"] == 0:
        # 标记里带值（`…=suite-did-not-finish`）：CI 日志里 grep 的是这个整串，
        # 而旧版 shell 打的就是这一串 —— 换了实现，可 grep 的形状不许变。
        out.append(("MOTION_FLOOR_SKIPPED=suite-did-not-finish",
                    "看门狗收掉了进程 ⇒ 不能把「没跑完」判成「验得不够」",
                    False))
        return out

    if facts["judged"] is None:
        out.append(("MOTION_FLOOR_NO_RESOLVE",
                    "跑完了却没有 MOTION_RESOLVE_SUMMARY ⇒ 这一族的读数今天不存在，"
                    "而旧版这一步在这里 exit 0（免检牌）", True))
        # 红必须有名字（R36）：整族没读数时，唯一能解释它的是 XCTest 层的 skip 原因，
        # 而那些行不带 `MOTION_NOT_RUN=`，CI 那一步的 grep 抓不到 ⇒ 以前这里只有一句"没有读数"。
        skips = facts.get("skips") or []
        if skips:
            out.append(("MOTION_FLOOR_SKIPS",
                        "被 XCTest 层 skip 掉的用例 %d 条（这些原因不带 MOTION_NOT_RUN=，"
                        "CI 那一步的 grep 看不见）：%s"
                        % (len(skips),
                           " | ".join("%s：%s" % (name, reason[:90]) for name, reason in skips[:4])),
                        False))
        else:
            out.append(("MOTION_FLOOR_SKIPS=none-found",
                        "日志里连一行 `Test skipped - <原因>` 都没有 ⇒ 这一族不是被 skip，"
                        "而是根本没执行到打结论行的那一步（看 suite 的退出码与看门狗）", False))
        return out

    missing = [name for name in scenarios if name not in facts["summary_arms"]]
    if missing:
        out.append(("MOTION_FLOOR_MISSING_KEY",
                    "MOTION_SUMMARY 少了这些臂：%s ⇒ 下游会把「没测」读成「测了且为 0」"
                    % ",".join(missing), True))
    extra = [name for name in facts["summary_arms"] if name not in scenarios]
    if extra:
        out.append(("MOTION_FLOOR_UNLISTED_SCENARIO",
                    "MOTION_SUMMARY 出现了清单外的臂：%s ⇒ 清单与判据脱节，新臂没被登记过"
                    % ",".join(extra), True))

    for arm in sorted(facts["not_run"]):
        spec = arms.get(arm)
        if spec is None:
            out.append(("MOTION_FLOOR_UNREGISTERED",
                        "%s not-run 而清单里没有这条登记 ⇒ 新的盲区要先写理由再放行" % arm, True))
            continue
        seen = facts["reasons"].get(arm)
        if not seen:
            out.append(("MOTION_FLOOR_REASONLESS",
                        "%s 在 not-run 名单里，却没有一行 MOTION_NOT_RUN=<reason> %s 说为什么"
                        % (arm, arm), True))
            continue
        allowed = set(spec.get("allowed_not_run_reasons", []))
        unexpected = sorted(seen - allowed)
        if unexpected:
            out.append(("MOTION_FLOOR_BAD_REASON",
                        "%s 的理由是 %s，而登记过的是 %s ⇒ 同一臂换了一种坏法 = 新缺陷"
                        % (arm, ",".join(unexpected), ",".join(sorted(allowed)) or "无"), True))

    for arm, spec in sorted(arms.items()):
        # 只有**明确登记成"这条永远判不了"**（`stale_if_judged`）的臂才因"判到了"而红。
        # 不能写成"凡 must_judge=false 判到了就红"：那正好把 R44 那种会随采样漂的臂
        # 变成反向的恒红（判到红、判不到也红），而恒红的守卫最后会被人删掉（R39 那一族）。
        if (spec.get("stale_if_judged")
                and arm not in facts["not_run"] and arm in facts["summary_arms"]):
            out.append(("MOTION_FLOOR_STALE",
                        "%s 登记为「永远判不了」，这次却判到了 ⇒ 这是好消息，"
                        "把清单里这一条删掉（留着它，清单就慢慢变成免检牌堆）" % arm, True))

    for group in expectations.get("thin_warnings", []):
        arms_in_group = [name for name in group.get("arms", [])]
        if arms_in_group and all(name in facts["not_run"] for name in arms_in_group):
            out.append(("MOTION_FLOOR_THIN",
                        "%s 这一族这次**全部**判不到（缺席理由都在登记之内 ⇒ 不红）。"
                        "今天两台机器都做不到这件事，所以红没有意义；但这一行必须打出来，"
                        "否则「这一族没被看」会变成没人知道的常态。见 %s"
                        % ("/".join(arms_in_group), group.get("points_to", "BACKLOG")),
                        False))

    floor = len(must_judge)
    if facts["judged"] < floor:
        out.append(("MOTION_FLOOR_UNDERCOVERED",
                    "judged=%d/%d 低于地板 %d（= 清单里 must_judge 的臂数）⇒ 动效判据今天没判够"
                    % (facts["judged"], facts["total"], floor), True))
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("log")
    parser.add_argument("--expectations", required=True)
    args = parser.parse_args(argv)

    try:
        with open(args.log, encoding="utf-8", errors="replace") as handle:
            text = handle.read()
    except OSError as error:
        print("MOTION_FLOOR_UNREADABLE=%s" % error)
        return 2
    try:
        with open(args.expectations, encoding="utf-8") as handle:
            expectations = json.load(handle)
    except (OSError, ValueError) as error:
        print("MOTION_FLOOR_EXPECTATIONS_UNREADABLE=%s" % error)
        return 2

    facts = parse(text)
    print("MOTION_FLOOR_FACTS judged=%s/%s executed=%d not-run=%s summary=%s"
          % (facts["judged"], facts["total"], facts["executed"],
             ",".join(sorted(facts["not_run"])) or "-",
             " ".join("%s=%d" % pair for pair in sorted(facts["summary_arms"].items()))))
    results = verdicts(facts, expectations)
    reds = 0
    for marker, message, is_red in results:
        print("%s %s" % (marker, message))
        reds += 1 if is_red else 0
    # `MOTION_FLOOR_OK` 以前只在"一条结果都没有"时打 —— 那等于说"有非红的提示（SKIPPED / THIN）
    # 就没有 OK"。今天 runner 那种"全部在登记之内但这一族很薄"的运行，日志里应当同时
    # 看得见 OK 与 THIN：绿是"没有新形状"，薄是"这一族今天没被看"，两句话都要说。
    if reds == 0:
        print("MOTION_FLOOR_OK=%s/%s 全部臂都在登记之内" % (facts["judged"], facts["total"]))
    print("MOTION_FLOOR_REDS=%d" % reds)
    return 1 if reds else 0


if __name__ == "__main__":
    sys.exit(main())
