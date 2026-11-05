#!/usr/bin/env python3
"""帧基线对比（第三轮审计 §3 C-2）。

CI 已经会把 78 张离屏帧拍出来（D-7 那一轮补的），但它只回答"今天拍得出来吗"，
不回答"和上一版比，哪几帧变了"。视觉回归最难复查的正是后者：
改动者看不见基线， reviewer 只能凭印象比。

这里存的**不是图片**，而是每张帧的 sha256 —— 一份 JSON，随仓库走。

    比对：  python3 scripts/frame_baseline.py compare <frames目录>
    更新：  python3 scripts/frame_baseline.py update  <frames目录>

两条规矩是这套办法有意义的前提：

1. **改了界面就在同一个 commit 里 update 基线**。否则基线永远过期，
   比对结果永远一片红，很快就没人看（这是 D-7 关于"红色要看不得"的同一条教训）。
2. **"消失的一帧"和"多出来的一帧"都算回归**。帧数掉了意味着某个夹具不再被执行 ——
   那正是执行数守卫防的那类事，只是换到了视觉这一侧。

退出码：0 = 完全一致；1 = 有差异（列出帧名）；2 = 用法/环境错误（基线文件不存在等）。
"""
import argparse
import hashlib
import json
import os
import sys
from typing import Dict, List, Optional, Tuple

BASELINE_RELATIVE = os.path.join("docs", "frame_baseline.json")
# 发布时冻结的**逐版本**基线放这里（§3 C-2 要的是"和上一版比"，
# 只有一份可随时 update 的工作基线的话，"上一版"其实是"上一次有人记得 update 的时候"）。
RELEASE_DIR_RELATIVE = os.path.join("docs", "frame_baselines")
SCHEMA_VERSION = 1
import re as _re

_VERSION_IN_NAME = _re.compile(r"v(\d+)\.(\d+)(?:\.(\d+))?")


def version_key(name: str):
    """`v1.4.10` 必须排在 `v1.4.9` 之后 —— 按字符串排会得到相反的答案，
    而这条错误会让"上一版"选错对象，整条 diff 的语义就没了。"""
    match = _VERSION_IN_NAME.search(name)
    if not match:
        return (0, 0, 0, name)
    parts = [int(x) if x else 0 for x in match.groups()]
    return (parts[0], parts[1], parts[2], name)


def manifest_path(repo_root: str) -> str:
    return os.path.join(repo_root, BASELINE_RELATIVE)


# R583 / BACKLOG 655：`check` 以前**只判 missing**，于是 `changed>0` 与 `added>0` 两态谁都不判 ——
# 那 8 张变帧不是被豁免，而是没人看。豁免名单是账，"没人判"不是。
# 现在三态都可数：变帧/新帧必须逐条登记在名册里（帧名 + 理由 + 归哪张单），否则门红。
DRIFT_REGISTRY_RELATIVE = os.path.join("docs", "frame_drift_registry.json")
DRIFT_KINDS = ("changed", "added")


def drift_registry_path(repo_root: str) -> str:
    return os.path.join(repo_root, DRIFT_REGISTRY_RELATIVE)


def load_drift_registry(path: str) -> List[Dict[str, str]]:
    """读登记名册。形状坏了要抛出去，不许在调用方手里变成"0 条 ⇒ 全绿"（R99 那一族）。"""
    with open(path, "r", encoding="utf-8") as handle:
        document = json.load(handle)
    rows = document.get("rows")
    if not isinstance(rows, list):
        raise ValueError("登记名册里没有 rows 列表：%s" % path)
    out = []  # type: List[Dict[str, str]]
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("登记名册里有一行不是对象：%r" % (row,))
        kind = str(row.get("kind", ""))
        if kind not in DRIFT_KINDS:
            raise ValueError("登记名册里有一行的 kind 不认识（只允许 %s）：%r" % ("/".join(DRIFT_KINDS), kind))
        out.append({"frame": str(row.get("frame", "")), "kind": kind,
                    "reason": str(row.get("reason", "")), "ticket": str(row.get("ticket", ""))})
    return out


