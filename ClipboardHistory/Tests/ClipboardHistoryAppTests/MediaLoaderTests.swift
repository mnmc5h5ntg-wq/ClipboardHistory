import AppKit
import XCTest
@testable import ClipboardHistoryApp

@MainActor
final class MediaLoaderTests: XCTestCase {
    func testLoadFilePreviewSyncLoadsTextFiles() throws {
        let url = try temporaryFile(named: "note.txt", contents: "hello preview")

        let preview = try XCTUnwrap(MediaLoader.loadFilePreviewSync(url: url, thumbnail: nil))

        guard case .text(let text) = preview.content else {
            return XCTFail("Expected text preview")
        }
        XCTAssertEqual(text, "hello preview")
    }

    func testLoadFilePreviewSyncLoadsImageFiles() throws {
        let url = try temporaryImageFile(named: "pixel.png")

        let preview = try XCTUnwrap(MediaLoader.loadFilePreviewSync(url: url, thumbnail: nil))

        guard case .image(let image) = preview.content else {
            return XCTFail("Expected image preview")
        }
        XCTAssertEqual(Int(image.size.width), 1)
        XCTAssertEqual(Int(image.size.height), 1)
    }

    func testLoadFilePreviewSyncUsesQuickLookForDocuments() throws {
        let url = try temporaryFile(named: "document.pdf", contents: "%PDF")

        let preview = try XCTUnwrap(MediaLoader.loadFilePreviewSync(url: url, thumbnail: nil))

        guard case .quickLook = preview.content else {
            return XCTFail("Expected QuickLook preview for document")
        }
    }

    func testLoadFilePreviewSyncUsesNativePreviewForVideos() throws {
        let url = try temporaryFile(named: "clip.mov", contents: "placeholder")

        let preview = try XCTUnwrap(MediaLoader.loadFilePreviewSync(url: url, thumbnail: nil))

        guard case .video = preview.content else {
            return XCTFail("Expected native video preview for video")
        }
    }

    func testLoadFilePreviewSyncFallsBackForUnknownExtensions() throws {
        let url = try temporaryFile(named: "archive.unknown", contents: "opaque")

        let preview = try XCTUnwrap(MediaLoader.loadFilePreviewSync(url: url, thumbnail: nil))

        guard case .fallback = preview.content else {
            return XCTFail("Expected fallback preview")
        }
    }

    func testLoadFilePreviewAsyncReturnsSuccess() async throws {
        let url = try temporaryFile(named: "async.md", contents: "# Title")

        let state = await MediaLoader.loadFilePreview(url: url, thumbnail: nil)

        guard case .success(let preview) = state,
              case .text(let text) = preview.content else {
            return XCTFail("Expected async text preview")
        }
        XCTAssertEqual(text, "# Title")
    }

    func testFilePreviewPayloadForImagesCarriesDataOnly() throws {
        let url = try temporaryImageFile(named: "payload.png")

        let payload = try XCTUnwrap(MediaLoader.filePreviewPayloadSync(url: url))

        guard case .imageData(let data) = payload else {
            return XCTFail("Expected image data payload")
        }
        XCTAssertFalse(data.isEmpty)
    }

    func testLoadFilePreviewSyncReturnsNilForMissingFiles() {
        let url = missingTemporaryFileURL(extension: "mov")

        let preview = MediaLoader.loadFilePreviewSync(url: url, thumbnail: nil)

        XCTAssertNil(preview)
    }

    func testLoadFilePreviewAsyncReturnsFailureForMissingFiles() async {
        let url = missingTemporaryFileURL(extension: "mov")

        let state = await MediaLoader.loadFilePreview(url: url, thumbnail: nil)

        guard case .failure(let message) = state else {
            return XCTFail("Expected missing file preview to fail")
        }
        XCTAssertEqual(message, MediaLoader.missingFileMessage)
    }

    func testLoadFilePreviewHandleCanBeCancelled() async throws {
        let url = try temporaryFile(named: "cancel.txt", contents: "slow")
        let handle = MediaLoader.loadFilePreviewHandle(url: url, thumbnail: nil) { url in
            try? await Task.sleep(nanoseconds: 1_000_000_000)
            return MediaLoader.filePreviewPayloadSync(url: url)
        }

        handle.cancel()
        let state = await handle.value

        guard case .failure(let message) = state else {
            return XCTFail("Expected cancelled loading to fail")
        }
        XCTAssertEqual(message, MediaLoader.cancellationMessage)
    }

    private func temporaryFile(named name: String, contents: String) throws -> URL {
        let directory = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString, isDirectory: true)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        let url = directory.appendingPathComponent(name)
        try contents.write(to: url, atomically: true, encoding: .utf8)
        return url
    }

    private func temporaryImageFile(named name: String) throws -> URL {
        let directory = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString, isDirectory: true)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        let url = directory.appendingPathComponent(name)
        let image = NSImage(size: NSSize(width: 1, height: 1))
        image.lockFocus()
        NSColor.red.setFill()
        NSRect(x: 0, y: 0, width: 1, height: 1).fill()
        image.unlockFocus()
        guard let data = image.tiffRepresentation,
              let bitmap = NSBitmapImageRep(data: data),
              let png = bitmap.representation(using: .png, properties: [:]) else {
            throw NSError(domain: "MediaLoaderTests", code: 1)
        }
        try png.write(to: url)
        return url
    }

    private func missingTemporaryFileURL(extension pathExtension: String) -> URL {
        FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString)
            .appendingPathExtension(pathExtension)
    }
}
