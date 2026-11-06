# -*- coding: utf-8 -*-
"""`scripts/repo_root_bundle.py` 的自检（R592 / BACKLOG 620）。

这一条判据要钉的是**构建落点**：`make bundle` 从前在仓库根 `ditto` 出一份可执行的
`时间剪史.app`，于是同一个 `CFBundleIdentifier` 在这台机器上有两条都能启动的路径，
登录项/Dock 当初记住的是仓库根那条 ⇒ 用户重启后看到第二个图标。修法在 Makefile，
而守卫必须能自己出声，所以这里五格各对应一种坏法：

1. 尺盲（扫不出临时目录里那份已知的 .app）⇒ 后面所有"名单=空"都不算数 ⇒ 必须能被发现；
2. 真违规（仓库根有 .app）⇒ 必须红；
3. **红不许被 not-run 掩掉**（仓库根有 + 没构建产物）⇒ 仍是红，不是"没判到"；
4. 没对象（没构建产物、仓库根干净）⇒ 具名 not-run，退出码 2，不许读成绿；
5. 扫描面（子目录里的夹具、非 bundle 的同名目录）不许算进来。
"""
from __future__ import annotations

import io
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
GUARD = os.path.join(REPO, "scripts", "repo_root_bundle.py")
sys.path.insert(0, os.path.join(REPO, "scripts"))

import repo_root_bundle as guard                                                  # noqa: E402


def make_bundle_at(root, name=guard.APP_NAME, binary="ClipboardHistoryApp"):
    """造一份"看着就是可启动副本"的目录树：`<名字>.app/Contents/MacOS/<二进制>`。"""
    if not name.endswith(u".app"):
        name = name + u".app"
    path = os.path.join(root, name)
    macos = os.path.join(path, "Contents", "MacOS")
    os.makedirs(macos)
    with io.open(os.path.join(macos, binary), "w", encoding="utf-8") as handle:
        handle.write("#!/bin/sh\necho x\n")
    os.chmod(os.path.join(macos, binary), 0o755)
    return path


class ScanTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="repo-root-bundle-")
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_it_sees_the_bundle_at_the_root_and_ignores_nested_fixtures(self):
        root = os.path.join(self.tmp, "repo")
        os.makedirs(root)
        self.assertEqual([], guard.app_bundles_at(root), "空目录就该是空名单，这是下面几条的基线")
        make_bundle_at(root)
        self.assertEqual([guard.APP_NAME + u".app"], guard.app_bundles_at(root))
        # 判据卷自己会在子目录造几十个 .app 夹具：它们不是这一条的靶。
        nested = os.path.join(root, "scripts", "tests", "fixture")
        os.makedirs(nested)
        make_bundle_at(nested, name=u"夹具")
        self.assertEqual([guard.APP_NAME + u".app"], guard.app_bundles_at(root),
                         "子目录里的夹具被算进仓库根名单 ⇒ 这一条会变成永远红")
        # 同名但不是 bundle 的目录也不算（不许把 `时间剪史.app` 这个名字当成结论）。
        os.makedirs(os.path.join(root, "不是bundle.app"))
        self.assertEqual([guard.APP_NAME + u".app"], guard.app_bundles_at(root),
                         "没有 Contents/MacOS 的空壳目录被当成可启动副本")

    def test_selfcheck_proves_the_ruler_is_not_blind(self):
        seen, found, missing = guard.selfcheck()
        self.assertTrue(seen, "自带正对照失败：尺认不出临时目录里那份 .app ⇒ 名单=空都不算数")
        self.assertEqual([u"样例.app"], found)
        self.assertEqual([], missing, "不存在的路径应该返回空名单，而不是抛出来把整条守卫打死")

    def test_red_is_not_masked_by_a_missing_build_artifact(self):
        """3. 顺序就是结论：有违规时报 red，而不是"没对象"。"""
        root = os.path.join(self.tmp, "repo2")
        os.makedirs(root)
        make_bundle_at(root)
        rc, hits, verdict, _why = guard.judge(root, os.path.join(self.tmp, "没有这一层"))
        self.assertEqual(1, rc, "仓库根有 .app 却因为没构建产物被读成 not-run ⇒ 真违规躲过去了")
        self.assertEqual(u"red", verdict)
        self.assertEqual(1, len(hits))

    def test_clean_root_without_a_build_object_is_a_named_not_run(self):
        """4. 没对象 = 具名 not-run（退出码 2），不是绿。"""
        root = os.path.join(self.tmp, "repo3")
        os.makedirs(root)
        rc, _hits, verdict, why = guard.judge(root, os.path.join(self.tmp, "nope"))
        self.assertEqual(2, rc)
        self.assertEqual(u"not-run", verdict)
        self.assertIn(u"不许读成干净", why, "not-run 这一支要自己说清它不判什么")

    def test_clean_root_with_a_built_staged_bundle_is_ok(self):
        root = os.path.join(self.tmp, "repo4")
        os.makedirs(root)
        staged = make_bundle_at(os.path.join(self.tmp, "stage"))
        rc, _hits, verdict, _why = guard.judge(root, staged)
        self.assertEqual(0, rc)
        self.assertEqual(u"ok", verdict)


