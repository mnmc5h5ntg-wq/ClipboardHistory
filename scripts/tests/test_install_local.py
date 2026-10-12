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
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "install_local.sh"
APP_NAME = "时间剪史"
BINARY = "ClipboardHistoryApp"

def file_sha(path: Path) -> str:
    """和脚本里的 `sha_of()` 同义：整文件 sha256。测试要自己算一遍，不能只信脚本打印的。"""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


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

    def test_it_really_notices_the_running_copy_under_a_cjk_path(self):
        """"要换的那一份在不在跑"必须真的认得出来 —— 认不出来会连锁假失败。

        这一条是被一次真实失败逼出来的（2026-10-13）：脚本原来用 `lsof` 取进程可执行路径，
        而 CJK 在 lsof/ps 输出里是八进制转义串；就算换成逐字返回的 `proc_path.py`，
        比较式 `${path%Contents/MacOS/…}` 还会**留下一个尾斜杠**，于是永远不相等 ⇒
        脚本判定"没在跑" ⇒ 跳过退出旧版 ⇒ 冒烟闸门被第二实例守卫假报成失败，
        报的还是"闸门没过"，根因完全看不出来。

        沙箱里造一个**真在跑的**同名实例（路径含中文、二进制名就是产品那个），
        要求脚本走"检测到 → 等它退出"那条分支，而不是"没在跑"。
        夹具进程自己 1 秒后退出：这里测的是**识别**，不是 osascript 的退出通道
        （一个假 App 不会响应 AppleScript，硬测会把测试变成测 macOS）。
        """
        sandbox_dest = self.tmp / "cjk-dest"
        running_bundle = make_bundle(sandbox_dest, "RUNNING_OLD")
        exe = running_bundle / "Contents" / "MacOS" / BINARY
        src = exe.parent / "autoexit.c"
        src.write_text("#include <unistd.h>\nint main(void){sleep(1);return 0;}\n", encoding="utf-8")
        compiler = shutil.which("cc") or shutil.which("clang")
        if compiler is None:
            raise unittest.SkipTest("no compiler for the fixture")
        built = subprocess.run([compiler, "-o", str(exe), str(src)],
                               capture_output=True, text=True, timeout=180)
        if built.returncode != 0:
            # 默认 SDK 在这台机器上链接不过（tapi 报 arm64e.x1），逐个 SDK 重试。
            sdk_root = Path("/Library/Developer/CommandLineTools/SDKs")
            for sdk in sorted(sdk_root.glob("MacOSX*.sdk"), reverse=True):
                built = subprocess.run([compiler, "-isysroot", str(sdk), "-o", str(exe), str(src)],
                                       capture_output=True, text=True, timeout=180)
                if built.returncode == 0:
                    break
            if built.returncode != 0:
                print("\n[跳过原因] 夹具编不出来：%s" % built.stderr.strip().splitlines()[-1:])
                raise unittest.SkipTest("no usable SDK for the fixture")
        exe.chmod(0o755)

        proc = subprocess.Popen([str(exe)])
        self.addCleanup(lambda: (proc.kill(), proc.wait()))
        time.sleep(0.2)
        self.assertIsNone(proc.poll(), "夹具没起来，这条测试会是空跑")

        out = subprocess.run(["bash", str(SCRIPT), "--yes", "--no-build", "--skip-smoke",
                              "--no-launch", f"--bundle={self.new_bundle}",
                              f"--dest={sandbox_dest}", f"--label=cjk-running-{os.getpid()}"],
                             capture_output=True, text=True, timeout=180)
        self.assertIn("检测到要替换的实例 pid=", out.stdout,
                      "脚本没认出'要换的那一份正在跑'（走了'没在跑'分支）："
                      + out.stdout[-500:] + out.stderr[-300:])
        # 沙箱目标**不许**发退出指令：这条判据的存在理由是 2026-10-13 的一次真实误伤 ——
        # `osascript tell application "<名字>"` 是按名字全局发的，跑沙箱自检时
        # 把用户 /Applications 里那份真 App 退掉了。
        self.assertIn("沙箱验证）⇒ 不发退出指令", out.stdout,
                      "沙箱安装仍然去给 App 发退出指令：" + out.stdout[-400:])
        self.assertNotIn("优雅退出正在跑的", out.stdout)
        self.assertEqual(out.returncode, 0, out.stdout[-500:] + out.stderr[-500:])
        installed_exe = sandbox_dest / f"{APP_NAME}.app" / "Contents" / "MacOS" / BINARY
        self.assertEqual(file_sha(installed_exe), file_sha(self.new_bundle / "Contents" / "MacOS" / BINARY),
                         "认出了在跑的实例，最后装的却不是新那份")


