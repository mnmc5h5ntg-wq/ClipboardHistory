# -*- coding: utf-8 -*-
"""R594 靶 2 / BACKLOG 668：把"交给下一轮的那段预测块"做成**会红的守卫**。

来历（都是本仓库自己栽过的，不是假想）：
· R593：`PREDICTIONS_R594` 里两条 lambda 举着只定义在 `main()` 函数体里的名字
  （`KNOWN_RUNNER_REDS` / `R592_LOCAL_RAN`）⇒ 下一轮真调用就是 `NameError`。那一族没人报，
  因为那个块从头到尾只被"读出来贴进台账"，**从没被执行过**。
· R590 / R592：判法写成 `all(...)` 之类 ⇒ 空输入（那一行根本没印出来）时返回 True，
  于是"通道缺席"被读成"预测命中"。这一族在台账里被叫做"把没读到写成中"。
· R588：只有"主张 + 判法"两格的预测会把**真主张**判成不中，因为没写"正文从哪一步取"；
  R589 又补了第四格"这条通道由哪一步以什么方式印出去"。缺格 = 下一轮从问题开始。

这一支做四件事，每件都是可数的：
① 把那段 `PREDICTIONS_R<未来>` 真的 `exec` 出来（模块顶层常量随之定义）⇒ 引用不存在的名字当场红；
② 每条都真调用一次判法（含目标 token 的合成正文 + 空输入 + 无关输入三种）⇒ 不许只贴不跑；
   ⚠ 这里**不判**"该不该命中"：命中与否由下一轮那份真日志说（取处/通道两格就是为这件事写的）；
   这一支只保证"能被调用、不崩、且不会在 absence 上白过"。
③ **空输入必须判 False**（absence 不许被满足）+ **无关输入必须判 False**（判法要有牙）；
④ 四格齐（主张 / 判法 / 取处 / 通道），缺任一格红 —— 缺格不是"少一句说明"，是让下一轮重新猜。

名单为空 = 红（R99 那一族：解析器坏掉时会安静地给 0 条然后全绿）。
只读：不改那个脚本，不写台账。
"""
from __future__ import annotations

import argparse
import glob
import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(REPO, ".scratch", "motion-audit-2")
BLOCK_KEY = re.compile(r"^PREDICTIONS_R(\d+)$")
REQUIRED = (u"主张", u"判法", u"取处", u"通道")
# 合成正文：① 含各条判法要的 token（证明它读得到），② 一份完全无关的（证明它有牙）。
POSITIVE = u"""RUN=99900000001 sha=abcdef1 status=completed conclusion=failure
SKIP_ROSTER 键=github-runner 类=runner 内层Ran=900 内层判=ok 内层skip汇总=6 解析=7 名单外=无 名册未跳=无
Ran 999 tests in 123.456s
BUNDLE_CONTENT_GATE_RESULT=ok APP_DELEGATE_STUB=absent 良性桩=3
REPO_ROOT_BUNDLE_RESULT=ok 这一格的读法：构建只落在暂存目录，仓库根干净
READER_SELFTEST=seen 已知答案=['样例.app'] 不存在的根=[]
SMOKE_TARGET=/tmp/时间剪史_bundle/时间剪史.app
PROBE_COVERAGE_SUMMARY 最差帧=97.9ms 超锚=0
Test Case '-[x.Y.testActionableInkStaysAboveTheLegibilityFloor]' failed
""".split(u"\n")
NEGATIVE = [u"完全无关的一行", u"another line that means nothing"]


def newest_block_file(path=None):
    if path:
        return path
    cands = sorted(glob.glob(os.path.join(DIR, "ci_status_r*.py")))
    if not cands:
        return None
    return cands[-1]


def load_block(file_path):
    """返回 (键名, 条目列表, 错误) —— 顶层只跑常量与 def，`main()` 不会被调用。"""
    src = io.open(file_path, encoding="utf-8").read()
    ns = {"__name__": "prediction_block_under_guard", "__file__": file_path}
    try:
        exec(compile(src, file_path, "exec"), ns)
    except BaseException as exc:                       # noqa: BLE001 —— 载入失败就是红
        return None, [], u"载入脚本就崩：%s：%s" % (type(exc).__name__, exc)
    keys = sorted([k for k in ns if BLOCK_KEY.match(k)], key=lambda k: int(BLOCK_KEY.match(k).group(1)))
    if not keys:
        return None, [], u"这个文件里读不到任何 `PREDICTIONS_R<未来>` 那一段 ⇒ 名单为空不许读成全绿"
    key = keys[-1]
    block = ns[key]
    if not isinstance(block, list) or not block:
        return key, [], u"%s 不是非空的列表（实得 %r）" % (key, type(block).__name__)
    return key, block, None


