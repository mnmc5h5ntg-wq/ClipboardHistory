#!/bin/sh
# R553 A：给本机构建选一个**固定**的代码签名身份。
#
# 为什么要它（用户实测：反复弹「时间剪史想访问桌面文件夹」，已批准无数次）：
# 每次构建都 `--remove-signature` 再 `-s -`（ad-hoc）⇒ CDHash 每轮变 ⇒ TCC 把它当成一个新 App，
# "桌面文件夹"那次授权作废 ⇒ 下一次读桌面又弹。授权跟着**签名身份**走，不跟着 bundle 路径走。
#
# 规矩（都写在台账里）：
# · 只在**登录钥匙串**里找身份；不动系统钥匙串、不 sudo、不改全局信任、不 `tccutil reset`。
# · 身份不存在或 `codesign` 因为信任链拒绝 ⇒ 回退 ad-hoc，并把这一格打进读数：
#   `SIGNATURE_KIND=local|adhoc`。CI 与其他机器没有这个身份，行为与以前逐字节相同。
# · 不许拿"回退 ad-hoc"当交差：本机要的是那条身份真的被用上，验收是连续两轮安装
#   `codesign -dvv` 的签名身份不变（这一条只能真机人工确认）。
set -u
IDENTITY="${CLIPBOARD_HISTORY_SIGN_IDENTITY:-ClipboardHistory Local Signing}"
bundle="${1:?用法：sign_bundle.sh <bundle>}"

if security find-identity -v -p codesigning 2>/dev/null | grep -F "\"$IDENTITY\"" >/dev/null; then
    if codesign -s "$IDENTITY" --force --timestamp=none "$bundle" 2>/tmp/sign_bundle.err; then
        echo "SIGNATURE_KIND=local identity=$IDENTITY"
        exit 0
    fi
    echo "SIGNATURE_KIND=identity-refused identity=$IDENTITY 原因=$(head -1 /tmp/sign_bundle.err 2>/dev/null)"
fi
codesign -s - --force --deep "$bundle" 2>&1
echo "SIGNATURE_KIND=adhoc"
