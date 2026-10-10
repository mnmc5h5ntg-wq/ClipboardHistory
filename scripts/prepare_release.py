#!/usr/bin/env python3
"""Prepare a local release package for 时间剪史."""

from __future__ import annotations

import argparse
import importlib.util
import datetime as dt
import hashlib
import os
import plistlib
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence


APP_NAME = "时间剪史"
MAKEFILE_VERSION_PATTERN = re.compile(r"^(VERSION\s*:=\s*).+$", re.MULTILINE)
VERSION_PATTERN = re.compile(r"^v?(\d+\.\d+(?:\.\d+)?[A-Za-z0-9._-]*)$")
CommandRunner = Callable[[Sequence[str], Path], None]
DisassemblyReader = Callable[[Path], str]


@dataclass(frozen=True)
class ReleasePaths:
    root: Path

    @property
    def makefile(self) -> Path:
        return self.root / "Makefile"

    @property
    def changelog(self) -> Path:
        return self.root / "CHANGELOG.md"

    @property
    def app_bundle(self) -> Path:
        return self.root / f"{APP_NAME}.app"

    @property
    def app_info_plist(self) -> Path:
        return self.app_bundle / "Contents" / "Info.plist"

    @property
    def docs_dir(self) -> Path:
        return self.root / "docs"

    @property
    def releases_dir(self) -> Path:
        return self.root / "releases"

    @property
    def archive_dir(self) -> Path:
        return self.releases_dir / "archive"

    def root_dmg(self, version: str) -> Path:
        return self.root / f"{APP_NAME}_v{version}.dmg"

    def release_dmg(self, version: str) -> Path:
        return self.releases_dir / f"{APP_NAME}_v{version}.dmg"

    def checksum_file(self, version: str) -> Path:
        return self.releases_dir / f"{APP_NAME}_v{version}.dmg.sha256"

    def release_notes(self, version: str) -> Path:
        return self.docs_dir / f"RELEASE_NOTES_v{version}.md"


@dataclass(frozen=True)
class ReleaseResult:
    version: str
    tag: str
    dmg: Path
    checksum_file: Path
    checksum: str
    release_notes: Path
    archived_dmg: Path | None
    info_plist: Path | None


class ReleaseError(RuntimeError):
    pass


def normalize_version(raw_version: str) -> tuple[str, str]:
    match = VERSION_PATTERN.fullmatch(raw_version.strip())
    if not match:
        raise ReleaseError("版本号格式应类似 1.2.3、v1.2.3 或 1.2.3beta。")
    version = match.group(1)
    return version, f"v{version}"


