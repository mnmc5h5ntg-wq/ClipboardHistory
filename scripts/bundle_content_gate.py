# -*- coding: utf-8 -*-
"""R593 / 靶 2：产物**内容**那一维在 runner 上到底有没有读数。

来历：620 把构建落点从仓库根搬进 `/tmp/<APP>_bundle` 之后，`test_built_bundle_carries_no_app_delegate_stub`
的对象跟着搬了，而它住在电池那一卷里 —— 电池在 CI 上排在 `make bundle` **之前**，所以那一格在 runner 上
**永远不会**有产物可判。它不是"豁免"，是"没有读数"：skip 与判过在输出里可能逐字混着读，所以这一支把
"谁在这一维出声"写成一条独立的、跑在产物已经落地之后的硬门。

判的是产品自己的那条驱动路径产出的东西：`make bundle` 落在那儿的那一份，不是手摆的文件。
读法三条，各自不同：
  · `BUNDLE_CONTENT=absent` ⇒ 产物不在（构建没落地）⇒ **not-run**，不许读成"内容干净"；
  · `APP_DELEGATE_STUB=present` ⇒ D-029 那个形状回来了 ⇒ 红；
  · 解析不出任何桩 ⇒ 尺瞎了（`STUB_SCAN_BLIND`）⇒ 红，"没读到桩"不等于"没有桩"。

用法：python3 scripts/bundle_content_gate.py [BUNDLE] [--repo-root PATH]
退出码：0=判过；1=红（有 AppDelegate 桩 / 尺瞎了）；2=没有对象（产物不在盘上）。
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from scripts import prepare_release  # noqa: E402
from scripts import repo_root_bundle  # noqa: E402

EXECUTABLE = u"ClipboardHistoryApp"
BAD_CLASS = u"ClipboardHistoryApp.AppDelegate"
# 这台机器上按实测应当有的良性桩数（D-029 之后是 3 个）。写死它是因为"一个都没读到"这件事
# 有两种解释：真的没有（不可能）与解析器瞎了 —— 只印数量分不清，所以数量也要判。
EXPECTED_MIN_STUBS = 1


def bundle_path(root, explicit):
    if explicit:
        return explicit
    return repo_root_bundle.makefile_stage(root)


def judge(otool_text):
    stubbed = prepare_release.classes_with_unimplemented_initializers(otool_text)
    if BAD_CLASS in stubbed:
        return 1, (u"APP_DELEGATE_STUB=present 桩在 %s ⇒ 用户一打开就闪退（D-029）；"
                   u"全部桩=%s" % (BAD_CLASS, u",".join(sorted(stubbed))))
    if len(stubbed) < EXPECTED_MIN_STUBS:
        return 1, (u"STUB_SCAN_BLIND=1 一个桩都没解析出来（期望至少 %d 个良性桩）⇒ "
                   u"'没读到'不是'没有'，这一格不许读成干净" % EXPECTED_MIN_STUBS)
    return 0, (u"APP_DELEGATE_STUB=absent 良性桩=%d（%s）⇒ 这一维在 runner 上由这一步出声"
               % (len(stubbed), u",".join(sorted(stubbed))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(u"bundle", nargs=u"?", default=None)
    ap.add_argument(u"--repo-root", default=REPO)
    args = ap.parse_args()
    bundle = bundle_path(args.repo_root, args.bundle)
    exe = os.path.join(bundle, u"Contents", u"MacOS", EXECUTABLE)
    print(u"BUNDLE_TARGET=%s" % bundle)
    if not os.path.exists(exe):
        print(u"BUNDLE_CONTENT=absent 原因=产物不在盘上（构建没落地或落点又漂回仓库根）⇒ 这一格 not-run，"
              u"不许读成『内容干净』")
        return 2
    proc = subprocess.run([u"otool", u"-tvV", u"-arch", u"arm64", exe],
                          capture_output=True, text=True,
                          env=prepare_release.build_child_environment())
    if proc.returncode != 0:
        print(u"BUNDLE_CONTENT_GATE_BROKEN=1 otool 退出码=%d：%s"
              % (proc.returncode, proc.stderr[:200]))
        return 1
    rc, why = judge(proc.stdout)
    print(u"BUNDLE_CONTENT_GATE_RESULT=%s %s" % (u"ok" if rc == 0 else (u"red" if rc == 1 else u"not-run"), why))
    return rc


if __name__ == u"__main__":
    sys.exit(main())
