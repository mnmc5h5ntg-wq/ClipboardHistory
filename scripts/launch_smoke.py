#!/usr/bin/env python3
"""运行时启动冒烟测试（第三轮审计 §3 C-4）。

静态闸门（R2-21 / `prepare_release.py` 的反汇编检查）只能证明"这个包没有已知的启动障碍"，
它没有把 app 真的启起来。这一步补的是另一半：**启一次，看它真的走到了
`applicationDidFinishLaunching`，而且没有因为第二实例守卫自己静默退出**。

三条设计约束：

1. **绝不碰用户的真存档**。app 用 `CLIPBOARD_HISTORY_DATA_DIR` 指向临时目录，
   日志用 `CLIPBOARD_HISTORY_LOG_DIR` 也指向临时目录（两个开关都是产品里已有的/本轮加的，
   见 `FileHistoryPersistence.dataDirectoryEnvironmentKey` 与 `LifecycleDebugLogger`）。
2. **不靠"退出码 0"当结论**。GUI app 是被我们 terminate 的，退出码必然是负的（信号）；
   判据全部来自生命周期日志的内容 + 进程是否活到了检查点。
3. **判定逻辑是纯函数**（`evaluate`），所以它能在没有 WindowServer 的环境里被自测到；
   真启动那一段在 CI 里是报告型步骤，不在测试里。

用法：`python3 scripts/launch_smoke.py <path/to/时间剪史.app>`；成功输出 `SMOKE_OK=1`，失败退出码 1。
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Dict, List, Optional, Tuple

SUCCESS_MARKER = "applicationDidFinishLaunching called"
# InstanceGuard 命中时的日志文案（同文件里搜得到，改文案时这里会跟着红，不会悄悄失效）
SECOND_INSTANCE_MARKER = "本次启动取消"
SIGTERM_MARKER = "applicationWillTerminate"
# 产品侧 `LifecycleDebugLogger.logFileName` 的字面值。自测会去 Swift 源里核对它，
# 因为文件名一改而这里没改的话，冒烟测试会"读不到日志"并报失败 —— 那条红是探针坏了，
# 不是启动坏了（本轮第一跑就是这么误报的）。
LOG_FILE_NAME = "lifecycle_debug.log"

TIMEOUT_SECONDS = 25.0
POLL_INTERVAL = 0.25


def log_path_for(directory: str) -> str:
    return os.path.join(directory, LOG_FILE_NAME)


def evaluate(log_text: str, alive_at_check: bool, exit_code: Optional[int]) -> Dict[str, object]:
    """把一次启动的观测结果折成结论。纯函数：CI 与自测都能跑同一段判定。

    `exit_code` 是 None 表示此刻仍在运行（还没等到退出）。
    """
    reasons: List[str] = []
    if not log_text:
        reasons.append("日志文件为空或不存在：app 没跑到能写日志的地方")
    if SUCCESS_MARKER not in log_text:
        reasons.append("日志里没有启动成功标记")
    if SECOND_INSTANCE_MARKER in log_text:
        reasons.append("第二实例守卫把这次启动中止了（冒烟测试自己撞上了守卫）")

    if exit_code is not None and not alive_at_check:
        # 提前退出：活到检查点之前就已经死了，那是崩溃或自杀，不是"我们关掉了它"
        if SIGTERM_MARKER not in log_text:
            reasons.append("进程提前退出（退出码 %s），且日志里没有正常终止记录" % exit_code)

    return {
        "ok": not reasons,
        "reasons": reasons,
        "saw_start": SUCCESS_MARKER in log_text,
        "saw_second_instance_abort": SECOND_INSTANCE_MARKER in log_text,
        "saw_terminate": SIGTERM_MARKER in log_text,
        "exit_code": exit_code,
    }


def executable_in(app_bundle: str) -> Optional[str]:
    """从 Info.plist 里读 CFBundleExecutable。

    刻意不依赖 `plutil`（无头 runner 上未必可用），也不硬编码"时间剪史"这个名字：
    附件名会被 GitHub 吞掉非 ASCII 前缀，产品名一改就找不到可执行文件。
    """
    macos_dir = os.path.join(app_bundle, "Contents", "MacOS")
    if not os.path.isdir(macos_dir):
        return None
    plist = os.path.join(app_bundle, "Contents", "Info.plist")
    name = None
    if os.path.exists(plist):
        try:
            with open(plist, "rb") as handle:
                blob = handle.read()
            # 文本 plist 与二进制 plist 都可能在；只找文本形式的键
            marker = b"CFBundleExecutable"
            index = blob.find(marker)
            if index >= 0:
                tail = blob[index + len(marker):]
                start = tail.find(b"<string>")
                end = tail.find(b"</string>")
                if start >= 0 and end > start:
                    name = tail[start + 8:end].decode("utf-8")
        except OSError:
            name = None
    if name:
        candidate = os.path.join(macos_dir, name)
        if os.path.exists(candidate):
            return candidate
    entries = sorted(os.listdir(macos_dir))
    return os.path.join(macos_dir, entries[0]) if entries else None


def run(app_bundle: str,
        settle_seconds: float = 1.0,
        timeout: float = TIMEOUT_SECONDS,
        workdir: Optional[str] = None) -> Tuple[bool, Dict[str, object], str]:
    executable = executable_in(app_bundle)
    if not executable:
        return False, {"ok": False, "reasons": ["在 %s 里找不到包内可执行文件" % app_bundle]}, ""

    own_workdir = workdir is None
    directory = workdir or tempfile.mkdtemp(prefix="launch-smoke-")
    os.makedirs(directory, exist_ok=True)
    data_dir = os.path.join(directory, "data")
    log_dir = os.path.join(directory, "logs")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)
    log_file = log_path_for(log_dir)

    env = dict(os.environ)
    env["CLIPBOARD_HISTORY_DEBUG"] = "1"
    env["CLIPBOARD_HISTORY_LOG_DIR"] = log_dir
    env["CLIPBOARD_HISTORY_DATA_DIR"] = data_dir
    env["CLIPBOARD_HISTORY_SMOKE_INSTANCE"] = str(os.getpid())

    process = subprocess.Popen([executable], env=env,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.time() + timeout
    text = ""
    while time.time() < deadline:
        if process.poll() is not None:
            break
        try:
            with open(log_file, "r", encoding="utf-8", errors="replace") as handle:
                text = handle.read()
        except OSError:
            text = ""
        if SUCCESS_MARKER in text:
            break
        time.sleep(POLL_INTERVAL)

    # 最后再读一次日志：进程也可能**已经退出了**才轮到这次轮询（快速崩溃/快速自杀的那种），
    # 那时循环是 `break` 出来的、`text` 还是空的 —— 只看 `text` 会把"退出了但有日志"误判成"没日志"。
    try:
        with open(log_file, "r", encoding="utf-8", errors="replace") as handle:
            text = handle.read()
    except OSError:
        text = text or ""

    alive = process.poll() is None
    if alive:
        time.sleep(settle_seconds)
        try:
            with open(log_file, "r", encoding="utf-8", errors="replace") as handle:
                text = handle.read()
        except OSError:
            pass
        process.terminate()
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=4)
    exit_code = process.returncode

    verdict = evaluate(text, alive, exit_code)
    if own_workdir:
        shutil.rmtree(directory, ignore_errors=True)
    return bool(verdict["ok"]), verdict, text


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="把打包后的 app 真启一次，看它启动到哪一步")
    parser.add_argument("app_bundle")
    parser.add_argument("--keep-logs", action="store_true", help="把临时目录留着（调试用），并打印它的路径")
    parser.add_argument("--timeout", type=float, default=TIMEOUT_SECONDS)
    args = parser.parse_args(argv)

    workdir = tempfile.mkdtemp(prefix="launch-smoke-") if args.keep_logs else None
    ok, verdict, _text = run(args.app_bundle, timeout=args.timeout, workdir=workdir)
    for key in ("saw_start", "saw_second_instance_abort", "saw_terminate", "exit_code"):
        print("SMOKE_%s=%s" % (key.upper(), verdict.get(key)))
    if workdir:
        print("SMOKE_WORKDIR=%s" % workdir)
    if not ok:
        print("SMOKE_OK=0")
        for reason in verdict["reasons"]:
            print("  - %s" % reason)
        return 1
    print("SMOKE_OK=1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
