#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R111 的变异表：BACKLOG 165 那条「刷新落地要重填」的四格牙（M602–M605）。

本轮做的事：macOS 12 的状态项菜单只在 `makeMenu` / `menuWillOpen` 两处**同步**填，
而 `HistoryStore.refreshPredictions()` 是异步的 ⇒ 菜单可以一直挂着「正在整理推荐…」
（修前实测：9 项里那句还在，候选区没出现）。修法是把"算完了"接回那张菜单。

四刀各钉一句，期望全部从当轮实测来：
  M602 摘掉 `.receive(on: DispatchQueue.main)` ⇒ 期望 **CAUGHT** ——
       `HistoryStore` 在同一个 `MainActor.run` 里**先**置 `isRefreshingPredictions = false`、
       **后**才写候选（`HistoryStore.swift:252-260`），而 `@Published` 的 sink 是同步的
       ⇒ 直接重填读到的是"算完了但候选还空"，菜单从「正在整理」当场翻成「暂无推荐」。
       **这一格是本轮最值钱的一刀**：它钉的不是"有没有重填"，而是**重填读的是哪一刻的值**。
  M603 摘掉 `makeMenu` 里那句接线 ⇒ 期望 **CAUGHT**（钉在调用点守卫上，防"零调用点的死尺"）。
  M604 把 sink 里的「算完了才填」反成「开始算才填」⇒ 期望 **CAUGHT**。
  M605 订阅不被属性持有 ⇒ 期望 **CAUGHT**（`AnyCancellable` 一丢就断；
       替换式写成 `_ = store.$…` 而不是裸表达式，后者会多一条"结果未使用"的编译告警，
       而 0 告警是本仓库的硬门）。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r111.py [M602 ...]
退出码：0 = 每一臂都拿到自己那条期望，且还原干净。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
MENU = "Sources/ClipboardHistoryApp/Managers/MenuBarController.swift"
BEHAVIOUR = "MenuBarPopulationTests/testMenuRepopulatesItselfWhenTheRefreshLands"
WIRING = "MenuBarPopulationTests/testLiveRefreshIsWiredIntoTheMenuTheControllerBuilds"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

ARMS = [
    ("M602", "摘掉 receive(on: .main) ⇒ 同步重填读到还没写候选的那一刻", MENU,
     "            .receive(on: DispatchQueue.main)\n", "", BEHAVIOUR, "CAUGHT"),
    ("M603", "摘掉 makeMenu 里的接线 ⇒ 机制有牙但产品不咬", MENU,
     "        attachLiveRefresh(to: menu, store: historyStore)\n", "", WIRING, "CAUGHT"),
    ("M604", "把「算完了才填」反成「开始算才填」", MENU,
     "                guard !refreshing, store.isRefreshingPredictions == false else { return }",
     "                guard refreshing else { return }", BEHAVIOUR, "CAUGHT"),
    ("M605", "订阅不被属性持有 ⇒ 桥当场失效", MENU,
     "        refreshBridge = store.$isRefreshingPredictions",
     "        _ = store.$isRefreshingPredictions", BEHAVIOUR, "CAUGHT"),
]


def read(key):
    return open(os.path.join(ROOT, key), encoding="utf-8").read()


def write(key, text):
    open(os.path.join(ROOT, key), "w", encoding="utf-8").write(text)


def run(judge):
    env = dict(BASE_ENV)
    r = subprocess.run(["swift", "test", "--filter", judge], cwd=ROOT, env=env,
                       capture_output=True, text=True)
    out = r.stdout + r.stderr
    if "Executed 0 tests" in out:
        return "DID-NOT-RUN", out
    if "error: " in out and "cannot " in out:
        return "DID-NOT-RUN", out          # 刀把代码切坏了 ⇒ 这一臂没跑成，不算抓到
    if "' failed" in out:
        return "CAUGHT", out
    if "with 0 failures" in out:
        return "PASSED", out
    return "DID-NOT-RUN", out


def main():
    keys = sorted(set([a[2] for a in ARMS]))
    originals = dict((k, read(k)) for k in keys)
    print("=== 预检（不注入：两格判据都必须 PASSED）===")
    for judge in (BEHAVIOUR, WIRING):
        verdict, out = run(judge)
        print("  %s %s" % (judge, verdict))
        if verdict != "PASSED":
            print("PREFLIGHT_FAILED：干净树上不是绿的 ⇒ 先修判据/产品（D-175）")
            print(out[-500:])
            return 1
    wanted = sys.argv[1:]
    tally = {}
    mismatch = 0
    not_run = 0
    results = []
    for name, note, fkey, needle, replacement, target, expect in ARMS:
        if wanted and name not in wanted:
            continue
        text = originals[fkey]
        hits = text.count(needle)
        if hits != 1:
            print("%s: DID-NOT-RUN needle 命中 [%d]（期望 1）" % (name, hits))
            tally["DID-NOT-RUN"] = tally.get("DID-NOT-RUN", 0) + 1
            not_run += 1
            results.append((name, expect, "DID-NOT-RUN", note, "needle 命中 %d ⇒ 不注入" % hits))
            continue
        write(fkey, text.replace(needle, replacement, 1))
        verdict, out = run(target)
        write(fkey, originals[fkey])
        tally[verdict] = tally.get(verdict, 0) + 1
        ok = (verdict == expect)
        if not ok:
            mismatch += 1
        if verdict == "DID-NOT-RUN":
            not_run += 1
        snippet = ""
        for line in out.splitlines():
            if "error:" in line and ("XCTAssert" in line or "cannot " in line):
                snippet = line.strip()[:170]
                break
        results.append((name, expect, verdict, note,
                        ("对 期望 %s｜%s" % (expect, snippet)) if ok
                        else ("**不符** 期望 %s 实得 %s｜%s" % (expect, verdict, snippet))))
        print("%s: %s %s" % (name, verdict, note))
    dirty = [k for k in keys if read(k) != originals[k]]
    for k in dirty:
        write(k, originals[k])
    restored = "yes" if not dirty else "二次还原仍不干净：" + ",".join(dirty)
    print("\n=== R111 汇总（每臂按自己的期望判定）===")
    for name, expect, verdict, note, detail in results:
        mark = "OK" if expect == verdict else "!!"
        print("  %s  exp=%-8s got=%-12s %s %s  %s" % (name, expect, verdict, mark, note, detail))
    print("RESTORE_CLEAN=%s" % restored)
    print("MUTATE_TABLE n=%d caught=%d mismatch=%d not_run=%d"
          % (len(results), tally.get("CAUGHT", 0), mismatch, not_run))
    return 0 if (mismatch == 0 and restored == "yes" and len(results) > 0) else 1


if __name__ == "__main__":
    sys.exit(main())
