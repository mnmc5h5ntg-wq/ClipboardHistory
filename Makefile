APP_NAME := 时间剪史
BUNDLE  := $(APP_NAME).app
BINARY  := ClipboardHistoryApp
BUILD   := ClipboardHistory/.build/arm64-apple-macosx/debug
ICONS   := ClipboardHistory/.build/arm64-apple-macosx/debug/ClipboardHistory_ClipboardHistoryApp.bundle/AppIcon.icns

.PHONY: build run clean bundle

build:
	cd ClipboardHistory && swift build

bundle: build
	rm -rf "$(BUNDLE)"
	mkdir -p "$(BUNDLE)/Contents/MacOS"
	mkdir -p "$(BUNDLE)/Contents/Resources"
	cp "$(BUILD)/$(BINARY)" "$(BUNDLE)/Contents/MacOS/$(BINARY)"
	cp "$(ICONS)" "$(BUNDLE)/Contents/Resources/AppIcon.icns" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Add :CFBundleExecutable string $(BINARY)" "$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Set :CFBundleExecutable $(BINARY)" "$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Add :CFBundleIdentifier string com.clipboardhistory.app" "$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Set :CFBundleIdentifier com.clipboardhistory.app" "$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Add :CFBundleName string $(APP_NAME)" "$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Set :CFBundleName $(APP_NAME)" "$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Add :CFBundleVersion string 1" "$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Add :CFBundleShortVersionString string 1.0" "$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Add :CFBundleIconFile string AppIcon" "$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Set :CFBundleIconFile AppIcon" "$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Add :LSMinimumSystemVersion string 15.0" "$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	/usr/libexec/PlistBuddy -c "Add :NSHighResolutionCapable bool true" "$(BUNDLE)/Contents/Info.plist" 2>/dev/null || true
	touch "$(BUNDLE)"
	@echo "✅ $(BUNDLE) ready"

run: bundle
	open "$(BUNDLE)"

clean:
	rm -rf "$(BUNDLE)"
	cd ClipboardHistory && swift package clean
