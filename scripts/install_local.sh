#!/bin/bash
# 把"构建出来的新版 App 真的换成用户在跑的那一份"固化成一条命令。
#
# 用法：scripts/install_local.sh [--dry-run] [--yes] [--bundle <path>] [--dest <dir>]
#                                [--no-build] [--skip-smoke] [--no-launch] [--label <名>] [--help]
#
# 为什么要有这个脚本（2026-10-12 动效轮收尾）：用户明确要求"以后要手动运行检测都这么干"——
# 需要真机验收的判据（方向键连翻会不会闪、读屏听不听得到、热键路径该不该有动画）
# 只有装上新包才能判。交付一个"要用户自己动手才看得见"的改动等于没交付。
# 而这套流程里每一步都有踩过的坑，靠记忆不可靠，所以写成会红的代码：
#
#   1. **冒烟闸门必须排在"退出旧版"之后**。`InstanceGuard` 是按 bundleIdentifier 在
#      `NSWorkspace.runningApplications` 里找第二实例的（不是数据目录里的锁），
#      所以旧版在跑时新包必然被守卫中止，报 `SMOKE_OK=0` —— 那是假失败。
#   2. **装的那份必须逐字节等于验过的那份**：核 staged 与 installed 的 sha，不等就回滚。
#   3. **"进程在跑"不等于"跑的是新的那份"**：`open` 对已在运行的 App 只"激活"。
#      所以要核新 pid + 启动时刻晚于安装时刻 + 可执行文件路径。
#   4. **活着的 App 会随时写存档**，所以"替换前后逐字节相同"不是有效判据；
#      这里判的是"条数只增不减 + schema 仍读得动"。
#   5. **CJK 路径在 `ps`/`lsof` 里是转义输出的**，别把它直接喂给 `shasum`（会假报"文件不存在"）。
#
# 退出码：0 = 换装并验证通过；非 0 = 没做成（若已进入替换阶段则**已自动回滚**到旧包）。
set -euo pipefail

usage() {
	sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
}

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
app_name="时间剪史"
bundle="${repo_root}/${app_name}.app"        # `make bundle` 会在仓库根产出一份
dest_dir="/Applications"
installed="${dest_dir}/${app_name}.app"
do_build=1
run_smoke=1
launch=1
dry_run=1
confirmed=0
label="local-$(date +%Y%m%d-%H%M%S)"

while [ "$#" -gt 0 ]; do
	case "$1" in
	--dry-run) dry_run=1; shift ;;
	--yes) confirmed=1; dry_run=0; shift ;;
	--bundle) bundle="$2"; shift 2 ;;
	--bundle=*) bundle="${1#*=}"; shift ;;
	--dest) dest_dir="$2"; installed="${dest_dir}/${app_name}.app"; shift 2 ;;
	--dest=*) dest_dir="${1#*=}"; installed="${dest_dir}/${app_name}.app"; shift ;;
	--label=*) label="${1#*=}"; shift ;;
	--no-build) do_build=0; shift ;;
	--skip-smoke) run_smoke=0; shift ;;
	--no-launch) launch=0; shift ;;
	--label) label="$2"; shift 2 ;;
	--help | -h) usage; exit 0 ;;
	*) printf '不认识的参数：%s\n\n' "$1" >&2; usage >&2; exit 2 ;;
	esac
done

binary_name="ClipboardHistoryApp"
staged_binary="${bundle}/Contents/MacOS/${binary_name}"
fail() { printf '❌ %s\n' "$*" >&2; exit 1; }
say() { printf '%s\n' "$*"; }
sha_of() { shasum -a 256 "$1" | cut -d' ' -f1; }
# `proc_pidpath` 返回的是**解析过符号链接**的路径（macOS 上 /var → /private/var），
# 而脚本里的 `installed` 是用户传进来的字面路径。两边都归一化之后再比，
# 否则沙箱测试（路径在 /var/folders 下）会永远比不中 —— 表现就是"没在跑"。
real_path() { python3 -c 'import os,sys; sys.stdout.write(os.path.realpath(sys.argv[1]))' "$1"; }

