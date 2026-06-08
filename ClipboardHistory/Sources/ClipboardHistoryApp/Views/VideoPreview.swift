import AVFoundation
import SwiftUI

enum VideoPlaybackMetrics {
    static let controlsLeadingPadding: CGFloat = 12
    static let floatingActionsWidth: CGFloat = 52
    static let floatingActionsTrailingPadding: CGFloat = 12
    static let controlsActionGap: CGFloat = 16
    static let minimumTimelineWidth: CGFloat = 56

    static var controlsTrailingPadding: CGFloat {
        floatingActionsWidth + floatingActionsTrailingPadding + controlsActionGap
    }

    static func controlContentWidth(for containerWidth: CGFloat) -> CGFloat {
        max(containerWidth - controlsLeadingPadding - controlsTrailingPadding, 0)
    }
}

enum VideoPlaybackTimeFormatter {
    static func string(from seconds: Double) -> String {
        guard seconds.isFinite, seconds > 0 else { return "00:00" }

        let roundedSeconds = Int(seconds.rounded())
        let hours = roundedSeconds / 3_600
        let minutes = (roundedSeconds % 3_600) / 60
        let seconds = roundedSeconds % 60

        if hours > 0 {
            return String(format: "%d:%02d:%02d", hours, minutes, seconds)
        }
        return String(format: "%02d:%02d", minutes, seconds)
    }
}

@MainActor
final class VideoPlaybackController: ObservableObject {
    let player = AVPlayer()
    @Published private(set) var currentTime: Double = 0
    @Published private(set) var duration: Double = 0
    @Published private(set) var isPlaying = false
    @Published private(set) var isMuted = true

    private var currentURL: URL?
    private var timeObserver: Any?
    private var timeControlObserver: NSKeyValueObservation?

    init() {
        player.isMuted = true
        timeControlObserver = player.observe(\.timeControlStatus, options: [.initial, .new]) { [weak self] player, _ in
            Task { @MainActor [weak self] in
                self?.isPlaying = player.timeControlStatus == .playing
            }
        }
    }

    func load(_ url: URL) {
        guard currentURL != url else { return }
        unloadCurrentItem()
        ensureTimeObserver()
        currentURL = url
        currentTime = 0
        duration = 0
        isMuted = true

        player.replaceCurrentItem(with: AVPlayerItem(url: url))
        player.isMuted = true
        player.play()
    }

    func togglePlayback() {
        if player.timeControlStatus == .playing {
            player.pause()
        } else {
            player.play()
        }
    }

    func seek(to seconds: Double) {
        let safeDuration = duration > 0 ? duration : seconds
        let clampedSeconds = min(max(seconds, 0), max(safeDuration, 0))
        currentTime = clampedSeconds
        player.seek(
            to: CMTime(seconds: clampedSeconds, preferredTimescale: 600),
            toleranceBefore: .zero,
            toleranceAfter: .zero
        )
    }

    func toggleMuted() {
        player.isMuted.toggle()
        isMuted = player.isMuted
    }

    func pause() {
        player.pause()
        isPlaying = false
    }

    func stop() {
        unloadCurrentItem()
    }

    private func unloadCurrentItem() {
        player.pause()
        if let timeObserver {
            player.removeTimeObserver(timeObserver)
            self.timeObserver = nil
        }
        player.replaceCurrentItem(with: nil)
        currentURL = nil
        currentTime = 0
        duration = 0
        isPlaying = false
    }

    private func updatePlaybackTime(_ time: CMTime) {
        currentTime = time.seconds.isFinite ? time.seconds : 0
        if let itemDuration = player.currentItem?.duration.seconds,
           itemDuration.isFinite,
           itemDuration > 0 {
            duration = itemDuration
        }
    }

    private func ensureTimeObserver() {
        guard timeObserver == nil else { return }
        timeObserver = player.addPeriodicTimeObserver(
            forInterval: CMTime(seconds: 0.2, preferredTimescale: 600),
            queue: .main
        ) { [weak self] time in
            Task { @MainActor [weak self] in
                self?.updatePlaybackTime(time)
            }
        }
    }
}

