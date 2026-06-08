APP_NAME := 时间剪史
VERSION  := 1.3
BUNDLE  := $(APP_NAME).app
BINARY  := ClipboardHistoryApp
BUILD_A := ClipboardHistory/.build/arm64-apple-macosx/debug
BUILD_X := ClipboardHistory/.build/x86_64-apple-macosx/debug
UNI     := /tmp/$(BINARY)_universal
ICONS   := ClipboardHistory/.build/arm64-apple-macosx/debug/ClipboardHistory_ClipboardHistoryApp.bundle/AppIcon.icns
STAGE   := /tmp/$(APP_NAME)_bundle

.PHONY: build run clean bundle dmg

build:
	cd ClipboardHistory && swift build --triple arm64-apple-macosx
	cd ClipboardHistory && swift build --triple x86_64-apple-macosx
	lipo -create "$(BUILD_A)/$(BINARY)" "$(BUILD_X)/$(BINARY)" -output "$(UNI)"
	@echo "✅ Universal Binary ready (arm64 + x86_64)"

bundle: build
	rm -rf "$(BUNDLE)"
	rm -rf "$(STAGE)"
	mkdir -p "$(STAGE)/$(BUNDLE)/Contents/MacOS"
	mkdir -p "$(STAGE)/$(BUNDLE)/Contents/Resources"
	cp "$(UNI)" "$(STAGE)/$(BUNDLE)/Contents/MacOS/$(BINARY)"
	cp "$(ICONS)" "$(STAGE)/$(BUNDLE)/Contents/Resources/AppIcon.icns" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Add :CFBundleExecutable string $(BINARY)" "$(STAGE)/$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Set :CFBundleExecutable $(BINARY)" "$(STAGE)/$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Add :CFBundleIdentifier string com.clipboardhistory.app" "$(STAGE)/$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Set :CFBundleIdentifier com.clipboardhistory.app" "$(STAGE)/$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Add :CFBundleName string $(APP_NAME)" "$(STAGE)/$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Set :CFBundleName $(APP_NAME)" "$(STAGE)/$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Add :CFBundleVersion string 1" "$(STAGE)/$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Add :CFBundleShortVersionString string $(VERSION)" "$(STAGE)/$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Add :CFBundleIconFile string AppIcon" "$(STAGE)/$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Set :CFBundleIconFile AppIcon" "$(STAGE)/$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Add :LSMinimumSystemVersion string 12.0" "$(STAGE)/$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Set :LSMinimumSystemVersion 12.0" "$(STAGE)/$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Add :NSHighResolutionCapable bool true" "$(STAGE)/$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
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
	open "$(STAGE)/$(BUNDLE)"

dmg: bundle
	rm -rf /tmp/$(APP_NAME)_dmg
	mkdir -p /tmp/$(APP_NAME)_dmg
	ditto --noextattr --noqtn "$(STAGE)/$(BUNDLE)" /tmp/$(APP_NAME)_dmg/$(BUNDLE)
	xattr -cr /tmp/$(APP_NAME)_dmg/ 2>/dev/null || true
	codesign --verify --deep --strict --verbose=2 /tmp/$(APP_NAME)_dmg/$(BUNDLE)
	sed "s/时间剪史 v.* — 安装说明/时间剪史 v$(VERSION) — 安装说明/" 安装说明.txt > /tmp/$(APP_NAME)_dmg/安装说明.txt
	ln -s /Applications /tmp/$(APP_NAME)_dmg/Applications
	hdiutil create -volname "$(APP_NAME)" 		-srcfolder /tmp/$(APP_NAME)_dmg 		-ov -format UDZO 		"$(APP_NAME)_v$(VERSION).dmg"
	@echo "✅ DMG created: $(APP_NAME)_v$(VERSION).dmg"

clean:
	rm -rf "$(BUNDLE)" "$(APP_NAME)_v$(VERSION).dmg"
	cd ClipboardHistory && swift package clean
