# -*- coding: utf-8 -*-
"""仓库根不许出现构建出来的 `.app`（BACKLOG 620 的守卫）。

成因（2026-11-06 用户实测）：`make bundle` 以前在仓库根 `ditto` 出一份可执行的
`时间剪史.app`，于是同一台机器上同一个 `CFBundleIdentifier` 有了两个可启动位置
（仓库根 + `/Applications`）；登录项当初注册的是仓库根那一份，重启后 Dock 就出现
第二个"时间剪史"图标，而那份是构建产物、随时会被下一次 make 覆盖。

四条读数，缺一格都不算判过：
  `READER_SELFTEST=` seen / blind —— **自带正对照**：拿一个已知答案的临时目录跑同一条扫描，
      认不出那份 .app 就是尺盲。为什么必须有：在 runner 上仓库根本来就干净，
      没有这条对照，"名单=空"这句话就只是"这里没构建"的同义反复（R590 那一族：扫描面 0 不算数）。
  `BUNDLE_STAGED=` 0/1 —— 构建确实产出过一份（在 Makefile 现读的暂存目录里）。
  `REPO_ROOT_BUNDLE=` present / absent + `名单=`
  `REPO_ROOT_BUNDLE_RESULT=` ok / red / not-run

退出码：0=判过且干净，1=仓库根有可执行 .app，2=没有对象或尺盲（两种都不算绿）。
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile

APP_NAME = u"时间剪史"


def app_bundles_at(root):
    """只看 `root` **这一层**：`<名字>.app/Contents/MacOS` 齐了才算一份可启动副本。

    子目录里的 .app（测试夹具、临时沙箱）不是这一条的靶 —— 判据卷自己就会造出几十个。
    """
    out = []
    if not os.path.isdir(root):
        return out
    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name)
        if not name.endswith(u".app") or not os.path.isdir(path):
            continue
        if os.path.exists(os.path.join(path, "Contents", "MacOS")):
            out.append(name)
    return out


def is_built_bundle(path):
    return os.path.isdir(path) and os.path.exists(os.path.join(path, "Contents", "MacOS"))


def staged_bundle_path(app_name=APP_NAME, stage=u"/tmp/%s_bundle" % APP_NAME):
    """`make bundle` 唯一的落点（R592 起）：暂存目录里那一份，不是仓库根。"""
    return os.path.join(stage, u"%s.app" % app_name)


def makefile_stage(root):
    """暂存目录从 Makefile 的 `STAGE :=` 现读，不在这里抄第二份常量（两处各写就会漂）。"""
    app_name, stage = APP_NAME, None
    path = os.path.join(root, "Makefile")
    if os.path.exists(path):
        for line in io_open(path):
            head, sep, value = line.partition(u":=")
            if not sep:
                continue
            key, value = head.strip(), value.strip()
            if key == u"APP_NAME":
                app_name = value
            elif key == u"STAGE":
                stage = value
    if stage is None:
        return staged_bundle_path(app_name, u"/tmp/%s_bundle" % app_name)
    return staged_bundle_path(app_name, stage.replace(u"$(APP_NAME)", app_name))


def io_open(path):
    with open(path, encoding=u"utf-8", errors=u"replace") as handle:
        for line in handle:
            yield line


def selfcheck():
    """已知答案：造一个含 `X.app/Contents/MacOS/b` 的临时根，扫描必须认出来。"""
    tmp = tempfile.mkdtemp(prefix="repo-root-bundle-selfcheck-")
    try:
        fake = os.path.join(tmp, u"样例.app", "Contents", "MacOS")
        os.makedirs(fake)
        open(os.path.join(fake, "ClipboardHistoryApp"), "w").close()
        found = app_bundles_at(tmp)
        blind_roots = app_bundles_at(os.path.join(tmp, "没有这一层"))
        return (found == [u"样例.app"], found, blind_roots)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def judge(root, staged):
    """三态：red（仓库根有）/ not-run（暂存目录里没有构建产物）/ ok（构建产出了、仓库根没有）。

    顺序是结论的一部分：**红必须排在 not-run 前面**。反过来写的话，
    "仓库根留着一份旧构建 + 这次没构建"这一对就报成"没判到"，那份真东西反而躲过去了。
    """
    found = app_bundles_at(root)
    if found:
        return (1, found, u"red", u"仓库根有可执行 .app ⇒ 同 id 第二份，登录项/Dock 会指向它")
    if not is_built_bundle(staged):
        return (2, found, u"not-run", u"暂存目录里没有构建产物 ⇒ 这一维没判到，不许读成干净")
    return (0, found, u"ok", u"构建只落在暂存目录，仓库根干净")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(u"root", nargs=u"?", default=u".")
    ap.add_argument(u"--staged", default=None)
    ns = ap.parse_args()
    root = os.path.abspath(ns.root)
    staged = ns.staged or makefile_stage(root)

    seen, found, missing = selfcheck()
    print(u"READER_SELFTEST=%s 已知答案=%s 不存在的根=%s"
          % (u"seen" if seen else u"blind", found, missing))
    if not seen:
        print(u"REPO_ROOT_BUNDLE_RESULT=not-run 这一格的读法：尺认不出临时目录里那份 .app ⇒ "
              u"下面所有「名单=空」都不算数")
        return 2

    rc, hits, verdict, why = judge(root, staged)
    print(u"BUNDLE_STAGED=%s 路径=%s" % (u"1" if is_built_bundle(staged) else u"0", staged))
    print(u"REPO_ROOT_BUNDLE=%s 名单=%s" % (u"present" if hits else u"absent", u",".join(hits) or u"-"))
    print(u"REPO_ROOT_BUNDLE_RESULT=%s 这一格的读法：%s" % (verdict, why))
    for name in hits:
        print(u"   offending: %s" % os.path.join(root, name))
    return rc


if __name__ == u"__main__":
    sys.exit(main())