class StagedPathTest(unittest.TestCase):
    def test_staged_path_is_read_from_the_real_makefile(self):
        """暂存目录只有一份真值：Makefile 的 `STAGE :=`。抄第二份常量就会漂成两个口径。"""
        path = guard.makefile_stage(REPO)
        self.assertTrue(path.endswith(u".app"), path)
        self.assertNotIn(REPO, path, "暂存目录被算成仓库根下面 ⇒ 这一条自己就会把自己判红")
        self.assertIn(u"_bundle", path, "现读没读到 Makefile 的 STAGE（现读值=%s）" % path)

    def test_staged_path_follows_a_rewritten_makefile(self):
        tmp = tempfile.mkdtemp(prefix="repo-root-bundle-makefile-")
        self.addCleanup(__import__("shutil").rmtree, tmp, True)
        with io.open(os.path.join(tmp, "Makefile"), "w", encoding="utf-8") as handle:
            handle.write(u"APP_NAME := 别的名字\nSTAGE := /tmp/$(APP_NAME)_staging\n")
        self.assertEqual(u"/tmp/别的名字_staging/别的名字.app",
                         guard.makefile_stage(tmp).replace(os.sep, u"/"))


class CliTest(unittest.TestCase):
    def _run(self, args):
        proc = subprocess.run([sys.executable, GUARD] + args,
                              capture_output=True, text=True, timeout=120, cwd=REPO)
        return proc.returncode, proc.stdout

    def test_cli_prints_all_three_readings_and_exits_zero_on_a_clean_root(self):
        tmp = tempfile.mkdtemp(prefix="repo-root-bundle-cli-")
        self.addCleanup(__import__("shutil").rmtree, tmp, True)
        staged = make_bundle_at(os.path.join(tmp, "stage"))
        root = os.path.join(tmp, "repo")
        os.makedirs(root)
        rc, out = self._run([root, u"--staged", staged])
        self.assertEqual(0, rc, out)
        for name in (u"READER_SELFTEST=seen", u"BUNDLE_STAGED=1", u"REPO_ROOT_BUNDLE=absent",
                     u"REPO_ROOT_BUNDLE_RESULT=ok"):
            self.assertIn(name, out, u"通道缺了 %s：\n%s" % (name, out))

    def test_cli_rings_when_the_repo_root_keeps_a_bundle(self):
        tmp = tempfile.mkdtemp(prefix="repo-root-bundle-cli-red-")
        self.addCleanup(__import__("shutil").rmtree, tmp, True)
        root = os.path.join(tmp, "repo")
        os.makedirs(root)
        make_bundle_at(root)
        staged = make_bundle_at(os.path.join(tmp, "stage"))
        rc, out = self._run([root, u"--staged", staged])
        self.assertEqual(1, rc, out)
        self.assertIn(u"REPO_ROOT_BUNDLE=present", out)
        self.assertIn(u"offending:", out, u"红了要能读出是哪一份，不然下一轮还得重跑")


class MakefileRecipeTest(unittest.TestCase):
    """`make -n bundle` 打印的是**真要执行的命令**，所以这一格判的是构建落点本身。

    为什么不跑真构建当证人：`make bundle` 要 lipo 两个 triple + 重签，两分钟起；
    而"仓库根有没有被写"这件事在配方里就定了 —— `-n` 把变量都展开、一条命令都不执行。
    """

    def _recipe(self, target):
        proc = subprocess.run([u"make", u"-n", target], capture_output=True, text=True,
                              timeout=180, cwd=REPO)
        self.assertEqual(0, proc.returncode, proc.stdout[-1500:] + proc.stderr[-1500:])
        return proc.stdout.replace(os.sep, u"/")

    def test_make_bundle_recipe_never_writes_the_repo_root(self):
        recipe = self._recipe(u"bundle")
        staged = guard.makefile_stage(REPO).replace(os.sep, u"/")
        hits = [line.strip() for line in recipe.splitlines()
                if (u"%s.app" % guard.APP_NAME) in line and staged not in line]
        self.assertEqual([], hits,
                         u"配方里出现了不落在暂存目录的那一份 ⇒ 仓库根又会多出可执行副本：\n"
                         + u"\n".join(hits[:8]))
        self.assertIn(staged, recipe, u"打印出来的配方里连暂存目录都没有 ⇒ 这一格没对象")

    def test_run_and_dmg_targets_point_at_the_same_staged_bundle(self):
        for target in (u"run", u"dmg"):
            recipe = self._recipe(target)
            staged = guard.makefile_stage(REPO).replace(os.sep, u"/")
            self.assertIn(staged, recipe,
                          u"%s 用的不是暂存目录那一份 ⇒ 两处各指各的，620 会从另一条路回来" % target)


if __name__ == u"__main__":
    unittest.main()
