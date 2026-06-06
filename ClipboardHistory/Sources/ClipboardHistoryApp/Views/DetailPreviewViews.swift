import Quartz
import SwiftUI

struct QuickLookPreview: NSViewRepresentable {
    let url: URL

    func makeNSView(context: Context) -> QLPreviewView {
        let view = QLPreviewView()
        view.autostarts = true
        return view
    }

    func updateNSView(_ nsView: QLPreviewView, context: Context) {
        nsView.previewItem = url as QLPreviewItem
    }
}

struct DetailFileView: View {
    let url: URL
    let thumbnail: StoredImage?

    private var fileExtension: String { url.pathExtension.lowercased() }

    private var isImageFile: Bool {
        FileTypeSupport.imageExtensions.contains(fileExtension)
    }

    private var isVideoFile: Bool {
        FileTypeSupport.videoExtensions.contains(fileExtension)
    }

    private var isTextFile: Bool {
        FileTypeSupport.textExtensions.contains(fileExtension)
    }

    private var isDocumentFile: Bool {
        FileTypeSupport.documentExtensions.contains(fileExtension)
    }

    var body: some View {
        if isImageFile, let nsImage = NSImage(contentsOf: url) {
            ImagePreviewView(nsImage: nsImage)
        } else if isTextFile {
            textPreview
        } else if isDocumentFile || isVideoFile {
            documentPreview
        } else {
            fallbackView
        }
    }

    private var textPreview: some View {
        Group {
            if let content = try? String(contentsOf: url, encoding: .utf8) {
                ScrollView([.vertical, .horizontal]) {
                    Text(content)
                        .font(.system(size: 13, design: .monospaced))
                        .foregroundStyle(.primary)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(20)
                        .textSelection(.enabled)
                }
            } else {
                fallbackView
            }
        }
    }

    private var documentPreview: some View {
        QuickLookPreview(url: url)
    }

    private var fallbackView: some View {
        VStack(spacing: 16) {
            if let thumb = thumbnail {
                Image(nsImage: thumb.nsImage)
                    .resizable()
                    .aspectRatio(contentMode: .fit)
                    .frame(width: 128, height: 128)
            } else {
                Image(systemName: "doc.fill")
                    .font(.system(size: 48))
                    .foregroundStyle(.quaternary)
            }
            Text(url.lastPathComponent)
                .font(.system(size: 14))
            Text(url.path)
                .font(.system(size: 11))
                .foregroundStyle(.secondary)
                .textSelection(.enabled)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}