# ---------- 0. 计划 ----------
backup_root="${HOME}/Documents/Codex_Project0_backups"
backup_dir="${backup_root}/before-${label}"
data_dir="${HOME}/Library/Application Support/${app_name}"
archive="${data_dir}/history.json"

say "目标        = ${installed}"
say "新包        = ${bundle}"
say "备份        = ${backup_dir}"
say "模式        = $([ "$dry_run" = 1 ] && echo 'dry-run（不写任何东西）' || echo '真换装')"
[ "$confirmed" = 1 ] || [ "$dry_run" = 1 ] || fail "内部状态矛盾：既 --yes 又 dry-run"
if [ "$dry_run" = 1 ] && [ "$confirmed" = 0 ]; then
	say ""
	say "这是 dry-run。确认要真的退出当前 App 并替换，请加 --yes。"
	exit 0
fi

# ---------- 回滚 ----------
moved_out=0
restored=0
rollback() {
	rc=$?
	[ "$rc" = 0 ] && exit 0
	[ "$moved_out" = 1 ] || { say "ROLLED_BACK=0（还没动过旧包，无需回滚）"; exit "$rc"; }
	if [ "$restored" = 1 ]; then exit "$rc"; fi
	say "回滚中：把旧包放回 ${installed}"
	rm -rf "$installed" 2>/dev/null || true
	mv "${backup_dir}/${app_name}.app" "${installed}" && restored=1
	say "ROLLED_BACK=1"
	open "$installed" >/dev/null 2>&1 || say "⚠️ 旧包已放回但没能自动启动，请手动打开"
	exit "$rc"
}
trap rollback EXIT

# ---------- 1. 基线 ----------
if [ -d "$installed" ]; then
	old_sha="$(sha_of "${installed}/Contents/MacOS/${binary_name}")"
	old_version="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "${installed}/Contents/Info.plist" 2>/dev/null || echo '?')"
	say "已装版本    = ${old_version}  sha=${old_sha:0:16}…"
else
	old_sha=""
	old_version="(没有已装版本)"
	say "已装版本    = 无（首次安装）"
fi
entries_before="-"
if [ -f "$archive" ]; then
	entries_before="$(python3 -c 'import json,sys;d=json.load(open(sys.argv[1]));print(len(d["entries"]) if isinstance(d,dict) and "entries" in d else -1)' "$archive")"
fi
say "存档条数    = ${entries_before}（只读，脚本不写它）"

# ---------- 2. 构建 ----------
if [ "$do_build" = 1 ]; then
	say "→ make bundle"
	( cd "$repo_root" && make bundle >/tmp/install_local_build.log 2>&1 ) || { tail -20 /tmp/install_local_build.log >&2; fail "构建失败（日志 /tmp/install_local_build.log）"; }
fi
[ -x "$staged_binary" ] || fail "找不到可执行文件 ${staged_binary}（先 make bundle，或用 --bundle 指到已构建的包）"
staged_sha="$(sha_of "$staged_binary")"
say "新包 sha    = ${staged_sha:0:16}…"