class ProcPathTest(unittest.TestCase):
    """`scripts/proc_path.py`：换装脚本"按身份认进程"的唯一可靠入口。

    这条测试是被一次真实失败逼出来的：`install_local.sh` 用 `lsof -p <pid> -Fn` 取可执行
    路径去和 `/Applications/时间剪史.app/…` 比，而 App 名字是中文 —— lsof 把非 ASCII
    转义成 `\\346\\227\\266…`，比较永远不相等，脚本于是误判"没在跑"、跳过退出旧版，
    下一步冒烟闸门被第二实例守卫假报成失败（报的还是"闸门没过"，看不出根因在路径转义）。
    """

    PROC = ROOT / "scripts" / "proc_path.py"

    def test_reports_the_exact_path_for_a_live_process_under_a_cjk_path(self):
        tmp = Path(tempfile.mkdtemp(prefix="proc-path-test-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        # 目录名与可执行文件名都带中文，并且**故意用产品的二进制名**：
        # 这样这条测试同时覆盖"路径含 CJK"和"按名字筛进程"两件事。
        exe_dir = tmp / f"{APP_NAME}.app" / "Contents" / "MacOS"
        exe_dir.mkdir(parents=True)
        exe = exe_dir / BINARY
        self.build_sleeper(exe)

        proc = subprocess.Popen([str(exe)])
        self.addCleanup(lambda: (proc.kill(), proc.wait()))
        deadline = time.time() + 5
        while proc.poll() is not None and time.time() < deadline:
            time.sleep(0.1)
        self.assertIsNone(proc.poll(),
                          "夹具进程没活下来（编译器/签名问题？），下面所有断言都是空跑")

        out = subprocess.run([sys.executable, str(self.PROC), str(proc.pid)],
                             capture_output=True, text=True, timeout=30)
        self.assertEqual(out.returncode, 0, out.stderr[-300:])
        # `proc_pidpath` 给的是**解析过符号链接**的路径，而 macOS 上 `/var` → `/private/var`，
        # 所以比较对象必须是 realpath —— 不是 proc_path 的错，是夹具路径本来就有两个名字。
        self.assertEqual(out.stdout.strip(), os.path.realpath(str(exe)),
                         "proc_path 没有把路径逐字打出来（CJK 被转义或截断了）")
        self.assertIn(APP_NAME, out.stdout, "返回的路径里连 App 名都不见了，说明被转义了")
        # 反面对照（只报数不断言）：`ps` 的输出确实是转义过的 —— 这正是换装脚本原来读不到
        # 路径的根因。不在这里断言它，是因为"哪个工具怎么转义"不是我们要钉住的契约，
        # 我们要钉的是"proc_path 逐字返回"。
        ps_out = subprocess.run(["ps", "-o", "comm=", "-p", str(proc.pid)],
                                capture_output=True, text=True).stdout.strip()
        if APP_NAME not in ps_out:
            print("\n[对照] ps 把 CJK 路径转义成： %s" % ps_out)

    def build_sleeper(self, exe: Path):
        """编一个 `pause()` 挂着的小程序，作为"活着的、路径含中文的进程"。

        为什么不用 `shutil.copy('/bin/sleep')`：Apple 的系统二进制受签名卷绑定，
        复制到别处会被内核直接 SIGKILL（实测 `poll() == -9`），Xcode 自带的 python3 也一样
        （SIGABRT）—— 夹具根本活不下来，测试就会变成"断言一个死进程的路径"。

        为什么要挨个试 SDK：这台机器的 CLT 默认 SDK（MacOSX27.0）在链接期报
        `tapi error: malformed file … unknown architecture arm64e.x1-macos`，
        而换一个 SDK 就能编（实测 26.5 可以）。所以这里"先按默认编，失败就逐个 SDK 重试"，
        全都不行就跳过并**打印原因**，不许静默变成"少验了一项"。
        """
        compiler = shutil.which("cc") or shutil.which("clang")
        if compiler is None:
            print("\n[跳过原因] 机器上没有 cc/clang，这条夹具编不出来")
            raise unittest.SkipTest("no compiler available for the fixture")
        src = exe.parent / "sleeper.c"
        src.write_text("#include <unistd.h>\nint main(void){pause();return 0;}\n", encoding="utf-8")
        attempts = [[compiler, "-o", str(exe), str(src)]]
        sdk_root = Path("/Library/Developer/CommandLineTools/SDKs")
        if sdk_root.is_dir():
            for sdk in sorted(sdk_root.glob("MacOSX*.sdk"), reverse=True):
                attempts.append([compiler, "-isysroot", str(sdk), "-o", str(exe), str(src)])
        errors = []
        for argv in attempts:
            built = subprocess.run(argv, capture_output=True, text=True, timeout=180)
            if built.returncode == 0 and exe.exists():
                exe.chmod(0o755)
                return
            errors.append("%s :: %s" % (" ".join(argv[1:4]), built.stderr.strip().splitlines()[-1:]))
        print("\n[跳过原因] 所有 SDK 都编不出来：%s" % errors[-3:])
        raise unittest.SkipTest("no usable SDK/clang combination for the fixture")

    def test_bogus_pid_fails_loudly_instead_of_printing_an_empty_line(self):
        """拿不到路径时必须非零退出：空字符串在调用方那里长得像"这个进程不是我要换的那份"。"""
        out = subprocess.run([sys.executable, str(self.PROC), "2147483646"],
                             capture_output=True, text=True, timeout=30)
        self.assertNotEqual(out.returncode, 0)
        self.assertEqual(out.stdout.strip(), "")

    def test_usage_error_on_a_non_numeric_pid(self):
        out = subprocess.run([sys.executable, str(self.PROC), "not-a-pid"],
                             capture_output=True, text=True, timeout=30)
        self.assertEqual(out.returncode, 2)


if __name__ == "__main__":
    unittest.main()
