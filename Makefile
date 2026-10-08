APP_NAME := 时间剪史
VERSION  := 1.4.5
BUNDLE  := $(APP_NAME).app
BINARY  := ClipboardHistoryApp
BUILD_A := ClipboardHistory/.build/arm64-apple-macosx/debug
BUILD_X := ClipboardHistory/.build/x86_64-apple-macosx/debug
UNI     := /tmp/$(BINARY)_universal
ICONS   := ClipboardHistory/.build/arm64-apple-macosx/debug/ClipboardHistory_ClipboardHistoryApp.bundle/AppIcon.icns
STAGE   := /tmp/$(APP_NAME)_bundle
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
	rm -rf "$(BUNDLE)"
	rm -rf "$(STAGE)"
	mkdir -p "$(STAGE)/$(BUNDLE)/Contents/MacOS"
	mkdir -p "$(STAGE)/$(BUNDLE)/Contents/Resources"
	cp "$(UNI)" "$(STAGE)/$(BUNDLE)/Contents/MacOS/$(BINARY)"
	if [ ! -f "$(ICONS)" ]; then echo "❌ 找不到图标 $(ICONS)（先跑 make build）"; exit 1; fi
	cp "$(ICONS)" "$(STAGE)/$(BUNDLE)/Contents/Resources/AppIcon.icns"
	scripts/make_info_plist.sh ClipboardHistory/Resources/Info.plist "$(STAGE)/$(BUNDLE)/Contents/Info.plist" "$(VERSION)"
	xattr -cr "$(STAGE)/$(BUNDLE)"
	find "$(STAGE)/$(BUNDLE)" -name ".DS_Store" -delete 2>/dev/null || true
	find "$(STAGE)/$(BUNDLE)" -name "._*" -delete 2>/dev/null || true
	dot_clean -m "$(STAGE)/$(BUNDLE)" 2>/dev/null || true
	codesign --remove-signature "$(STAGE)/$(BUNDLE)" 2>/dev/null || true
	codesign -s - --force --deep "$(STAGE)/$(BUNDLE)" 2>&1
	codesign --verify --deep --strict --verbose=2 "$(STAGE)/$(BUNDLE)"
	ditto --noextattr --noqtn "$(STAGE)/$(BUNDLE)" "$(BUNDLE)"
	xattr -cr "$(BUNDLE)"
	xattr -d com.apple.FinderInfo "$(BUNDLE)" 2>/dev/null || true
	xattr -d "com.apple.fileprovider.fpfs#P" "$(BUNDLE)" 2>/dev/null || true
	xattr -d com.apple.macl "$(BUNDLE)" 2>/dev/null || true
	@echo "✅ $(BUNDLE) ready (ad-hoc signed, quarantine-free)"

run: bundle
	open -n "$(STAGE)/$(BUNDLE)"

dmg: bundle
	rm -rf /tmp/$(APP_NAME)_dmg
	mkdir -p /tmp/$(APP_NAME)_dmg
	ditto --noextattr --noqtn "$(STAGE)/$(BUNDLE)" /tmp/$(APP_NAME)_dmg/$(BUNDLE)
	xattr -cr /tmp/$(APP_NAME)_dmg/ 2>/dev/null || true
	codesign --verify --deep --strict --verbose=2 /tmp/$(APP_NAME)_dmg/$(BUNDLE)
	sed "s/时间剪史 v.* — 安装说明/时间剪史 v$(VERSION) — 安装说明/" 安装说明.txt > /tmp/$(APP_NAME)_dmg/安装说明.txt
	ln -s /Applications /tmp/$(APP_NAME)_dmg/Applications
	hdiutil create -volname "$(APP_NAME)" 		-srcfolder /tmp/$(APP_NAME)_dmg 		-ov -format UDZO 		"$(APP_NAME)_v$(VERSION).dmg"
	shasum -a 256 "$(APP_NAME)_v$(VERSION).dmg" > "$(APP_NAME)_v$(VERSION).dmg.sha256"
	shasum -a 256 -c "$(APP_NAME)_v$(VERSION).dmg.sha256"
	@echo "✅ DMG created: $(APP_NAME)_v$(VERSION).dmg (+ .sha256)"

clean:
	rm -rf "$(BUNDLE)" "$(APP_NAME)_v$(VERSION).dmg" "$(APP_NAME)_v$(VERSION).dmg.sha256"
	cd ClipboardHistory && swift package clean