# ---------- 3. 退出正在跑的旧版（冒烟闸门的前置，见文件头第 1 条）----------
# 只退"跑着的就是我要换的那一份"：按可执行文件路径认，不按进程名认。
# 否则往 /tmp 装一份做验证时，会顺手把用户 /Applications 里那份杀掉。
#
# 路径必须用 `scripts/proc_path.py`（proc_pidpath）拿，**不能**用 `lsof`/`ps` 的输出：
# App 名字是中文，那两个工具会把非 ASCII 转义成 `\346\227\266…`，于是比较永远不相等，
# 脚本就会误判"没在跑"、跳过退出旧版，然后被第二实例守卫假报成冒烟失败
# （2026-10-12 真就是这么失败的；判据见 scripts/tests/test_install_local.py）。
running_pid_under() {
	local want="$1" pid path
	for pid in $(pgrep -x "$binary_name" 2>/dev/null || true); do
		path="$(python3 "${repo_root}/scripts/proc_path.py" "$pid" 2>/dev/null || true)"
		[ -n "$path" ] && [ "$path" = "$(real_path "$want")/Contents/MacOS/$binary_name" ] && { printf '%s\n' "$pid"; return 0; }
	done
	return 1
}
old_pid="$(running_pid_under "$installed" || true)"
if [ -n "$old_pid" ]; then
	# 先无条件把"认出来了"打出来：这条判据坏过两次（lsof 转义、比较留尾斜杠），
	# 两次的表现都是"没在跑"，而真正的后果在后面那步冒烟闸门里看不出来。
	say "检测到要替换的实例 pid=${old_pid}"
	if [ "$dest_dir" != "/Applications" ]; then
		# 沙箱验证（`--dest /tmp/...`）**不给任何 App 发退出指令**。
		# 原来这里不分沙箱，而 `osascript tell application "<名字>" to quit` 是
		# **按名字全局**发指令的：2026-10-13 跑自检时，它把用户 /Applications 里那份真 App 退掉了。
		# 不用 SIGTERM 代替是有原因的：存档落盘挂在 `applicationWillTerminate` 上
		# （`ApplicationShell.swift:134` → `flushPendingPersistence`），SIGTERM 不触发它，
		# 会把去抖窗口里还没写盘的记录丢掉 —— 一个以"别丢历史"为使命的 App 不能这么退。
		say "目标不是 /Applications（沙箱验证）⇒ 不发退出指令，也不动用户那份实例"
	else
		say "→ 优雅退出正在跑的 ${app_name}（让它把待写存档落盘）"
		osascript -e "tell application \"${app_name}\" to quit" >/dev/null 2>&1 || true
		for _ in $(seq 1 30); do
			kill -0 "$old_pid" 2>/dev/null || break
			sleep 0.5
		done
		kill -0 "$old_pid" 2>/dev/null && fail "旧版 pid ${old_pid} 15 秒内没退出（可能正忙或有未决对话框）；不去 kill -9，请手动退出后重试"
		say "旧版已退出"
	fi
else
	say "要换的那一份没在跑，跳过退出"
fi

# ---------- 4. 运行时冒烟（必须 SMOKE_OK=1）----------
if [ "$run_smoke" = 1 ]; then
	say "→ 运行时冒烟闸门（临时数据目录，不碰真存档）"
	smoke_out="$(cd "$repo_root" && python3 scripts/launch_smoke.py "$bundle" --timeout 40 2>&1)" || true
	printf '%s\n' "$smoke_out" | sed 's/^/   /'
	printf '%s\n' "$smoke_out" | grep -q '^SMOKE_OK=1$' || fail "冒烟闸门没过（见上）。注意：如果旧版还在跑，这里会被第二实例守卫假报成失败"
else
	say "跳过冒烟闸门（--skip-smoke）"
fi

# ---------- 5. 旧包移走备份（不删）+ 新包落位 ----------
codesign --verify --deep --strict "$bundle" 2>/dev/null || fail "新包签名校验就没过，不动现有安装"
mkdir -p "$backup_dir"
if [ -d "$installed" ]; then
	mv "$installed" "${backup_dir}/${app_name}.app"
	moved_out=1
	say "旧包已移入  = ${backup_dir}"
fi
ditto --noextattr --noqtn "$bundle" "$installed"

