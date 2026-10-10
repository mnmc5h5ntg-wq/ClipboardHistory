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
    if args.action == "check":
        # check = 只要求"一帧不许少"（多帧与变帧交给人判断，因为新功能本来就会加帧）。
        return 1 if missing else 0
    return 1 if (changed or missing or added) else 0


if __name__ == "__main__":
    sys.exit(main())