struct VideoPreview: View {
    let url: URL
    let aspectRatio: CGFloat
    @StateObject private var playback = VideoPlaybackController()

    var body: some View {
        VStack(spacing: 0) {
            ZStack {
                VideoPlayerSurface(player: playback.player)
                    .aspectRatio(aspectRatio, contentMode: .fit)
                    .padding(.horizontal, 20)
                    .padding(.top, 16)
                    .padding(.bottom, 10)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)

            VideoPlaybackControls(playback: playback)
                .padding(.leading, VideoPlaybackMetrics.controlsLeadingPadding)
                .padding(.trailing, VideoPlaybackMetrics.controlsTrailingPadding)
                .padding(.bottom, 12)
        }
        .background(Color.clear)
        .onAppear {
            playback.load(url)
        }
        .onChange(of: url) { newURL in
            playback.load(newURL)
        }
        .onReceive(NotificationCenter.default.publisher(for: .mainWindowDidHide)) { _ in
            playback.pause()
        }
        .onDisappear {
            playback.stop()
        }
    }
}

private struct VideoPlayerSurface: NSViewRepresentable {
    let player: AVPlayer

    func makeNSView(context: Context) -> PlayerLayerView {
        let view = PlayerLayerView()
        view.playerLayer.player = player
        return view
    }

    func updateNSView(_ nsView: PlayerLayerView, context: Context) {
        nsView.playerLayer.player = player
    }

    static func dismantleNSView(_ nsView: PlayerLayerView, coordinator: ()) {
        nsView.playerLayer.player = nil
    }

    final class PlayerLayerView: NSView {
        let playerLayer = AVPlayerLayer()

        override init(frame frameRect: NSRect) {
            super.init(frame: frameRect)
            wantsLayer = true
            layer?.backgroundColor = NSColor.clear.cgColor
            layer?.addSublayer(playerLayer)
            playerLayer.videoGravity = .resizeAspect
            playerLayer.backgroundColor = NSColor.clear.cgColor
        }

        required init?(coder: NSCoder) {
            fatalError("init(coder:) has not been implemented")
        }

        override var isOpaque: Bool { false }

        override func layout() {
            super.layout()
            playerLayer.frame = bounds
        }
    }
}

private struct VideoPlaybackControls: View {
    @ObservedObject var playback: VideoPlaybackController

    var body: some View {
        HStack(spacing: 8) {
            Button(action: playback.togglePlayback) {
                Image(systemName: playback.isPlaying ? "pause.fill" : "play.fill")
                    .font(.system(size: 16, weight: .semibold))
                    .frame(width: 22, height: 22)
            }
            .buttonStyle(.plain)
            .help(playback.isPlaying ? "暂停" : "播放")

            Text(VideoPlaybackTimeFormatter.string(from: playback.currentTime))
                .font(.system(size: 12, design: .monospaced))
                .foregroundStyle(.secondary)
                .lineLimit(1)
                .minimumScaleFactor(0.85)
                .frame(width: 46, alignment: .trailing)

            Slider(
                value: Binding(
                    get: { playback.currentTime },
                    set: { playback.seek(to: $0) }
                ),
                in: 0...max(playback.duration, 1)
            )
            .frame(minWidth: VideoPlaybackMetrics.minimumTimelineWidth)
            .help("调整播放进度")

            Text(VideoPlaybackTimeFormatter.string(from: playback.duration))
                .font(.system(size: 12, design: .monospaced))
                .foregroundStyle(.secondary)
                .frame(width: 45, alignment: .leading)

            Button(action: playback.toggleMuted) {
                Image(systemName: playback.isMuted ? "speaker.slash.fill" : "speaker.wave.2.fill")
                    .font(.system(size: 15, weight: .semibold))
                    .frame(width: 22, height: 22)
            }
            .buttonStyle(.plain)
            .help(playback.isMuted ? "取消静音" : "静音")
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 8)
        .frame(maxWidth: .infinity)
        .background(.ultraThinMaterial, in: Capsule())
        .overlay(
            Capsule()
                .strokeBorder(.white.opacity(0.18), lineWidth: 0.7)
        )
        .shadow(color: .black.opacity(0.08), radius: 8, y: 3)
    }
}