# ---------- 6. 装的那份 == 验过的那份 ----------
installed_sha="$(sha_of "${installed}/Contents/MacOS/${binary_name}")"
say "staged    = ${staged_sha:0:16}…"
say "installed = ${installed_sha:0:16}…"
[ "$staged_sha" = "$installed_sha" ] || fail "装的与验过的不是同一份，回滚"
codesign --verify --deep --strict "$installed" || fail "装完的签名校验不过，回滚"
say "INSTALL_SHA_MATCH=1"

# ---------- 7. 启动，并按身份认（不按 open 的客气话认）----------
if [ "$launch" = 0 ]; then
	say "跳过启动与身份核对（--no-launch：沙箱验证用；同 bundle id 的副本会被第二实例守卫自退）"
	trap - EXIT
	say "INSTALL_RESULT=sandbox-ok（未启动，因此不构成交付证明）"
	exit 0
fi
before_pid="$(running_pid_under "$installed" || true)"
install_epoch="$(date +%s)"
open "$installed"
pid=""
for _ in $(seq 1 30); do
	pid="$(running_pid_under "$installed" || true)"
	[ -n "$pid" ] && break
	sleep 0.5
done
[ -n "$pid" ] || fail "启动后找不到进程"
[ "$pid" != "$before_pid" ] || fail "pid 没变（$pid）—— 这就是'open 只激活了旧进程'那一类假装机"
proc_start="$(ps -o lstart= -p "$pid" | xargs -I{} date -j -f '%a %b %e %T %Y' '{}' +%s 2>/dev/null || echo 0)"
[ "$proc_start" -ge "$install_epoch" ] || fail "进程启动时刻($proc_start)早于安装时刻($install_epoch)：跑的不是刚装的这份"
exe_path="$(python3 "${repo_root}/scripts/proc_path.py" "$pid" 2>/dev/null || true)"
[ -n "$exe_path" ] || fail "读不到进程的可执行文件路径（proc_path.py 失败了，别用 lsof/ps 的输出兜底：CJK 路径会被转义）"
[ "$exe_path" = "$(real_path "$installed")/Contents/MacOS/$binary_name" ] \
	|| fail "跑着的这份不是刚装的那一份：exe=${exe_path}"
say "INSTALL_RUNNING_PID=${pid} 启动晚于安装，exe 路径逐字对上 ${installed} ✔"

# ---------- 8. 存档只读复核：条数不许变少 ----------
if [ -f "$archive" ]; then
	entries_after="$(python3 -c 'import json,sys;d=json.load(open(sys.argv[1]));print(len(d["entries"]) if isinstance(d,dict) and "entries" in d else -1)' "$archive")"
else
	entries_after="-1"
fi
say "INSTALL_ENTRIES_BEFORE=${entries_before}  INSTALL_ENTRIES_AFTER=${entries_after}"
if [ "$entries_after" != "-1" ] && [ "$entries_before" != "-" ]; then
	[ "$entries_after" -ge "$entries_before" ] || fail "存档条数变少了（${entries_before} → ${entries_after}）：立刻回滚，别用这个包"
fi

# ---------- 9. 崩溃面 ----------
recent_crash="$(ls -t "${HOME}/Library/Logs/DiagnosticReports/" 2>/dev/null | grep -a "^${binary_name}" | head -1 || true)"
if [ -n "$recent_crash" ]; then
	newer="$(python3 -c 'import os,sys,time;print(1 if os.path.getmtime(os.path.join(sys.argv[1],sys.argv[2]))>=int(sys.argv[3])-5 else 0)' "${HOME}/Library/Logs/DiagnosticReports" "$recent_crash" "$install_epoch")"
	[ "$newer" = "0" ] || fail "安装之后出现了新的崩溃报告：${recent_crash}"
fi

trap - EXIT
say "INSTALL_RESULT=ok  版本=${old_version}→$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "${installed}/Contents/Info.plist" 2>/dev/null || echo '?')"
say "旧包留在：${backup_dir}（要退回：rm -rf '${installed}' && mv '${backup_dir}/${app_name}.app' '${installed}' && open '${installed}'）"
