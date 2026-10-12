"""`scripts/install_local.sh` 的自检：换装脚本的三条危险路径必须能被打红。

为什么值得给一个 shell 脚本写测试（2026-10-12）：这个脚本会**退出用户正在用的 App、
把 /Applications 里那一份移走、再放一份新的进去**。它自己出错的方式不是"报错"，
而是"看起来成功了，但用户屏幕上还是旧的"或者"新包坏了而旧包已经被移走"。
所以三条判据各自对应一种失败：

1. **预检不过就不许动现场**：包不存在时必须非零退出，且目标目录一字不变。
2. **装的那份必须等于验过的那份**：走通沙箱安装并拿到 `INSTALL_SHA_MATCH=1`。
3. **回滚要真回滚**：强制让"移动旧包之后"某一步失败，回来的必须是**原来那一份**——
   所以沙箱里的"旧包"内容要和新包**可分辨**（同一个 sha 的话，回滚什么都不做也能绿，
   这条判据就白写了：这是我自己第一版踩到的）。

沙箱靠 `--dest /tmp/... --skip-smoke --no-launch` 三个开关实现：
不启动是因为同 bundle id 的副本会被产品的第二实例守卫自退（那是守卫的正确行为，
但会让"启动后按身份认"这一步在测试里永远测不到真东西）。
"""
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "install_local.sh"
APP_NAME = "时间剪史"
BINARY = "ClipboardHistoryApp"


def make_bundle(dir_path: Path, marker: str) -> Path:
    """造一个最小但**能过 codesign 校验**的 .app，内容带一个可分辨的 marker。"""
    bundle = dir_path / f"{APP_NAME}.app"
    macos = bundle / "Contents" / "MacOS"
    macos.mkdir(parents=True, exist_ok=True)
    (bundle / "Contents" / "Info.plist").write_text(textwrap.dedent(f"""\
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0"><dict>
        <key>CFBundleExecutable</key><string>{BINARY}</string>
        <key>CFBundleIdentifier</key><string>local.selftest.install</string>
        <key>CFBundleName</key><string>{APP_NAME}</string>
        <key>CFBundlePackageType</key><string>APPL</string>
        <key>CFBundleShortVersionString</key><string>0.0-selftest</string>
        </dict></plist>
        """), encoding="utf-8")
    exe = macos / BINARY
    exe.write_text(f"#!/bin/sh\necho '{marker}'\n", encoding="utf-8")
    exe.chmod(0o755)
    subprocess.run(["codesign", "--force", "--sign", "-", str(bundle)],
                   check=True, capture_output=True)
    return bundle


def run(args, cwd=None):
    return subprocess.run(["bash", str(SCRIPT), *args], capture_output=True, text=True,
                          timeout=180, cwd=cwd)


class InstallLocalSelfTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="install-local-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.dest = self.tmp / "dest"
        self.dest.mkdir()
        self.new_bundle = make_bundle(self.tmp / "new", "NEW_BUILD")
        self.base = ["--no-build", "--skip-smoke", "--no-launch", "--yes",
                     "--bundle", str(self.new_bundle), "--dest", str(self.dest)]

    def common(self):
        return [f"--label=test-{os.getpid()}", *self.base]

    def test_missing_bundle_refuses_without_touching_target(self):
        """预检不过 ⇒ 非零退出，且目标目录里什么都没发生。"""
        before = sorted(p.name for p in self.dest.iterdir())
        proc = run(["--no-build", "--yes", "--bundle", str(self.tmp / "nope.app"),
                    "--dest", str(self.dest)])
        self.assertNotEqual(proc.returncode, 0,
                            "包不存在却退出 0 —— 这条脚本会在没装任何东西时报成功")
        self.assertIn("找不到可执行文件", proc.stderr + proc.stdout)
        self.assertEqual(sorted(p.name for p in self.dest.iterdir()), before,
                         "预检失败却动了目标目录")
        self.assertIn("ROLLED_BACK=0", proc.stdout, "没动过旧包却声称回滚了")

    def test_sandbox_install_matches_sha(self):
        proc = run(self.common())
        self.assertEqual(proc.returncode, 0, proc.stdout[-800:] + proc.stderr[-800:])
        self.assertIn("INSTALL_SHA_MATCH=1", proc.stdout)
        installed = self.dest / f"{APP_NAME}.app" / "Contents" / "MacOS" / BINARY
        self.assertTrue(installed.exists(), "报成功但目标里没有可执行文件")
        # 未启动就不算交付证明：脚本必须自己说清这一点，别让人把沙箱结果读成装机结果
        self.assertIn("不构成交付证明", proc.stdout)

    def test_failure_after_move_restores_the_original_copy(self):
        """移动旧包之后失败 ⇒ 回来的必须确实是原来那一份（内容可分辨）。"""
        old_bundle = make_bundle(self.tmp / "old", "OLD_BUILD")
        shutil.copytree(old_bundle, self.dest / f"{APP_NAME}.app", symlinks=True)
        old_exe = self.dest / f"{APP_NAME}.app" / "Contents" / "MacOS" / BINARY
        old_text = old_exe.read_text(encoding="utf-8")
        self.assertNotIn("NEW_BUILD", old_text, "沙箱没搭好：旧包内容和新包不可分辨")

        mutant = self.tmp / "mutant_install.sh"
        body = SCRIPT.read_text(encoding="utf-8")
        anchor = '[ "$staged_sha" = "$installed_sha" ] || fail "装的与验过的不是同一份，回滚"'
        self.assertEqual(body.count(anchor), 1,
                         "锚点没了：脚本里那道 sha 比对改过名/改过写法，这条自检要跟着改")
        # 只改这一行：让"装的那份 == 验的那份"必然失败，从而走回滚分支
        mutant.write_text(body.replace(anchor, '[ 1 = 2 ] || fail "强制失败（自检注入）"', 1),
                          encoding="utf-8")
        proc = subprocess.run(["bash", str(mutant), *self.common()],
                              capture_output=True, text=True, timeout=180)
        self.assertNotEqual(proc.returncode, 0, "强制失败后脚本却退出 0")
        self.assertIn("ROLLED_BACK=1", proc.stdout)
        self.assertTrue(old_exe.exists(), "回滚后目标里那份 App 没了")
        self.assertEqual(old_exe.read_text(encoding="utf-8"), old_text,
                         "回来的不是原来那一份（可能只是把失败的新包留在原地）")

    def test_dry_run_is_the_default(self):
        """默认必须是 dry-run：忘了加 --dry-run 也不该动用户的 App。"""
        proc = subprocess.run(["bash", str(SCRIPT), "--no-build",
                               "--bundle", str(self.new_bundle)],
                              capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr[-400:])
        self.assertIn("dry-run", proc.stdout)
        self.assertIn("请加 --yes", proc.stdout)


if __name__ == "__main__":
    unittest.main()
