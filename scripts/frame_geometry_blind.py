# -*- coding: utf-8 -*-
"""R593 / 靶 1：帧通道对"产品默认几何"这一维是不是盲的 —— 量出来，不许只在注释里推。

来历（不是修辞问题）：R592 把默认几何从 750/420 抬到 848/424，而同一轮台账里那句
"356 张帧与上一批逐字节相同"被读成了"像素没动 ⇒ 产品没动"的反证。**那句话的方向是反的**：
捕获通道走的是夹具自己钉死的尺寸，`UICaptureHarness.swift` 里 `MainWindowCollapsePolicy` 出现 **0 次**
（本轮现读），所以产品默认怎么改，那一批帧都不会动 ⇒ 帧逐字节相同在这一维**不含任何信息**。
把它当证人，就等于把"尺看不见"说成"没发生"（R558 / R560 那一族）。

判法写成三个量，都是扫出来的，不是抄来的：
  · `refs`   —— 捕获侧（harness + 夹具卷）引用产品默认几何那组常量的次数；
  · `tiers`  —— 帧基线里出现的尺寸档数（用来证明"这一维有 356 张帧、0 张与默认同源"）；
  · `登记`   —— `docs/frame_geometry_blind.json` 里那次测量记的产品默认值。
三种结论：
  A. `refs > 0` 而登记说盲 ⇒ **红**：帧通道现在看得见默认几何了，那条具名要撤（不许留着当永久豁免）。
  B. `refs == 0` 而现读默认 != 登记默认 ⇒ **红**：默认变了而这一维没有像素证人 ⇒ 必须补第二条独立通道
     或把这一格具名留在账上并说清谁签（本轮就是这一格在响：848/424/600 vs 登记 750/420）。
  C. `refs == 0` 且默认与登记一致 ⇒ ok，照旧印那行 blind 读数。

正对照不是可选项：`selfcheck()` 拿两份合成树各跑一遍（一份 harness 里带常量引用 ⇒ 必须读成"不盲"，
一份默认被挪走 ⇒ 必须判红）。扫不出这两样就 exit 2 —— 没有正对照的"名单=空"只是"这里根本没引用"。

用法：python3 scripts/frame_geometry_blind.py [--repo-root PATH] [--policy PATH] [--harness PATH]
退出码：0=判过；1=红（A 或 B）；2=读不到对象或尺自己瞎了。
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLICY = os.path.join("ClipboardHistory", "Sources", "ClipboardHistoryApp",
                      "Models", "MainWindowCollapsePolicy.swift")
HARNESS = os.path.join("ClipboardHistory", "Tests", "ClipboardHistoryAppTests", "UICaptureHarness.swift")
FIXTURE_TESTS = os.path.join("ClipboardHistory", "Tests", "ClipboardHistoryAppTests")
REGISTRY = os.path.join("docs", "frame_geometry_blind.json")
BASELINE = os.path.join("docs", "frame_baseline.json")
# 捕获侧要引用的就是这三个常量；写全名而不是 `Default` 这种短词，短词在别处会撞出假"不盲"。
CONSTANTS = (u"expandedWidthDefault", u"collapsedWidthDefault", u"contentHeightDefault")


def read(path):
    with io.open(path, encoding=u"utf-8", errors=u"replace") as handle:
        return handle.read()


def policy_defaults(path):
    """从产品源码现读那三档默认值（不在这里抄第二份常量，抄了就会漂）。"""
    text = read(path)
    out = {}
    for name in CONSTANTS:
        m = re.search(r"static\s+let\s+" + name + r"\s*:\s*CGFloat\s*=\s*([0-9.]+)", text)
        if not m:
            return None
        out[name] = float(m.group(1))
    return out


def capture_refs(tests_dir, extra_harness=None):
    """捕获侧引用默认几何常量的次数（逐文件、逐常量）。

    扫描面只算**捕获这一条通道**：harness + 那一卷里的夹具表。不许扩到整个 Tests 目录去数
    `FoldGeometryMigrationTests` 自己的引用 —— 那是判据本身，不是捕获通道。
    """
    files = []
    for name in sorted(os.listdir(tests_dir)):
        if name.endswith(u".swift") and (u"Capture" in name or u"Harness" in name):
            files.append(os.path.join(tests_dir, name))
    if extra_harness:
        files.append(extra_harness)
    refs, hit_files = 0, []
    for path in files:
        text = read(path)
        n = sum(text.count(c) for c in CONSTANTS) + len(re.findall(r"MainWindowCollapsePolicy\b", text))
        if n:
            hit_files.append(os.path.basename(path))
        refs += n
    return refs, len(files), hit_files


def frame_tiers(baseline_path):
    if not os.path.exists(baseline_path):
        return None, 0
    data = json.loads(read(baseline_path))
    frames = data.get(u"frames") or {}
    names = list(frames) if isinstance(frames, dict) else [f.get(u"name", u"") for f in frames]
    tiers = set()
    for name in names:
        m = re.search(r"(\d+)x(\d+)", name)
        if m:
            tiers.add((int(m.group(1)), int(m.group(2))))
    return tiers, len(names)


def load_registry(path):
    if not os.path.exists(path):
        return None
    return json.loads(read(path))


def judge(defaults, refs, file_count, tiers, frame_count, registered):
    """返回 (rc, 逐字读数行列表)。红排在 not-run 前面（R590 那一课：先判有没有违规，再判有没有对象）。"""
    out = []
    tier_default = (int(defaults[u"expandedWidthDefault"]), int(defaults[u"contentHeightDefault"]))
    same_tier = 0 if tiers is None else sum(1 for t in tiers if t == tier_default)
    out.append(u"FRAME_GEOMETRY_DEFAULTS 展开=%.0fx%.0f 折叠=%.0fx%.0f 捕获侧引用=%d 扫的文件=%d "
               u"帧档数=%s 帧数=%d 与默认同档的帧=%d"
               % (defaults[u"expandedWidthDefault"], defaults[u"contentHeightDefault"],
                  defaults[u"collapsedWidthDefault"], defaults[u"contentHeightDefault"],
                  refs, file_count,
                  (len(tiers) if tiers is not None else u"（没读到）"), frame_count, same_tier))
    if registered is None:
        out.append(u"FRAME_GEOMETRY_BLIND_RESULT=not-run 原因=登记不在盘上（第一次跑要先登记，不是判过）")
        return 2, out
    reg = registered.get(u"policy_defaults") or {}
    moved = {k: v for k, v in defaults.items() if float(reg.get(k, -1)) != float(v)}
    if refs > 0:
        out.append(u"FRAME_GEOMETRY_BLIND_RESULT=red 原因=A 登记说盲（refs=%s）而现读 refs=%d ⇒ "
                   u"捕获通道已经引用产品默认几何，那条具名要撤，不许留着当永久豁免"
                   % (registered.get(u"harness_policy_refs"), refs))
        return 1, out
    if moved:
        out.append(u"FRAME_GEOMETRY_BLIND_RESULT=red 原因=B 默认几何变了 %s 而捕获侧引用仍是 0 ⇒ "
                   u"这一维没有像素证人：要么补第二条独立通道，要么把这一格具名留在账上并说清谁签"
                   % json.dumps(moved, ensure_ascii=False, sort_keys=True))
        return 1, out
    out.append(u"FRAME_GEOMETRY_BLIND=policy-default 帧数=%d 与默认同档的帧=%d 引用=%d ⇒ "
               u"帧通道对这一维盲，这条具名继续挂着（它答的是『有没有人用帧判这一维』，不是『这一维有没有问题』）"
               % (frame_count, same_tier, refs))
    out.append(u"FRAME_GEOMETRY_BLIND_RESULT=ok")
    return 0, out


def selfcheck(root):
    """两把正对照：合成一份"捕获侧引用了常量"的树必须读成不盲；合成一份"默认被挪走"的必须判红。

    少了这一步，`refs=0` 这句话就退化成"这里根本没构建过/扫错了目录"（R590 那一族：扫描面 0 不算数）。
    """
    import tempfile
    tmp = tempfile.mkdtemp(prefix=u"frame-geometry-blind-")
    tests_dir = os.path.join(tmp, "Tests")
    os.makedirs(tests_dir)
    with io.open(os.path.join(tests_dir, u"UICaptureHarness.swift"), u"w", encoding=u"utf-8") as h:
        h.write(u"// 合成：捕获侧引用了产品默认常量 ⇒ refs 必须 > 0\n"
                u"let w = MainWindowCollapsePolicy.expandedWidthDefault\n"
                u"let h = MainWindowCollapsePolicy.contentHeightDefault\n")
    refs, files, hits = capture_refs(tests_dir)
    a = (refs > 0 and files == 1 and hits == [u"UICaptureHarness.swift"])
    with io.open(os.path.join(tests_dir, u"UICaptureHarness.swift"), u"w", encoding=u"utf-8") as h:
        h.write(u"// 合成：捕获侧一次都不提默认几何 ⇒ refs 必须 = 0\nimport AppKit\n")
    refs0, _, _ = capture_refs(tests_dir)
    defaults = {u"expandedWidthDefault": 848.0, u"collapsedWidthDefault": 424.0,
                u"contentHeightDefault": 600.0}
    registered_moved = {u"policy_defaults": {u"expandedWidthDefault": 750.0,
                                             u"collapsedWidthDefault": 420.0,
                                             u"contentHeightDefault": 600.0},
                        u"harness_policy_refs": 0}
    rc_moved, _ = judge(defaults, 0, 1, {(848, 600)}, 356, registered_moved)
    registered_same = {u"policy_defaults": defaults, u"harness_policy_refs": 0}
    rc_ok, _ = judge(defaults, 0, 1, {(720, 520)}, 356, registered_same)
    registered_refs = {u"policy_defaults": defaults, u"harness_policy_refs": 0}
    rc_A, _ = judge(defaults, 3, 1, {(720, 520)}, 356, registered_refs)
    b = refs0 == 0 and rc_moved == 1 and rc_ok == 0 and rc_A == 1
    ok = a and b
    print(u"READER_SELFTEST=%s 正对照A(引用必须读成不盲)=%d 正对照B(默认挪走必须红)=%d "
          u"对照C(一致时绿)=%d 对照D(refs>0 而登记说盲)=%d"
          % (u"seen" if ok else u"blind", 1 if a else 0,
             1 if (refs0 == 0 and rc_moved == 1) else 0, 1 if rc_ok == 0 else 0, 1 if rc_A == 1 else 0))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(u"--repo-root", default=REPO)
    ap.add_argument(u"--policy")
    ap.add_argument(u"--harness-dir")
    args = ap.parse_args()
    root = args.repo_root
    if not selfcheck(root):
        print(u"FRAME_GEOMETRY_BLIND_RESULT=red 原因=尺瞎了（正对照没响）⇒ 这一格今天没判")
        return 2
    policy = args.policy or os.path.join(root, POLICY)
    tests_dir = args.harness_dir or os.path.join(root, FIXTURE_TESTS)
    defaults = policy_defaults(policy)
    if defaults is None:
        print(u"FRAME_GEOMETRY_DEFAULTS=not-run 原因=产品里读不到那三档默认常量（%s）⇒ 不判" % policy)
        return 2
    refs, file_count, hits = capture_refs(tests_dir)
    tiers, frame_count = frame_tiers(os.path.join(root, BASELINE))
    registered = load_registry(os.path.join(root, REGISTRY))
    rc, lines = judge(defaults, refs, file_count, tiers, frame_count, registered)
    for line in lines:
        print(line)
    return rc


if __name__ == u"__main__":
    sys.exit(main())
