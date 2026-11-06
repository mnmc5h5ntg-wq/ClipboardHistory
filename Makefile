APP_NAME := 时间剪史
VERSION  := 1.4.8
STAGE   := /tmp/$(APP_NAME)_bundle
# R592（BACKLOG 620）：构建产物**只**落在暂存目录，不再往仓库根 ditto 一份可执行 .app。
# 为什么这一条要写进 Makefile 而不是只写进文档：仓库根那份和 /Applications 那份同一个
# CFBundleIdentifier，LaunchServices 会把两条都登记，登录项/Dock 当初记住的是仓库根那条
# ⇒ 用户重启后看到第二个"时间剪史"图标，而点开的是构建产物（会被下一次 make 覆盖掉）。
BUNDLE  := $(STAGE)/$(APP_NAME).app
BINARY  := ClipboardHistoryApp
BUILD_A := ClipboardHistory/.build/arm64-apple-macosx/debug
BUILD_X := ClipboardHistory/.build/x86_64-apple-macosx/debug
UNI     := /tmp/$(BINARY)_universal
ICONS   := ClipboardHistory/.build/arm64-apple-macosx/debug/ClipboardHistory_ClipboardHistoryApp.bundle/AppIcon.icns
BUILD_HINT := 构建失败：若报错里有 not registered 或 missing inputs: DerivedSources，说明 .build 处于半删除状态；执行 rm -rf ClipboardHistory/.build 后重试

.PHONY: build run clean bundle dmg

# SwiftPM 的两个 --triple 目录共用一份构建数据库；只删掉其中一个（或被中断）之后，
# 下一次 build 会报 `not registered` / `missing inputs: DerivedSources/...`，
# 而且不会自己恢复。本轮实测撞到两次，所以失败时把唯一有效的处置打出来。
build:
	cd ClipboardHistory && swift build --triple arm64-apple-macosx || { echo "$(BUILD_HINT)"; exit 1; }
	cd ClipboardHistory && swift build --triple x86_64-apple-macosx || { echo "$(BUILD_HINT)"; exit 1; }
	lipo -create "$(BUILD_A)/$(BINARY)" "$(BUILD_X)/$(BINARY)" -output "$(UNI)"
	@echo "✅ Universal Binary ready (arm64 + x86_64)"

bundle: build
	rm -rf "$(STAGE)"
	mkdir -p "$(BUNDLE)/Contents/MacOS" "$(BUNDLE)/Contents/Resources"
	cp "$(UNI)" "$(BUNDLE)/Contents/MacOS/$(BINARY)"
	if [ ! -f "$(ICONS)" ]; then echo "❌ 找不到图标 $(ICONS)（先跑 make build）"; exit 1; fi
	cp "$(ICONS)" "$(BUNDLE)/Contents/Resources/AppIcon.icns"
	scripts/make_info_plist.sh ClipboardHistory/Resources/Info.plist "$(BUNDLE)/Contents/Info.plist" "$(VERSION)"
	xattr -cr "$(BUNDLE)"
	find "$(BUNDLE)" -name ".DS_Store" -delete 2>/dev/null || true
	find "$(BUNDLE)" -name "._*" -delete 2>/dev/null || true
	dot_clean -m "$(BUNDLE)" 2>/dev/null || true
	codesign --remove-signature "$(BUNDLE)" 2>/dev/null || true
	scripts/sign_bundle.sh "$(BUNDLE)"
	codesign --verify --deep --strict --verbose=2 "$(BUNDLE)"
	@echo "✅ $(BUNDLE) ready (签名种类见上面那行 SIGNATURE_KIND, quarantine-free；仓库根不留副本 = 620)"

run: bundle
	open -n "$(BUNDLE)"

dmg: bundle
	rm -rf /tmp/$(APP_NAME)_dmg
	mkdir -p /tmp/$(APP_NAME)_dmg
	ditto --noextattr --noqtn "$(BUNDLE)" /tmp/$(APP_NAME)_dmg/$(APP_NAME).app
	xattr -cr /tmp/$(APP_NAME)_dmg/ 2>/dev/null || true
	codesign --verify --deep --strict --verbose=2 /tmp/$(APP_NAME)_dmg/$(APP_NAME).app
	sed "s/时间剪史 v.* — 安装说明/时间剪史 v$(VERSION) — 安装说明/" 安装说明.txt > /tmp/$(APP_NAME)_dmg/安装说明.txt
	ln -s /Applications /tmp/$(APP_NAME)_dmg/Applications
	hdiutil create -volname "$(APP_NAME)" 		-srcfolder /tmp/$(APP_NAME)_dmg 		-ov -format UDZO 		"$(APP_NAME)_v$(VERSION).dmg"
	shasum -a 256 "$(APP_NAME)_v$(VERSION).dmg" > "$(APP_NAME)_v$(VERSION).dmg.sha256"
	shasum -a 256 -c "$(APP_NAME)_v$(VERSION).dmg.sha256"
	@echo "✅ DMG created: $(APP_NAME)_v$(VERSION).dmg (+ .sha256)"

clean:
	rm -rf "$(BUNDLE)" "$(STAGE)"
	# 清掉 R592 之前那一版留在仓库根的构建产物（620 的根因；它是产物不是源码）
	rm -rf "$(APP_NAME).app"
	rm -rf "$(APP_NAME)_v$(VERSION).dmg" "$(APP_NAME)_v$(VERSION).dmg.sha256"
	cd ClipboardHistory && swift package clean
