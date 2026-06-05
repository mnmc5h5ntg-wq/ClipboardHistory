APP_NAME := 时间剪史
BUNDLE  := $(APP_NAME).app
BINARY  := ClipboardHistoryApp
BUILD_A := ClipboardHistory/.build/arm64-apple-macosx/debug
BUILD_X := ClipboardHistory/.build/x86_64-apple-macosx/debug
UNI     := /tmp/$(BINARY)_universal
ICONS   := ClipboardHistory/.build/arm64-apple-macosx/debug/ClipboardHistory_ClipboardHistoryApp.bundle/AppIcon.icns

.PHONY: build run clean bundle dmg

build:
	cd ClipboardHistory && swift build --triple arm64-apple-macosx
	cd ClipboardHistory && swift build --triple x86_64-apple-macosx
	lipo -create "$(BUILD_A)/$(BINARY)" "$(BUILD_X)/$(BINARY)" -output "$(UNI)"
	@echo "✅ Universal Binary ready (arm64 + x86_64)"

bundle: build
	rm -rf "$(BUNDLE)"
	mkdir -p "$(BUNDLE)/Contents/MacOS"
	mkdir -p "$(BUNDLE)/Contents/Resources"
	cp "$(UNI)" "$(BUNDLE)/Contents/MacOS/$(BINARY)"
	cp "$(ICONS)" "$(BUNDLE)/Contents/Resources/AppIcon.icns" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Add :CFBundleExecutable string $(BINARY)" "$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Set :CFBundleExecutable $(BINARY)" "$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Add :CFBundleIdentifier string com.clipboardhistory.app" "$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Set :CFBundleIdentifier com.clipboardhistory.app" "$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Add :CFBundleName string $(APP_NAME)" "$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Set :CFBundleName $(APP_NAME)" "$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Add :CFBundleVersion string 1" "$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Add :CFBundleShortVersionString string 1.1" "$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Add :CFBundleIconFile string AppIcon" "$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Set :CFBundleIconFile AppIcon" "$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Add :LSMinimumSystemVersion string 12.0" "$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Set :LSMinimumSystemVersion 12.0" "$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Add :NSHighResolutionCapable bool true" "$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
		xattr -cr "$(BUNDLE)"
	find "$(BUNDLE)" -name ".DS_Store" -delete 2>/dev/null || true
	find "$(BUNDLE)" -name "._*" -delete 2>/dev/null || true
	dot_clean -m "$(BUNDLE)" 2>/dev/null || true
	codesign --remove-signature "$(BUNDLE)" 2>/dev/null || true
	-codesign -s - --force --deep "$(BUNDLE)" 2>&1
	codesign -dv "$(BUNDLE)" 2>/dev/null | head -1 || echo "(sign check skipped)"
	touch "$(BUNDLE)"
	@echo "✅ $(BUNDLE) ready (ad-hoc signed, quarantine-free)"

run: bundle
	open "$(BUNDLE)"

dmg: bundle
	rm -rf /tmp/$(APP_NAME)_dmg
	mkdir -p /tmp/$(APP_NAME)_dmg
	cp -Rp "$(BUNDLE)" /tmp/$(APP_NAME)_dmg/
	xattr -cr /tmp/$(APP_NAME)_dmg/ 2>/dev/null || true
	cp /tmp/readme_dmg.txt /tmp/$(APP_NAME)_dmg/安装说明.txt
	ln -s /Applications /tmp/$(APP_NAME)_dmg/Applications
	hdiutil create -volname "$(APP_NAME)" 		-srcfolder /tmp/$(APP_NAME)_dmg 		-ov -format UDZO 		"$(APP_NAME)_v1.1.dmg"
	@echo "✅ DMG created: $(APP_NAME)_v1.1.dmg"

clean:
	rm -rf "$(BUNDLE)" "$(APP_NAME)_v1.1.dmg"
	cd ClipboardHistory && swift package clean