def sha256_for(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


UNIMPLEMENTED_INITIALIZER_CALL = re.compile(r"^\s*[0-9a-f]+\s+(?:bl|b|call[a-z]*)\s+\S*unimplementedInitializer")
LITERAL_POOL_STRING = re.compile(r'^.*literal pool for: "([^"]*)"$')
MODULE_CLASS_NAME = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*\.[A-Za-z_$][A-Za-z0-9_$]*$")

# 只有"会被 ObjC 元类型构造"的类才是致命的：AppDelegate 由 SwiftUI 的
# @NSApplicationDelegateAdaptor(AppDelegate.self) 通过 -init 创建，桩一命中就闪退。
LAUNCH_CRITICAL_CLASSES = ("ClipboardHistoryApp.AppDelegate",)


def classes_with_unimplemented_initializers(disassembly: str) -> set[str]:
    """从 `otool -tvV` 的输出里挑出"带未实现初始化器桩"的类名。

    两个架构的桩形状不一样，都是实测：

        x86_64:  leaq ...  ## literal pool for: "ClipboardHistoryApp.Coordinator"
                 callq _$ss25_unimplementedInitializer...
        arm64 :  add  x5, x5, #0x3b0 ; literal pool for: "ClipboardHistoryApp.ChineseSelectableNSTextView"
                 ...（中间还有一串 mov）
                 bl   _$ss25_unimplementedInitializer...
                 brk  #0x1

    arm64 里 className 的字面量离 `bl` 有二十几行，所以**不能用固定小窗口往前找** ——
    那样会在真正坏掉的产物上报"干净"，一把永远绿的假闸门比没有闸门更坏。
    这里改成按块扫：两条桩调用之间的所有字面量里，取最后一条形如 `Module.Class` 的。
    文件路径那条（`ClipboardHistoryApp/ChineseTextContextMenu.swift`，含 `/`）必须排除，
    否则它会被当成类名，检查在正确产物上也会误报。
    """
    lines = disassembly.splitlines()
    call_indexes = [index for index, line in enumerate(lines) if UNIMPLEMENTED_INITIALIZER_CALL.search(line)]
    found: set[str] = set()
    for position, call_index in enumerate(call_indexes):
        block_start = 0 if position == 0 else call_indexes[position - 1] + 1
        nearest_class: str | None = None
        for previous in lines[block_start:call_index]:
            match = LITERAL_POOL_STRING.search(previous)
            if match and MODULE_CLASS_NAME.match(match.group(1)):
                nearest_class = match.group(1)
        if nearest_class:
            found.add(nearest_class)
    return found


def read_disassembly(executable: Path) -> str:
    """跑 `otool -tvV` 读一个二进制的反汇编（arm64 切片）。

    单独成函数是为了可注入：发布脚本的测试用假产物，真机跑时读真包。
    """
    completed = subprocess.run(
        ["otool", "-tvV", "-arch", "arm64", str(executable)],
        capture_output=True,
        text=True,
        env=build_child_environment(),
    )
    if completed.returncode != 0:
        raise ReleaseError(
            f"otool 反汇编失败（退出码 {completed.returncode}）："
            f"{completed.stderr.strip()[:200] or '无 stderr'}"
        )
    return completed.stdout


def find_launch_blockers(disassembly: str,
                         critical: Sequence[str] = LAUNCH_CRITICAL_CLASSES) -> list[str]:
    """返回"有 -init 桩且必须由 ObjC 构造"的类名列表；空列表才允许发布。"""
    stubbed = classes_with_unimplemented_initializers(disassembly)
    return sorted(name for name in critical if name in stubbed)


def replace_makefile_version(text: str, version: str) -> str:
    if not MAKEFILE_VERSION_PATTERN.search(text):
        raise ReleaseError("Makefile 中没有找到 VERSION := ... 行。")
    return MAKEFILE_VERSION_PATTERN.sub(rf"\g<1>{version}", text, count=1)


def insert_changelog_release(text: str, version: str, today: dt.date, checksum: str) -> str:
    heading = f"## [v{version}]"
    if heading in text:
        return text

    release_block = f"""## [v{version}] - {today.isoformat()}

### Added

- 待补充本次新增功能。

### Changed

- 待补充本次改进内容。

### Fixed

- 待补充本次修复内容。

### Release

- DMG：`releases/{APP_NAME}_v{version}.dmg`
- SHA256：`{checksum}`

"""
    first_release = re.search(r"^## \[", text, flags=re.MULTILINE)
    if first_release:
        return text[: first_release.start()] + release_block + text[first_release.start() :]
    return text.rstrip() + "\n\n" + release_block


def render_release_notes(version: str, today: dt.date, checksum: str) -> str:
    return f"""# 时间剪史 v{version}

这是 v{version} 的发布说明草稿。正式发布前，请把下面的占位内容替换成本轮真实改动。

## 本次更新

- 待补充本次新增功能。
- 待补充本次体验或架构改进。
- 待补充本次修复的问题。

## 验证结果

- 构建 App：待确认。
- 生成 DMG：`releases/{APP_NAME}_v{version}.dmg`
- SHA256：`{checksum}`
- 发布日期：{today.isoformat()}

## 兼容性说明

- 最低系统：macOS 12 Monterey。
- 支持架构：Intel + Apple Silicon。
- 当前流程使用本地 ad-hoc 签名；如未做 Apple 公证，首次打开仍可能需要手动允许。
"""


def build_child_environment() -> dict[str, str]:
    """给子进程一套与编译器一致的 SDK 环境。

    本机实测（2026-10-09）：`/usr/bin/python3` 会主动给它的整棵进程树注入
    `SDKROOT=/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk`，连 `env -u SDKROOT` 都去不掉；
    而 `swift` 编译器来自 Xcode。结果：脚本里任何 `swift …` 子进程都报
    "this SDK is not supported by the compiler" 并在第一步就把发布链打断 ——
    同一条命令在 shell 里手动跑却是好的。所以这里显式把 SDKROOT 设成 `xcrun` 解析出来的那个，
    让"能不能编译"不再取决于脚本是被谁启动的。
    """
    env = dict(os.environ)
    try:
        resolved = subprocess.run(
            ["xcrun", "--sdk", "macosx", "--show-sdk-path"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        resolved = ""
    if resolved:
        env["SDKROOT"] = resolved
    else:
        env.pop("SDKROOT", None)
    return env


class ReleasePreparer:
    def __init__(
        self,
        paths: ReleasePaths,
        *,
        dry_run: bool = False,
        skip_tests: bool = False,
        skip_build: bool = False,
        force: bool = False,
        today: dt.date | None = None,
        timestamp: str | None = None,
        runner: CommandRunner | None = None,
        disassembly_reader: DisassemblyReader | None = None,
    ) -> None:
        self.paths = paths
        self.dry_run = dry_run
        self.skip_tests = skip_tests
        self.skip_build = skip_build
        self.force = force
        self.today = today or dt.date.today()
        self.timestamp = timestamp or dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        self.runner = runner or self._default_runner
        self.disassembly_reader = disassembly_reader or read_disassembly

    def prepare(self, raw_version: str) -> ReleaseResult:
        version, tag = normalize_version(raw_version)
        self._ensure_project_root()

        root_dmg = self.paths.root_dmg(version)
        release_dmg = self.paths.release_dmg(version)
        checksum_file = self.paths.checksum_file(version)
        release_notes = self.paths.release_notes(version)
        original_makefile_text = self.paths.makefile.read_text(encoding="utf-8")
        original_changelog_text = self.paths.changelog.read_text(encoding="utf-8")
        original_release_notes_text = release_notes.read_text(encoding="utf-8") if release_notes.exists() else None
        original_checksum_text = checksum_file.read_text(encoding="utf-8") if checksum_file.exists() else None
        had_release_dmg = release_dmg.exists()
        archived_dmg: Path | None = None

        if self.dry_run:
            checksum = "DRY-RUN"
            return ReleaseResult(version, tag, release_dmg, checksum_file, checksum, release_notes, None, None)

        self._preflight(release_notes)

        try:
            if not self.skip_tests:
                self._run_tests()
            self._write_makefile_version(version)
            if not self.skip_build:
                stamp_before = ReleasePreparer._dmg_stamp(root_dmg)
                self._run_make_dmg()
                ReleasePreparer._require_fresh_dmg(root_dmg, stamp_before)
                self._verify_info_plist(version)
                self._verify_launchable_binary()

            if not root_dmg.exists():
                raise ReleaseError(f"没有找到 DMG：{root_dmg}")

            self.paths.releases_dir.mkdir(parents=True, exist_ok=True)
            archived_dmg = self._archive_existing_release_dmg(release_dmg)
            shutil.copy2(root_dmg, release_dmg)

            checksum = sha256_for(release_dmg)
            checksum_file.write_text(f"{checksum}  {release_dmg.name}\n", encoding="utf-8")

            self._write_release_notes(release_notes, version, checksum)
            self._write_changelog(version, checksum)
            # 冻结帧基线放在**整个流程的最后一步**：这样"发布没成功"时根本不会有
            # 一个 `v<那个版本>.json` 留下来当下一版的基准 —— 顺序本身就是防护，
            # 所以这里不需要（也不该有）一段永远走不到的回滚代码。
            self._snapshot_frame_baseline(version)
        except Exception:
            self._rollback_release_files(
                release_dmg=release_dmg,
                archived_dmg=archived_dmg,
                had_release_dmg=had_release_dmg,
                checksum_file=checksum_file,
                original_checksum_text=original_checksum_text,
                release_notes=release_notes,
                original_release_notes_text=original_release_notes_text,
                original_makefile_text=original_makefile_text,
                original_changelog_text=original_changelog_text,
            )
            raise

        return ReleaseResult(
            version,
            tag,
            release_dmg,
            checksum_file,
            checksum,
            release_notes,
            archived_dmg,
            None if self.skip_build else self.paths.app_info_plist,
        )

    def _snapshot_frame_baseline(self, version: str) -> str | None:
        """发布时把帧基线冻结成逐版本的一份（第三轮审计 §3 C-2）。

        为什么挂在发布流程里而不是"想起来就跑一下"：只有一份可随时 `update` 的工作基线时，
        "和上一版比"里的"上一版"实际是"上一次有人记得 update 的时候" —— 那不是版本，是习惯。

        用 importlib 按文件路径加载：这个脚本既被 `python3 scripts/prepare_release.py` 直接执行，
        也被测试当作 `scripts.prepare_release` 导入，两种入口下的包路径不一样。
        """
        sibling = Path(__file__).with_name("frame_baseline.py")
        if not sibling.exists():
            # 别处的仓库里没有这套帧工具，安静跳过（这条挂钩是本仓自己的约定）。
            return None
        spec = importlib.util.spec_from_file_location("frame_baseline_for_release", sibling)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        frozen = module.snapshot(str(self.paths.root), version)
        if frozen is None:
            # **不许静默地不发基线**：C-2 的"和上一版比"整条链就靠这份文件存在。
            # 少一句 raise 的话，这里会一路绿着发布完，然后下一版的比对悄悄退化成
            # "和工作基线比" —— 而没人会去查是谁把历史问句弄丢的。
            raise ReleaseError(
                "没能冻结帧基线：docs/frame_baseline.json 不存在或读不出来。"
                "发布前先跑 scripts/frame_baseline.py update（第三轮审计 §3 C-2）。"
            )
        return frozen

    def planned_steps(self, raw_version: str) -> list[str]:
        version, tag = normalize_version(raw_version)
        steps = [
            f"版本号：{version}（tag: {tag}）",
        ]
        if self.skip_tests:
            steps.append("跳过自动测试")
        else:
            steps.append("运行 Swift 单元测试和发布脚本测试")
        steps.append("写入 Makefile VERSION，并由 Makefile 写入 App 的 Info.plist")
        if self.skip_build:
            steps.append("跳过构建，使用现有 DMG")
        else:
            steps.append("运行 make dmg 构建 App 并生成 DMG")
            steps.append("验证 App 的 Info.plist 版本号")
            steps.append("反汇编包内二进制，确认没有给 AppDelegate 留 -init 桩（启动闸门）")
        steps.append("把帧基线冻结成 docs/frame_baselines/v%s.json（下一版据此回答「哪些帧变了」）" % version)
        steps.extend(
            [
                f"复制 DMG 到 releases/{APP_NAME}_v{version}.dmg",
                "生成 SHA256 校验文件",
                f"生成 docs/RELEASE_NOTES_v{version}.md",
                "更新 CHANGELOG.md",
                "如 releases 中已有同名 DMG，先移入 releases/archive",
            ]
        )
        return steps

    def _ensure_project_root(self) -> None:
        if not self.paths.makefile.exists():
            raise ReleaseError(f"没有找到 Makefile：{self.paths.makefile}")
        if not self.paths.changelog.exists():
            raise ReleaseError(f"没有找到 CHANGELOG.md：{self.paths.changelog}")

    def _preflight(self, release_notes: Path) -> None:
        if release_notes.exists() and not self.force:
            raise ReleaseError(f"发布说明已存在：{release_notes}。如需覆盖，请加 --force。")

    def _write_makefile_version(self, version: str) -> None:
        text = self.paths.makefile.read_text(encoding="utf-8")
        self.paths.makefile.write_text(replace_makefile_version(text, version), encoding="utf-8")

    def _run_tests(self) -> None:
        self.runner(["swift", "test", "--package-path", "ClipboardHistory"], self.paths.root)
        self.runner([sys.executable, "-m", "unittest", "discover", "-s", "scripts/tests"], self.paths.root)

    def _run_make_dmg(self) -> None:
        self.runner(["make", "dmg"], self.paths.root)

    @staticmethod
    def _dmg_stamp(path: Path) -> int | None:
        """DMG 的 mtime_ns；文件不存在返回 None（意味着必须被新建出来）。"""
        return path.stat().st_mtime_ns if path.exists() else None

    @staticmethod
    def _require_fresh_dmg(path: Path, stamp_before: int | None) -> None:
        """构建后必须真的出现一个新 DMG。

        少了这道闸，`make dmg` 静默失败时脚本会把**上一版的字节**当成本版归档，
        还会顺手算出"自洽"的 sha256 写进 CHANGELOG —— 下游没有任何办法发现
        v1.4.6 里装的是 v1.4.5（审计 R-15/R-34）。
        """
        if not path.exists():
            raise ReleaseError(f"make dmg 之后没有找到 {path.name}：构建没有产出 DMG。")
        if stamp_before is None:
            return
        if path.stat().st_mtime_ns <= stamp_before:
            raise ReleaseError(
                f"{path.name} 在 make dmg 之后没有被改写（mtime 未变），"
                "拒绝把上一版的产物当成本版发布。"
            )

    def _verify_info_plist(self, version: str) -> None:
        if not self.paths.app_info_plist.exists():
            raise ReleaseError(f"没有找到 App Info.plist：{self.paths.app_info_plist}")

        with self.paths.app_info_plist.open("rb") as file:
            info = plistlib.load(file)

        actual_version = info.get("CFBundleShortVersionString")
        if actual_version != version:
            raise ReleaseError(
                f"Info.plist 版本号不匹配：期望 {version}，实际 {actual_version or '空'}。"
            )

    def _verify_launchable_binary(self) -> None:
        """启动闸门（R2-21）：包里的二进制不许给 AppDelegate 留 `-init` 桩。

        D-029 那次闪退就是这个形状：Swift 侧写 `AppDelegate()` 会解析到带默认参数的
        `init(historyStore:)`，所以几百个用例与 CI 全绿也碰不到 ObjC 的 `-init`；
        而 SwiftUI 的 `@NSApplicationDelegateAdaptor(AppDelegate.self)` 正是通过 ObjC 发 `-init`，
        桩一命中就 `EXC_BREAKPOINT`。只有真的打开 .app 才看得见 —— 而发布链路里没人打开它。

        这里不启动用户的 app（那会读他真实存档、还可能触发写盘），改成读反汇编：
        编译器留没留那个桩，和"打开就 trap"是同一件事，且完全可离线判定。
        只反汇编 arm64 切片（发布包是 universal，两切片同源同结论，省一半时间）。
        """
        if not self.paths.app_info_plist.exists():
            raise ReleaseError(f"没有找到 App Info.plist：{self.paths.app_info_plist}")
        with self.paths.app_info_plist.open("rb") as file:
            executable_name = plistlib.load(file).get("CFBundleExecutable")
        if not executable_name:
            raise ReleaseError("Info.plist 里没有 CFBundleExecutable，无法做启动检查。")

        executable = self.paths.app_bundle / "Contents" / "MacOS" / str(executable_name)
        if not executable.exists():
            raise ReleaseError(f"没有找到可执行文件：{executable}")

        blockers = find_launch_blockers(self.disassembly_reader(executable))
        if blockers:
            raise ReleaseError(
                "包里的二进制给这些类留了「未实现初始化器」桩，用户一打开就会闪退："
                + "、".join(blockers)
                + "。修法见 AGENT_DECISIONS.md 的 D-029（显式 override init()）。"
            )

    @staticmethod
    def _default_runner(command: Sequence[str], cwd: Path) -> None:
        subprocess.run(list(command), cwd=cwd, check=True, env=build_child_environment())


    def _archive_existing_release_dmg(self, release_dmg: Path) -> Path | None:
        if not release_dmg.exists():
            return None
        self.paths.archive_dir.mkdir(parents=True, exist_ok=True)
        archived = self.paths.archive_dir / f"{release_dmg.stem}-{self.timestamp}{release_dmg.suffix}"
        shutil.move(str(release_dmg), str(archived))
        return archived

    def _write_release_notes(self, path: Path, version: str, checksum: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_release_notes(version, self.today, checksum), encoding="utf-8")

    def _write_changelog(self, version: str, checksum: str) -> None:
        text = self.paths.changelog.read_text(encoding="utf-8")
        self.paths.changelog.write_text(
            insert_changelog_release(text, version, self.today, checksum),
            encoding="utf-8",
        )

    def _rollback_release_files(
        self,
        *,
        release_dmg: Path,
        archived_dmg: Path | None,
        had_release_dmg: bool,
        checksum_file: Path,
        original_checksum_text: str | None,
        release_notes: Path,
        original_release_notes_text: str | None,
        original_makefile_text: str,
        original_changelog_text: str,
    ) -> None:
        self.paths.makefile.write_text(original_makefile_text, encoding="utf-8")
        self.paths.changelog.write_text(original_changelog_text, encoding="utf-8")
        self._restore_text_file(checksum_file, original_checksum_text)
        self._restore_text_file(release_notes, original_release_notes_text)

        if release_dmg.exists():
            release_dmg.unlink()
        if had_release_dmg and archived_dmg and archived_dmg.exists():
            archived_dmg.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(archived_dmg), str(release_dmg))

    @staticmethod
    def _restore_text_file(path: Path, original_text: str | None) -> None:
        if original_text is None:
            if path.exists():
                path.unlink()
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(original_text, encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="准备时间剪史本地发布包。")
    parser.add_argument("version", help="版本号，例如 1.2.3、v1.2.3 或 1.2.3beta")
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--dry-run", action="store_true", help="只展示计划，不写文件、不构建")
    parser.add_argument("--skip-tests", action="store_true", help="跳过自动测试")
    parser.add_argument("--skip-build", action="store_true", help="跳过 make dmg，使用项目根目录已有 DMG")
    parser.add_argument("--force", action="store_true", help="允许覆盖已有发布说明")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    preparer = ReleasePreparer(
        ReleasePaths(args.project_root.resolve()),
        dry_run=args.dry_run,
        skip_tests=args.skip_tests,
        skip_build=args.skip_build,
        force=args.force,
    )

    if args.dry_run:
        print("发布准备预演：")
        for step in preparer.planned_steps(args.version):
            print(f"- {step}")
        return 0

    try:
        result = preparer.prepare(args.version)
    except (ReleaseError, subprocess.CalledProcessError) as error:
        print(f"发布准备失败：{error}", file=sys.stderr)
        return 1

    print(f"发布准备完成：{result.tag}")
    print(f"- DMG：{result.dmg}")
    print(f"- SHA256：{result.checksum}")
    print(f"- 校验文件：{result.checksum_file}")
    print(f"- 发布说明：{result.release_notes}")
    if result.info_plist:
        print(f"- Info.plist：{result.info_plist}")
    if result.archived_dmg:
        print(f"- 已备份旧 DMG：{result.archived_dmg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
