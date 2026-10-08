import plistlib
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "make_info_plist.sh"
TEMPLATE = REPO / "ClipboardHistory" / "Resources" / "Info.plist"


class MakeInfoPlistTests(unittest.TestCase):
    """Info.plist 的生成闸必须能在不构建 App 的情况下被验证。

    以前这些校验写在 Makefile 里且每行 `|| true`：想证明它会失败，
    得先跑一次几分钟的 universal 构建，于是没人证明过。
    """

    def run_script(self, template: Path, version: str = "9.9.9", dest_name: str = "Info.plist"):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        dest = Path(tmp.name) / dest_name
        proc = subprocess.run(
            ["/bin/sh", str(SCRIPT), str(template), str(dest), version],
            capture_output=True, text=True,
        )
        return proc, dest

    def test_real_template_yields_valid_plist_with_usage_description(self):
        proc, dest = self.run_script(TEMPLATE)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        info = plistlib.loads(dest.read_bytes())
        self.assertEqual(info["CFBundleShortVersionString"], "9.9.9")
        self.assertEqual(info["CFBundleExecutable"], "ClipboardHistoryApp")
        self.assertEqual(info["CFBundlePackageType"], "APPL")
        self.assertEqual(info["NSPrincipalClass"], "NSApplication")
        self.assertEqual(info["LSMinimumSystemVersion"], "12.0")
        # R-13：没有这句话，系统会静默拒绝自动化，用户只看到"点了没反应"。
        self.assertTrue(info["NSAppleEventsUsageDescription"].strip())
        self.assertIn("系统事件", info["NSAppleEventsUsageDescription"])
        # 用途描述必须承诺"只做这一件事"，不能是万能授权口吻。
        self.assertIn("⌘V", info["NSAppleEventsUsageDescription"])

    def test_missing_usage_description_fails_the_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "template.plist"
            info = plistlib.loads(TEMPLATE.read_bytes())
            del info["NSAppleEventsUsageDescription"]
            bad.write_bytes(plistlib.dumps(info))

            proc, _ = self.run_script(bad)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("NSAppleEventsUsageDescription", proc.stderr)

    def test_unsubstituted_placeholder_is_reported_as_version_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "template.plist"
            info = plistlib.loads(TEMPLATE.read_bytes())
            info["CFBundleShortVersionString"] = "__VERSION__-dirty"
            bad.write_bytes(plistlib.dumps(info))

            proc, _ = self.run_script(bad)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("版本号不一致", proc.stderr)

    def test_missing_template_is_reported(self):
        proc, _ = self.run_script(Path("/nonexistent/Info.plist"))
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("找不到模板", proc.stderr)

    def test_wrong_argument_count_is_usage_error(self):
        proc = subprocess.run(["/bin/sh", str(SCRIPT), str(TEMPLATE)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("用法", proc.stderr)


if __name__ == "__main__":
    unittest.main()
