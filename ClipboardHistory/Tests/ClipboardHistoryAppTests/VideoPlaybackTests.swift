import AVFoundation
import CoreGraphics
import XCTest
@testable import ClipboardHistoryApp

final class VideoPlaybackTimeFormatterTests: XCTestCase {
    func testFormatsShortAndLongDurations() {
        XCTAssertEqual(VideoPlaybackTimeFormatter.string(from: 0), "00:00")
        XCTAssertEqual(VideoPlaybackTimeFormatter.string(from: 9.4), "00:09")
        XCTAssertEqual(VideoPlaybackTimeFormatter.string(from: 125), "02:05")
        XCTAssertEqual(VideoPlaybackTimeFormatter.string(from: 3_665), "1:01:05")
    }

    func testInvalidDurationsFallBackToZero() {
        XCTAssertEqual(VideoPlaybackTimeFormatter.string(from: .nan), "00:00")
        XCTAssertEqual(VideoPlaybackTimeFormatter.string(from: .infinity), "00:00")
        XCTAssertEqual(VideoPlaybackTimeFormatter.string(from: -12), "00:00")
    }
}

final class VideoPlaybackMetricsTests: XCTestCase {
    func testControlsReserveSpaceForFloatingActions() {
        XCTAssertGreaterThanOrEqual(
            VideoPlaybackMetrics.controlsTrailingPadding,
            VideoPlaybackMetrics.floatingActionsWidth + VideoPlaybackMetrics.floatingActionsTrailingPadding
        )
    }

    func testControlContentWidthAvoidsReservedActionArea() {
        let containerWidth: CGFloat = 520
        let contentWidth = VideoPlaybackMetrics.controlContentWidth(for: containerWidth)

        XCTAssertEqual(
            contentWidth,
            containerWidth - VideoPlaybackMetrics.controlsLeadingPadding - VideoPlaybackMetrics.controlsTrailingPadding
        )
    }

    func testControlContentWidthDoesNotBecomeNegative() {
        XCTAssertEqual(VideoPlaybackMetrics.controlContentWidth(for: 20), 0)
    }
}

@MainActor
final class VideoPlaybackControllerTests: XCTestCase {
    func testStopUnloadsCurrentPlayerItemAndResetsPlaybackState() {
        let controller = VideoPlaybackController()
        let url = URL(fileURLWithPath: "/tmp/video.mov")

        controller.load(url)
        controller.seek(to: 12)
        XCTAssertNotNil(controller.player.currentItem)

        controller.stop()

        XCTAssertNil(controller.player.currentItem)
        XCTAssertEqual(controller.currentTime, 0)
        XCTAssertEqual(controller.duration, 0)
        XCTAssertFalse(controller.isPlaying)
    }

    func testLoadingDifferentURLReplacesCurrentPlayerItem() {
        let controller = VideoPlaybackController()
        let firstURL = URL(fileURLWithPath: "/tmp/first.mov")
        let secondURL = URL(fileURLWithPath: "/tmp/second.mov")

        controller.load(firstURL)
        let firstItem = controller.player.currentItem

        controller.load(secondURL)
        let secondItem = controller.player.currentItem

        XCTAssertNotNil(firstItem)
        XCTAssertNotNil(secondItem)
        XCTAssertFalse(firstItem === secondItem)
    }
}

final class VideoAspectRatioResolverTests: XCTestCase {
    func testUsesNaturalLandscapeAspectRatio() {
        let ratio = VideoAspectRatioResolver.aspectRatio(naturalSize: CGSize(width: 1920, height: 1080))

        XCTAssertNotNil(ratio)
        XCTAssertEqual(
            ratio ?? 0,
            16.0 / 9.0,
            accuracy: 0.0001
        )
    }

    func testAppliesPreferredTransformForRotatedPortraitVideo() {
        let ratio = VideoAspectRatioResolver.aspectRatio(
            naturalSize: CGSize(width: 1920, height: 1080),
            preferredTransform: CGAffineTransform(rotationAngle: .pi / 2)
        )

        XCTAssertNotNil(ratio)
        XCTAssertEqual(
            ratio ?? 0,
            9.0 / 16.0,
            accuracy: 0.0001
        )
    }

    func testRejectsEmptySizes() {
        XCTAssertNil(VideoAspectRatioResolver.aspectRatio(naturalSize: .zero))
    }
}
