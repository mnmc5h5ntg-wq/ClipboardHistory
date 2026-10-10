import datetime as dt
import hashlib
import os
import plistlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.prepare_release import (
    APP_NAME,
    ReleaseError,
    ReleasePaths,
    ReleasePreparer,
    insert_changelog_release,
    normalize_version,
    replace_makefile_version,
)
from scripts import prepare_release


class PrepareReleaseTests(unittest.TestCase):
    def test_normalize_version_accepts_plain_or_tagged_versions(self):
        self.assertEqual(normalize_version("1.2.3"), ("1.2.3", "v1.2.3"))
        self.assertEqual(normalize_version("v1.2.3beta"), ("1.2.3beta", "v1.2.3beta"))

    def test_replace_makefile_version_updates_only_version_line(self):
        text = "APP_NAME := 时间剪史\nVERSION  := 1.2.2beta\nBUNDLE := app\n"

        updated = replace_makefile_version(text, "1.2.3")

        self.assertIn("VERSION  := 1.2.3", updated)
        self.assertIn("APP_NAME := 时间剪史", updated)

    def test_insert_changelog_release_adds_new_section_before_existing_releases(self):
        text = "# Changelog\n\nIntro\n\n## [v1.2.2beta] - 2026-06-08\n"

        updated = insert_changelog_release(
            text,
            "1.2.3",
            dt.date(2026, 6, 8),
            "abc123",
        )

        self.assertLess(updated.index("## [v1.2.3]"), updated.index("## [v1.2.2beta]"))
        self.assertIn("SHA256：`abc123`", updated)

    def test_prepare_with_existing_dmg_updates_release_files_and_archives_old_release(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "releases").mkdir()
            (root / "Makefile").write_text(
                "APP_NAME := 时间剪史\nVERSION  := 1.2.2beta\n",
                encoding="utf-8",
            )
            (root / "CHANGELOG.md").write_text(
                "# Changelog\n\nIntro\n\n## [v1.2.2beta] - 2026-06-08\n",
                encoding="utf-8",
            )
            root_dmg = root / f"{APP_NAME}_v1.2.3.dmg"
            root_dmg.write_bytes(b"new dmg")
            old_release = root / "releases" / f"{APP_NAME}_v1.2.3.dmg"
            old_release.write_bytes(b"old dmg")

            result = ReleasePreparer(
                ReleasePaths(root),
                skip_tests=True,
                skip_build=True,
                today=dt.date(2026, 6, 8),
                timestamp="20260608-120000",
            ).prepare("1.2.3")

            expected_hash = hashlib.sha256(b"new dmg").hexdigest()
            self.assertEqual(result.checksum, expected_hash)
            self.assertEqual(result.dmg.read_bytes(), b"new dmg")
            self.assertTrue((root / "releases" / "archive" / f"{APP_NAME}_v1.2.3-20260608-120000.dmg").exists())
            self.assertIn("VERSION  := 1.2.3", (root / "Makefile").read_text(encoding="utf-8"))
            self.assertIn(expected_hash, result.checksum_file.read_text(encoding="utf-8"))
            self.assertIn("时间剪史 v1.2.3", result.release_notes.read_text(encoding="utf-8"))
            self.assertIn("## [v1.2.3] - 2026-06-08", (root / "CHANGELOG.md").read_text(encoding="utf-8"))

    def test_prepare_preflight_does_not_change_makefile_when_release_notes_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "Makefile").write_text(
                "APP_NAME := 时间剪史\nVERSION  := 1.2.2beta\n",
                encoding="utf-8",
            )
            (root / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")
            (root / "docs" / "RELEASE_NOTES_v1.2.3.md").write_text("exists", encoding="utf-8")

            with self.assertRaisesRegex(Exception, "发布说明已存在"):
                ReleasePreparer(ReleasePaths(root), skip_tests=True, skip_build=True).prepare("1.2.3")

            self.assertIn("VERSION  := 1.2.2beta", (root / "Makefile").read_text(encoding="utf-8"))

    def test_prepare_rolls_back_makefile_when_dmg_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "Makefile").write_text(
                "APP_NAME := 时间剪史\nVERSION  := 1.2.2beta\n",
                encoding="utf-8",
            )
            (root / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")

            with self.assertRaisesRegex(Exception, "没有找到 DMG"):
                ReleasePreparer(ReleasePaths(root), skip_tests=True, skip_build=True).prepare("1.2.3")

            self.assertIn("VERSION  := 1.2.2beta", (root / "Makefile").read_text(encoding="utf-8"))

    def test_prepare_rolls_back_release_files_when_late_step_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "releases").mkdir()
            (root / "Makefile").write_text(
                "APP_NAME := 时间剪史\nVERSION  := 1.2.2beta\n",
                encoding="utf-8",
            )
            (root / "CHANGELOG.md").write_text("# Changelog\n\nold changelog\n", encoding="utf-8")
            root_dmg = root / f"{APP_NAME}_v1.2.3.dmg"
            root_dmg.write_bytes(b"new dmg")
            release_dmg = root / "releases" / f"{APP_NAME}_v1.2.3.dmg"
            release_dmg.write_bytes(b"old dmg")
            checksum_file = root / "releases" / f"{APP_NAME}_v1.2.3.dmg.sha256"
            checksum_file.write_text("old checksum\n", encoding="utf-8")

            original_insert_changelog_release = prepare_release.insert_changelog_release

            def failing_insert_changelog_release(text, version, today, checksum):
                raise RuntimeError("late changelog failure")

            prepare_release.insert_changelog_release = failing_insert_changelog_release
            try:
                with self.assertRaisesRegex(RuntimeError, "late changelog failure"):
                    ReleasePreparer(
                        ReleasePaths(root),
                        skip_tests=True,
                        skip_build=True,
                        today=dt.date(2026, 6, 8),
                        timestamp="20260608-120000",
                    ).prepare("1.2.3")
            finally:
                prepare_release.insert_changelog_release = original_insert_changelog_release

            self.assertEqual(release_dmg.read_bytes(), b"old dmg")
            self.assertEqual(checksum_file.read_text(encoding="utf-8"), "old checksum\n")
            self.assertFalse((root / "docs" / "RELEASE_NOTES_v1.2.3.md").exists())
            self.assertEqual((root / "CHANGELOG.md").read_text(encoding="utf-8"), "# Changelog\n\nold changelog\n")
            self.assertIn("VERSION  := 1.2.2beta", (root / "Makefile").read_text(encoding="utf-8"))

    def test_prepare_runs_tests_builds_and_verifies_info_plist(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "Makefile").write_text(
                "APP_NAME := 时间剪史\nVERSION  := 1.2.2beta\n",
                encoding="utf-8",
            )
            (root / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")
            commands = []

            def runner(command, cwd):
                commands.append(list(command))
                if list(command) == ["make", "dmg"]:
                    root_dmg = root / f"{APP_NAME}_v1.2.3.dmg"
                    root_dmg.write_bytes(b"dmg")
                    info_plist = root / f"{APP_NAME}.app" / "Contents" / "Info.plist"
                    info_plist.parent.mkdir(parents=True)
                    # 真包里 Contents/MacOS/<CFBundleExecutable> 一定存在，闸门会检查它。
                    executable = info_plist.parent / "MacOS" / "ClipboardHistoryApp"
                    executable.parent.mkdir(parents=True)
                    executable.write_bytes(b"fake binary")
                    info_plist.write_bytes(
                        plistlib.dumps({
                            "CFBundleShortVersionString": "1.2.3",
                            # 真的包一定有这个键；启动闸门靠它找到可执行文件。
                            "CFBundleExecutable": "ClipboardHistoryApp",
                        })
                    )

            result = ReleasePreparer(
                ReleasePaths(root),
                today=dt.date(2026, 6, 8),
                runner=runner,
                disassembly_reader=lambda executable: "",
            ).prepare("1.2.3")

            self.assertEqual(
                commands,
                [
                    ["swift", "test", "--package-path", "ClipboardHistory"],
                    [sys.executable, "-m", "unittest", "discover", "-s", "scripts/tests"],
                    ["make", "dmg"],
                ],
            )
            self.assertEqual(result.info_plist, root / f"{APP_NAME}.app" / "Contents" / "Info.plist")
            self.assertIn("VERSION  := 1.2.3", (root / "Makefile").read_text(encoding="utf-8"))

    def test_prepare_refuses_a_bundle_that_cannot_launch(self):
        """启动闸门必须真的接在 prepare() 里 —— 只定义不调用等于没有。

        产物形状照抄 D-029：包能构建、签名能过、Info.plist 版本也对，
        但二进制里 AppDelegate 还留着 -init 桩 ⇒ 用户一打开就闪退。这种包不许出门。
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "Makefile").write_text(
                "APP_NAME := 时间剪史\nVERSION  := 1.2.2beta\n", encoding="utf-8"
            )
            (root / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")

            def runner(command, cwd):
                if list(command) == ["make", "dmg"]:
                    (root / f"{APP_NAME}_v1.2.3.dmg").write_bytes(b"dmg")
                    contents = root / f"{APP_NAME}.app" / "Contents"
                    contents.mkdir(parents=True)
                    (contents / "Info.plist").write_bytes(plistlib.dumps({
                        "CFBundleShortVersionString": "1.2.3",
                        "CFBundleExecutable": "ClipboardHistoryApp",
                    }))
                    executable = contents / "MacOS" / "ClipboardHistoryApp"
                    executable.parent.mkdir()
                    executable.write_bytes(b"fake binary")

            stub = LaunchGateTests.ARM64_STUB_BLOCK.replace(
                '"ClipboardHistoryApp.ChineseSelectableNSTextView"',
                '"ClipboardHistoryApp.AppDelegate"',
            )
            with self.assertRaises(ReleaseError) as caught:
                ReleasePreparer(
                    ReleasePaths(root),
                    today=dt.date(2026, 6, 8),
                    runner=runner,
                    disassembly_reader=lambda executable: stub,
                ).prepare("1.2.3")

            message = str(caught.exception)
            self.assertIn("ClipboardHistoryApp.AppDelegate", message, message)
            self.assertIn("VERSION  := 1.2.2beta", (root / "Makefile").read_text(encoding="utf-8"),
                          "闸门拦下之后必须回滚 VERSION，别留下改了一半的工作区")
            self.assertFalse((root / "docs" / "RELEASE_NOTES_v1.2.3.md").exists())

    def test_prepare_refuses_dmg_that_make_dmg_did_not_rewrite(self):
        """`make dmg` 退出码为 0 但没重写 DMG ⇒ 必须停下并回滚。

        这是发布链路上最危险的一种失败：拿到的是上一版的字节，
        而脚本会给它算出一个"看起来正确"的 sha256 并写进 CHANGELOG。
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "Makefile").write_text(
                "APP_NAME := 时间剪史\nVERSION  := 1.2.2beta\n", encoding="utf-8"
            )
            (root / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")
            stale = root / f"{APP_NAME}_v1.2.3.dmg"
            stale.write_bytes(b"stale-bytes")
            old_ns = 946_684_800_000_000_000  # 2000-01-01
            os.utime(stale, ns=(old_ns, old_ns))

            def runner(command, cwd):
                info_plist = root / f"{APP_NAME}.app" / "Contents" / "Info.plist"
                info_plist.parent.mkdir(parents=True, exist_ok=True)
                info_plist.write_bytes(plistlib.dumps({"CFBundleShortVersionString": "1.2.3"}))

            with self.assertRaises(prepare_release.ReleaseError) as ctx:
                ReleasePreparer(
                    ReleasePaths(root), today=dt.date(2026, 6, 8), runner=runner
                ).prepare("1.2.3")

            self.assertIn("mtime", str(ctx.exception))
            self.assertIn(
                "VERSION  := 1.2.2beta", (root / "Makefile").read_text(encoding="utf-8")
            )
            self.assertFalse((root / "releases" / f"{APP_NAME}_v1.2.3.dmg").exists())
            self.assertEqual(stale.read_bytes(), b"stale-bytes")


    def test_child_environment_matches_the_selected_toolchain(self):
        """发布脚本交给子进程的 SDKROOT 必须与编译器同源。

        本机真实事故（2026-10-09）：`/usr/bin/python3` 会给整棵进程树注入 CLT 的
        `SDKROOT`，而 `swift` 来自 Xcode ⇒ `swift test` 子进程报
        "this SDK is not supported by the compiler"，整条发布链在第一步就断，
        而同一条命令在 shell 里手跑却是好的。
        """
        probe = subprocess.run(
            ["xcrun", "--sdk", "macosx", "--show-sdk-path"], capture_output=True, text=True
        )
        resolved = probe.stdout.strip()
        if not resolved:
            self.skipTest("本机没有可用的 xcrun SDK 解析")

        env = prepare_release.build_child_environment()
        self.assertEqual(env.get("SDKROOT"), resolved,
                         "子进程 SDK 必须等于 xcrun 解析出来的那个，否则编译必然失败")

        dev = subprocess.run(["xcode-select", "-p"], capture_output=True, text=True).stdout.strip()
        if dev and "CommandLineTools" not in dev:
            self.assertNotIn("CommandLineTools/SDKs", env.get("SDKROOT", ""),
                             "开发者目录是 Xcode，子进程却拿到 CLT 的 SDK —— 就是本次事故本身")


class LaunchGateTests(unittest.TestCase):
    """R2-21：发布链路里"能不能启动"这一关。

    夹具是 `otool -tvV -arch arm64` 的**真实输出**（取自 v1.4.8 候选包，逐字照抄），
    不是凭印象编的 —— arm64 与 x86_64 的桩形状本来就不同（`bl`+`brk` 对 `callq`+`ud2`，
    且 className 字面量离调用点有二十几行），编的夹具会测出一个"绿着的死闸门"。
    """

    # 真取自 ClipboardHistoryApp 的 arm64 切片（ChineseSelectableNSTextView 的桩块）。
    ARM64_STUB_BLOCK = """000000010001ce18	add	x29, sp, #0x30
000000010001ce1c	adrp	x0, 510 ; 0x10021a000
000000010001ce20	add	x0, x0, #0x3e0 ; literal pool for: "init(frame:)"
000000010001ce24	adrp	x2, 510 ; 0x10021a000
000000010001ce28	add	x2, x2, #0x330 ; literal pool for: "ClipboardHistoryApp/ChineseTextContextMenu.swift"
000000010001ce2c	adrp	x5, 510 ; 0x10021a000
000000010001ce30	add	x5, x5, #0x3b0 ; literal pool for: "ClipboardHistoryApp.ChineseSelectableNSTextView"
000000010001ce34	movi.2d	v4, #0000000000000000
000000010001ce38	str	q4, [sp, #0x10]
000000010001ce3c	str	q4, [sp, #0x20]
000000010001ce40	mov	w9, #0xd
000000010001ce44	str	x9, [x10]
000000010001ce48	mov	x1, x9
000000010001ce4c	mov	w9, #0x30
000000010001ce50	mov	x3, x9
000000010001ce54	mov	w4, #0x2
000000010001ce58	bl	_$ss25_unimplementedInitializer9className04initD04file4line6columns5NeverOs12StaticStringV_A2JS2utFySRys5UInt8VGXEfU_yAMXEfU_
000000010001ce5c	brk	#0x1"""

    def test_reads_the_class_from_a_real_arm64_stub_block(self):
        found = prepare_release.classes_with_unimplemented_initializers(self.ARM64_STUB_BLOCK)
        self.assertEqual(found, {"ClipboardHistoryApp.ChineseSelectableNSTextView"},
                         "读不出类名，闸门就会在坏产物上报干净")

    def test_file_path_literal_is_not_mistaken_for_a_class(self):
        found = prepare_release.classes_with_unimplemented_initializers(self.ARM64_STUB_BLOCK)
        self.assertNotIn("ChineseTextContextMenu.swift", found,
                         "文件路径字面量含 .swift，按'带点的字符串'算类名会在正确产物上误报")

    def test_app_delegate_stub_blocks_the_release_and_the_current_shape_does_not(self):
        broken = self.ARM64_STUB_BLOCK.replace(
            '"ClipboardHistoryApp.ChineseSelectableNSTextView"', '"ClipboardHistoryApp.AppDelegate"'
        )
        self.assertEqual(prepare_release.find_launch_blockers(broken),
                         ["ClipboardHistoryApp.AppDelegate"],
                         "D-029 那个形状必须被拦下：桩在 AppDelegate 上 = 一打开就闪退")
        self.assertEqual(prepare_release.find_launch_blockers(self.ARM64_STUB_BLOCK), [],
                         "良性桩（只在 Swift 侧显式构造的类型）不该挡住发布")

    def test_built_bundle_carries_no_app_delegate_stub(self):
        """端到端：真读一次仓库里已构建的包。这条就是 D-029 当时缺的那一关。"""
        root = Path(__file__).resolve().parents[2]
        executable = root / "时间剪史.app" / "Contents" / "MacOS" / "ClipboardHistoryApp"
        if not executable.exists():
            self.skipTest("仓库根目录没有已构建的 .app（先跑 make bundle 再验）")
        completed = subprocess.run(
            ["otool", "-tvV", "-arch", "arm64", str(executable)],
            capture_output=True, text=True, env=prepare_release.build_child_environment(),
        )
        self.assertEqual(completed.returncode, 0, completed.stderr[:200])
        stubbed = prepare_release.classes_with_unimplemented_initializers(completed.stdout)
        self.assertNotIn("ClipboardHistoryApp.AppDelegate", stubbed,
                         "包里的 AppDelegate 仍有 -init 桩 —— 用户一打开就闪退（D-029）")
        self.assertTrue(stubbed,
                        "一个桩都没读到 = 解析器瞎了（这个包按实测应有 3 个良性桩），别把死闸门当守卫")



class FrameBaselineSnapshotOnReleaseTests(unittest.TestCase):
    """§3 C-2：发布流程必须把帧基线冻结成**逐版本**的一份。

    只有一份可以随时 `update` 的工作基线，"和上一版比"就是一句空话 ——
    "上一版"实际等于"上一次有人记得 update 的时候"。所以这一步挂在发布流程里，
    而不是写在一句"记得跑一下"里。
    """

    def _root_with_working_manifest(self, root: str) -> Path:
        docs = Path(root) / "docs"
        docs.mkdir(parents=True, exist_ok=True)
        (docs / "frame_baseline.json").write_text(
            '{"schema": 1, "count": 2, "frames": {"a.png": "1", "b.png": "2"}}\n',
            encoding="utf-8")
        return docs

    def test_release_freezes_a_versioned_baseline(self):
        with tempfile.TemporaryDirectory() as root:
            docs = self._root_with_working_manifest(root)
            preparer = ReleasePreparer(ReleasePaths(root), skip_tests=True, skip_build=True)
            target = preparer._snapshot_frame_baseline("1.4.9")
            self.assertEqual(target, str(docs / "frame_baselines" / "v1.4.9.json"))
            written = Path(target).read_text(encoding="utf-8")
            self.assertIn("a.png", written)

    def test_a_real_release_freezes_the_baseline_last(self):
        """走完整的 `prepare()`，而不是只单测那个方法。

        这条存在的理由有两半：
        1. 它证明冻结**确实发生在发布流程里**（被调到、文件落在版本名下），
           而不是只在我的单元里被调到 —— 后者证明不了接线。
        2. 顺带钉住"它是最后一步"：预检失败的那一路一个版本基线都不该留下，
           否则"没发成功的版本"会变成下一版的比对基准。
           （原先我在 except 里写了一段清理，那条路径其实永远走不到 ——
           把顺序改对之后它就不需要存在了，见 D-047 的补记。）
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir(parents=True)
            (root / "releases").mkdir()
            (root / "Makefile").write_text(
                "APP_NAME := 时间剪史\nVERSION  := 1.2.2beta\n", encoding="utf-8")
            (root / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")
            (root / "docs" / "frame_baseline.json").write_text(
                '{"schema": 1, "count": 1, "frames": {"a.png": "1"}}\n', encoding="utf-8")
            (root / ("%s_v1.2.3.dmg" % APP_NAME)).write_bytes(b"dmg")

            ReleasePreparer(ReleasePaths(root), skip_tests=True, skip_build=True).prepare("1.2.3")
            frozen = root / "docs" / "frame_baselines" / "v1.2.3.json"
            self.assertTrue(frozen.exists(), "发布走完了却没冻结基线：下一版就没有可比的对象")
            self.assertIn("a.png", frozen.read_text(encoding="utf-8"))

            # 同一版本再发一次会被预检挡住（发布说明已存在）—— 那条路上不许留下新的基线
            before = sorted(p.name for p in (root / "docs" / "frame_baselines").iterdir())
            with self.assertRaises(Exception):
                ReleasePreparer(ReleasePaths(root), skip_tests=True, skip_build=True).prepare("1.2.3")
            after = sorted(p.name for p in (root / "docs" / "frame_baselines").iterdir())
            self.assertEqual(before, after, "失败的发布留下了帧基线")

    def test_no_working_manifest_means_no_snapshot(self):
        with tempfile.TemporaryDirectory() as root:
            preparer = ReleasePreparer(ReleasePaths(root), skip_tests=True, skip_build=True)
            self.assertIsNone(preparer._snapshot_frame_baseline("2.0.0"),
                              "没有工作基线时不该凭空造一个版本基线")

    def test_the_step_is_announced_before_it_runs(self):
        with tempfile.TemporaryDirectory() as root:
            self._root_with_working_manifest(root)
            steps = ReleasePreparer(ReleasePaths(root), skip_tests=True, skip_build=True).planned_steps("1.4.9")
            self.assertTrue(any("frame_baselines" in step for step in steps),
                            "冻结基线这一步要出现在计划里，dry-run 时用户才看得见它会动哪些文件")


if __name__ == "__main__":
    unittest.main()