def judge_drift(changed: List[str], added: List[str], baseline: Dict[str, str],
                current: Dict[str, str],
                rows: Optional[List[Dict[str, str]]]) -> Dict[str, object]:
    """纯函数：三态 + 名册 ⇒ 该红的与只报数的。

    ⚠ **陈旧行只报数、不判**，这不是漏：漂移是**按机器**的（本机那 8 张在 runner 上一张都不漂），
       另一台此刻不漂不代表这条登记写错了 —— 把它判红等于逼人在两台机器之间来回删名册。
       真正该红的是**对不上任何帧名的行**（拼错的、夹具改名后留下的），那条与机器无关。
    """
    rows = rows or []
    registered_changed = set(r["frame"] for r in rows if r["kind"] == "changed")
    registered_added = set(r["frame"] for r in rows if r["kind"] == "added")
    unregistered = [n for n in changed if n not in registered_changed] + \
                   [n for n in added if n not in registered_added]
    unknown = [r["frame"] for r in rows
               if (r["kind"] == "changed" and r["frame"] not in baseline)
               or (r["kind"] == "added" and r["frame"] not in current)]
    bad_fields = [r["frame"] for r in rows if not r["reason"].strip() or not r["ticket"].strip()]
    stale = [r["frame"] for r in rows
             if r["kind"] == "changed" and r["frame"] in baseline and r["frame"] not in changed]
    return {
        "changed": len(changed), "added": len(added),
        "registered": len([n for n in changed if n in registered_changed])
                      + len([n for n in added if n in registered_added]),
        "unregistered": unregistered,
        "rows": len(rows), "unknown": unknown, "bad_fields": bad_fields, "stale": stale,
    }


