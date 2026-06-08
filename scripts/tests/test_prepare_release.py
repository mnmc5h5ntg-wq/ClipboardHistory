import datetime as dt
import hashlib
import plistlib
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.prepare_release import (
    APP_NAME,
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
                    info_plist.write_bytes(
                        plistlib.dumps({"CFBundleShortVersionString": "1.2.3"})
                    )

            result = ReleasePreparer(
                ReleasePaths(root),
                today=dt.date(2026, 6, 8),
                runner=runner,
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


if __name__ == "__main__":
    unittest.main()