def judge_entry(entry):
    """一条预测的四格 + 两向牙，全部判完才返回问题列表。"""
    problems = []
    if not isinstance(entry, dict):
        return [u"这一条不是字典：%r" % (entry,)]
    claim = entry.get(u"主张", u"")
    fn = entry.get(u"判法")
    label = (claim or u"（没有主张那一格）")[:34]
    for cell in REQUIRED:
        if cell not in entry:
            problems.append(u"%s 缺「%s」那一格" % (label, cell))
    if not callable(fn):
        problems.append(u"%s 的「判法」不可调用（实得 %r）" % (label, type(fn).__name__))
        return problems
    try:
        hit = fn(POSITIVE)
    except BaseException as exc:                       # noqa: BLE001 —— NameError 那一族就在这里
        problems.append(u"%s 真调用就崩：%s：%s" % (label, type(exc).__name__, exc))
        return problems
    try:
        on_empty = fn([])
        on_junk = fn(NEGATIVE)
    except BaseException as exc:                       # noqa: BLE001
        problems.append(u"%s 喂空/无关输入就崩：%s" % (label, exc))
        return problems
    # ⚠ 这一支**不判**"在合成正文上该不该命中"：每条预测的"命中对象"是下一轮那份真日志，
    # 由取处/通道那两格说；在这里用通用样本来要求命中，等于用我的猜测换掉它的承诺（会误红）。
    # 合成正文只用来证明"这条判法能被真调用而不崩"。
    del hit
    if on_empty:
        problems.append(u"%s 在**空输入**上判 True ⇒ absence 会被读成命中（R590/R592 那一族）" % label)
    if on_junk:
        problems.append(u"%s 对完全无关的行也判 True ⇒ 判法没牙（坐死 True 或写成了恒真门）" % label)
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=None, help="要判的 ci_status 脚本；默认取现读最新那一份")
    ap.add_argument("--selftest", action="store_true", help="只跑内置的合成对照")
    args = ap.parse_args(argv)

    bad = 0
    if args.selftest:
        # 合成对照三块：好的那块必须 0 问题；坏的两块（缺通道 + 空输入为真）必须各被抓到。
        good = [{u"主张": u"x", u"判法": lambda g: any(u"SKIP_ROSTER" in l for l in g),
                 u"取处": u"STEP[9]", u"通道": u"电池那一步的 stdout"}]
        hollow = [{u"主张": u"y", u"判法": lambda g: all(u"k" in l for l in g),
                   u"取处": u"STEP[9]", u"通道": u"电池"}]
        missing = [{u"主张": u"z", u"判法": lambda g: bool(g), u"取处": u"STEP[16]"}]
        dead = [{u"主张": u"w", u"判法": lambda g: True, u"取处": u"x", u"通道": u"y"}]
        cases = [(u"四格齐", good, 0), (u"空输入满足", hollow, 1),
                 (u"缺通道", missing, 1), (u"坐死 True", dead, 2)]
        for name, block, expect_min in cases:
            got = sum(len(judge_entry(e)) for e in block)   # 数的是**问题条数**，不是有问题的条目数
            # 下限而不是精确值：一条坏形状可以同时踩到"没牙"和"空输入为真"两格，
            # 要求恰好 N 会把守卫写成"只能以一种坏法红"。好那块必须是 0。
            ok = (got == 0) if expect_min == 0 else (got >= expect_min)
            print(u"SELFTEST %s 问题条数=%d 期望=%s ⇒ %s"
                  % (name, got, u"恰 0" if expect_min == 0 else u"≥%d" % expect_min,
                     u"ok" if ok else u"red"))
            bad += 0 if ok else 1
        if bad:
            print(u"PREDICTION_BLOCK_RESULT=red 合成对照没过 ⇒ 守卫自己坏了")
            return 1
        print(u"PREDICTION_BLOCK_SELFTEST=seen 对照=4 不符=0")

    path = newest_block_file(args.file)
    if not path:
        print(u"PREDICTION_BLOCK_RESULT=red 找不到任何 ci_status_r*.py ⇒ 交接通道没有对象")
        return 1
    key, block, err = load_block(path)
    if err:
        print(u"PREDICTION_BLOCK 文件=%s ⇒ %s" % (os.path.basename(path), err))
        print(u"PREDICTION_BLOCK_RESULT=red")
        return 1
    print(u"PREDICTION_BLOCK 文件=%s 键=%s 条数=%d" % (os.path.basename(path), key, len(block)))
    reds = 0
    for i, entry in enumerate(block, 1):
        problems = judge_entry(entry)
        print(u"  ⑤%d %s" % (i, u"ok" if not problems else u"；".join(problems)))
        reds += 1 if problems else 0
    print(u"PREDICTION_BLOCK 判完=%d 有问题=%d" % (len(block), reds))
    if reds:
        print(u"PREDICTION_BLOCK_RESULT=red ⇒ 这一段贴进台账之前先修，否则下一轮拿它判不出任何事")
        return 1
    print(u"PREDICTION_BLOCK_RESULT=ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