def sha256_of(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect(frames_dir: str) -> Dict[str, str]:
    """目录里每张 PNG 的 sha256，键是文件名。"""
    result = {}  # type: Dict[str, str]
    for name in sorted(os.listdir(frames_dir)):
        if not name.endswith(".png"):
            continue
        full = os.path.join(frames_dir, name)
        if os.path.isfile(full):
            result[name] = sha256_of(full)
    return result


def compare(baseline: Dict[str, str], current: Dict[str, str]) -> Tuple[List[str], List[str], List[str]]:
    """(变了, 少了, 多了)。分开报是因为三者的处置完全不同：
    变了要人看图，少了要查为什么夹具不跑了，多了要确认是新功能还是重名。"""
    changed = [name for name in sorted(baseline) if name in current and baseline[name] != current[name]]
    missing = [name for name in sorted(baseline) if name not in current]
    added = [name for name in sorted(current) if name not in baseline]
    return changed, missing, added


def load_baseline(path: str) -> Dict[str, str]:
    with open(path, "r", encoding="utf-8") as handle:
        document = json.load(handle)
    frames = document.get("frames")
    if not isinstance(frames, dict):
        raise ValueError("基线文件里没有 frames 字典：%s" % path)
    return {str(k): str(v) for k, v in frames.items()}


def write_baseline(path: str, frames: Dict[str, str]) -> None:
    document = {
        "schema": SCHEMA_VERSION,
        "count": len(frames),
        "note": "离屏帧的 sha256 基线。改了界面就在同一个 commit 里跑 update；"
                "CI 的 compare 步骤靠它回答“上一版比这一版哪些帧变了”。",
        "frames": frames,
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(document, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def release_dir(repo_root: str) -> str:
    return os.path.join(repo_root, RELEASE_DIR_RELATIVE)


def released_baselines(repo_root: str) -> List[str]:
    """按版本号排序的逐版本基线文件名（旧 → 新）。"""
    directory = release_dir(repo_root)
    if not os.path.isdir(directory):
        return []
    return sorted((n for n in os.listdir(directory) if n.endswith(".json")), key=version_key)


def latest_released_baseline(repo_root: str) -> Optional[str]:
    names = released_baselines(repo_root)
    return os.path.join(repo_root, RELEASE_DIR_RELATIVE, names[-1]) if names else None


def snapshot(repo_root: str, version: str) -> Optional[str]:
    """把当前工作基线冻结成 `docs/frame_baselines/vX.Y.Z.json`。

    发布脚本调它（不重拍帧）：冻结的是"这次发出去的包对应的界面"，
    而那份帧在发布前就该由 `update` 确认过是最新的。
    """
    source = manifest_path(repo_root)
    if not os.path.exists(source):
        return None
    frames = load_baseline(source)
    target = os.path.join(release_dir(repo_root), "%s.json" % ("v%s" % version.lstrip("v")))
    write_baseline(target, frames)
    return target


def resolve_baseline_path(repo_root: str, against: str = "auto") -> Tuple[str, str]:
    """返回 (路径, 说明)。`auto` = 有逐版本基线就用最新的那一版，否则退回工作基线。"""
    if against == "working":
        return manifest_path(repo_root), "working"
    latest = latest_released_baseline(repo_root)
    if against == "latest-release":
        if not latest:
            raise ValueError("还没有任何逐版本基线（跑一次 snapshot 才有）")
        return latest, os.path.basename(latest)[:-5]
    if latest:
        return latest, os.path.basename(latest)[:-5]
    return manifest_path(repo_root), "working"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="离屏帧基线的比对与更新")
    parser.add_argument("action", choices=["compare", "update", "check", "snapshot"])
    parser.add_argument("frames_dir", nargs="?", default=None,
                        help="compare / check / update 必需；snapshot 只冻结已有的工作基线")
    parser.add_argument("--version", default=None, help="snapshot 用：要冻结成哪个版本（如 1.4.8）")
    parser.add_argument("--allow-missing", action="append", default=[],
                        help="允许缺席的帧名（可重复）。无头 runner 上有几帧注定拍不出来 —— "
                             "「捕获失效闸门」拒绝把 95%% 空白的帧当证据写盘，那是诚实的行为。"
                             "把它们列在这里，剩下的缺席才是真回归。")
    parser.add_argument("--repo-root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    parser.add_argument("--against", default="auto", choices=["auto", "working", "latest-release"],
                        help="比对对象：默认 auto，即有逐版本基线就和最新一版比，否则和工作基线比")
    parser.add_argument("--drift-registry", default=None,
                        help="变帧/新帧的逐张登记名册（默认 docs/frame_drift_registry.json）。"
                             "check 用它把 changed 与 added 两态也变成会红的判据 —— 登记是账，不是措辞。")
    args = parser.parse_args(argv)

    if args.action != "snapshot":
        if not args.frames_dir:
            print("FRAME_BASELINE_ERROR=%s 需要 frames 目录参数" % args.action)
            return 2
    if args.frames_dir is not None and not os.path.isdir(args.frames_dir):
        print("FRAME_BASELINE_ERROR=frames 目录不存在：%s" % args.frames_dir)
        return 2

    if args.action == "snapshot":
        if not args.version:
            print("FRAME_BASELINE_ERROR=snapshot 需要版本号")
            return 2
        target = snapshot(args.repo_root, args.version)
        if not target:
            print("FRAME_BASELINE_ERROR=还没有工作基线可冻结（先跑 update）")
            return 2
        print("FRAME_BASELINE_SNAPSHOT=%s" % target)
        return 0

    if args.action == "update":
        frames = collect(args.frames_dir)
        # 工作基线永远写在 docs/frame_baseline.json：逐版本的那份是它的快照，不是替代品。
        write_baseline(manifest_path(args.repo_root), frames)
        print("FRAME_BASELINE_UPDATED=%d" % len(frames))
        return 0

    try:
        path, against_label = resolve_baseline_path(args.repo_root, args.against)
    except ValueError as error:
        print("FRAME_BASELINE_ERROR=%s" % error)
        return 2
    if not os.path.exists(path):
        print("FRAME_BASELINE_ERROR=基线不存在：%s（先跑 update）" % path)
        return 2

    try:
        baseline = load_baseline(path)
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print("FRAME_BASELINE_ERROR=基线读不出来：%s" % error)
        return 2

    current = collect(args.frames_dir)
    changed, missing, added = compare(baseline, current)
    # 先扣掉许可名单，再谈"少帧"：否则这条硬门只是把 runner 的物理限制每天复述一遍。
    allowed = [name for name in missing if name in set(args.allow_missing)]
    missing = [name for name in missing if name not in set(args.allow_missing)]
    print("FRAME_BASELINE_AGAINST=%s" % against_label)
    print("FRAME_BASELINE_COMPARED=%d" % len(current))
    if allowed:
        print("FRAME_BASELINE_ALLOW_MISSING=%d  %s" % (len(allowed), ", ".join(allowed)))
    print("FRAME_BASELINE_CHANGED=%d" % len(changed))
    print("FRAME_BASELINE_MISSING=%d" % len(missing))
    print("FRAME_BASELINE_ADDED=%d" % len(added))
    for name in changed:
        print("  changed  %s" % name)
    for name in missing:
        print("  missing  %s  <- 夹具不再产出这一帧，必须查" % name)
    for name in added:
        print("  added    %s" % name)
    if args.action != "check":
        return 1 if (changed or missing or added) else 0

    # —— check：三态都要有人判。以前这里只写 `return 1 if missing else 0`，
    #    于是 changed/added 两态"命令成功、输出看着齐、其实谁都没判"（R583 / 655 那个洞）。
    registry = args.drift_registry or drift_registry_path(args.repo_root)
    rows = None      # type: Optional[List[Dict[str, str]]]
    registry_state = "absent"
    if os.path.exists(registry):
        try:
            rows = load_drift_registry(registry)
            registry_state = "loaded"
        except (ValueError, OSError, json.JSONDecodeError) as error:
            print(u'FRAME_BASELINE_DRIFT_REGISTRY=broken %s ⇒ 名册读不出来时不许当成「没有登记」' % error)
            return 2
    verdict = judge_drift(changed, added, baseline, current, rows)
    print("FRAME_BASELINE_DRIFT_REGISTRY=%s %s 行=%s" % (registry_state, registry, verdict["rows"]))
    print("FRAME_BASELINE_DRIFT 变帧=%d 新帧=%d 已登记=%d 未登记=%d 名册对不上帧名=%d 名册空理由或空单号=%d 陈旧行=%d"
          % (verdict["changed"], verdict["added"], verdict["registered"],
             len(verdict["unregistered"]), len(verdict["unknown"]),
             len(verdict["bad_fields"]), len(verdict["stale"])))
    for name in verdict["unregistered"]:
        print("  未登记  %s  <- 既没在名册里登记，也没人判它 ⇒ 门红（补登记或查为什么变了，不许调宽阈值）" % name)
    for name in verdict["unknown"]:
        print("  名册对不上  %s  <- 名册里这一行既不对应当前基线的变帧、也不对应当前产出的新帧（拼错或夹具改名后留下的）" % name)
    for name in verdict["bad_fields"]:
        print("  名册缺字段  %s  <- 登记必须有理由与单号，否则它只是措辞" % name)
    for name in verdict["stale"]:
        print("  陈旧行（只报数）  %s  <- 这台机器此刻不漂；漂移按机器，删行会逼两台来回改" % name)
    blockers = len(missing) + len(verdict["unregistered"]) + len(verdict["unknown"]) + len(verdict["bad_fields"])
    print("FRAME_BASELINE_RESULT=%s 拦路=%d（缺席%d 未登记%d 对不上%d 缺字段%d）"
          % ("ok" if blockers == 0 else "red", blockers, len(missing),
             len(verdict["unregistered"]), len(verdict["unknown"]), len(verdict["bad_fields"])))
    return 0 if blockers == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
