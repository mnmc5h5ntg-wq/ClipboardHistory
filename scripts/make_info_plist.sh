#!/bin/sh
# 从模板生成 App bundle 的 Info.plist，并把"产物是否完整"变成构建失败。
#
# 用法：scripts/make_info_plist.sh <模板> <输出> <版本号>
#
# 为什么单独成文：以前这些步骤是 Makefile 里 20 行 PlistBuddy，每行都带
# `2>/dev/null || true`，于是"缺一个键"和"构建成功"长得一模一样（审计 R-15/R-34）。
# 挪进脚本后它可被单元测试直接跑，不必先做一次几分钟的 universal 构建。
set -eu

if [ "$#" -ne 3 ]; then
	echo "用法：$0 <模板 plist> <输出 plist> <版本号>" >&2
	exit 2
fi

template="$1"
dest="$2"
version="$3"

# 少任何一个都可能"能跑但发布不对"：用途描述缺失会让系统静默拒绝自动化，
# 版本号不一致会让发布脚本把上一版当成本版。
required_keys="CFBundleExecutable CFBundleIdentifier CFBundleName CFBundleShortVersionString LSMinimumSystemVersion NSAppleEventsUsageDescription NSPrincipalClass CFBundlePackageType"

if [ ! -f "${template}" ]; then
	echo "❌ 找不到模板 ${template}" >&2
	exit 1
fi

mkdir -p "$(dirname "${dest}")"
sed "s/__VERSION__/${version}/" "${template}" > "${dest}"

if ! plutil -lint "${dest}" >/dev/null; then
	echo "❌ 生成的 plist 语法不合法：${dest}" >&2
	exit 1
fi

for key in $required_keys; do
	if ! /usr/libexec/PlistBuddy -c "Print :${key}" "${dest}" >/dev/null 2>&1; then
		echo "❌ Info.plist 缺少必需键 ${key}" >&2
		exit 1
	fi
done

actual_version=$(/usr/libexec/PlistBuddy -c "Print :CFBundleShortVersionString" "${dest}")
if [ "${actual_version}" != "${version}" ]; then
	echo "❌ 版本号不一致：Info.plist 是 ${actual_version}，期望 ${version}" >&2
	exit 1
fi

if grep -q "__VERSION__" "${dest}"; then
	echo "❌ Info.plist 里还留着未替换的 __VERSION__ 占位符" >&2
	exit 1
fi

echo "✅ Info.plist 就绪：版本 ${version}，必需键 $(printf '%s\n' $required_keys | wc -l | tr -d ' ') 个齐备"
