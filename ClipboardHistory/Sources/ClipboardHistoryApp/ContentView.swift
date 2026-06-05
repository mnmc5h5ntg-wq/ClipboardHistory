import SwiftUI
import Quartz

struct ContentView: View {
    @ObservedObject var manager: ClipboardManager

    var body: some View {
        if #available(macOS 13, *) {
            NavigationSplitView {
                sidebar
                    .navigationSplitViewColumnWidth(min: 220, ideal: 260, max: 320)
            } detail: {
                detailView
            }
            .navigationTitle("")
            .windowBackground()
        } else {
            NavigationView {
                sidebar
                    .frame(minWidth: 220, idealWidth: 260, maxWidth: 320)
                detailView
            }
            .navigationTitle("")
            .windowBackground()
        }
    }

    @ViewBuilder private var sidebar: some View {
        VStack(spacing: 0) {
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass").foregroundStyle(.secondary)
                TextField("搜索历史…", text: Binding(get: { manager.searchText }, set: { manager.updateSearch($0) }))
                    .textFieldStyle(.plain).font(.system(size: 13))
                if !manager.searchText.isEmpty {
                    Button(action: { manager.updateSearch("") }) {
                        Image(systemName: "xmark.circle.fill").foregroundStyle(.secondary)
                    }.buttonStyle(.plain)
                }
            }.padding(.horizontal, 12).padding(.vertical, 10)
            Divider()
            HStack {
                Text("时间剪史").font(.system(size: 16, weight: .semibold)).foregroundStyle(.secondary)
                Spacer()
                Text("\(manager.filteredEntries.count) 条记录").font(.system(size: 15, weight: .regular)).foregroundStyle(.tertiary)
                if !manager.entries.isEmpty {
                    GlassCircleButton(symbol: "trash.slash", helpText: "清空全部") {
                        manager.clearAll()
                    }
                    .padding(.leading, 6)
                }
            }.padding(.horizontal, 16).padding(.vertical, 8)
            if manager.filteredEntries.isEmpty {
                VStack(spacing: 12) {
                    Image(systemName: "clipboard").font(.system(size: 28)).foregroundStyle(.quaternary)
                    Text("暂无剪贴板历史").font(.system(size: 13)).foregroundStyle(.tertiary)
                }.frame(maxWidth: .infinity, maxHeight: .infinity).padding(.vertical, 40)
                Spacer()
            } else {
                ScrollView {
                    LazyVStack(spacing: 0) {
                        ForEach(manager.filteredEntries) { entry in
                            Button(action: { manager.selectedEntry = entry }) {
                                HistoryRow(entry: entry, selected: manager.selectedEntry?.id == entry.id)
                                    .padding(.horizontal, 12).padding(.vertical, 8)
                                    .frame(maxWidth: .infinity, alignment: .leading)
                                    .background(manager.selectedEntry?.id == entry.id ? Color.accentColor.opacity(0.15) : .clear)
                                    .contentShape(Rectangle())
                            }.buttonStyle(.plain)
                            Divider().padding(.leading, 12)
                        }
                    }
                }
            }
        }
    }

    @ViewBuilder private var detailView: some View {
        if let entry = manager.selectedEntry {
            VStack(spacing: 0) {
                HStack {
                    Spacer()
                    VStack(alignment: .center, spacing: 2) {
                        Text("于 \(entry.timestamp.formatted(date: .omitted, time: .shortened)) 复制")
                            .font(.system(size: 11)).foregroundStyle(.secondary)
                        Text(entry.content.sizeDescription).font(.system(size: 11)).foregroundStyle(.tertiary)
                    }
                    Spacer()
                }.padding(.horizontal, 20).padding(.vertical, 12).background(.ultraThinMaterial)
                Divider()
                switch entry.content {
                case .text(let text):
                    ScrollView(.vertical) {
                        Text(text).font(.system(size: 14, design: .monospaced)).foregroundStyle(.primary)
                            .frame(maxWidth: .infinity, alignment: .leading).padding(20).textSelection(.enabled)
                    }
                case .image(let stored):
                    DetailImageView(storedImage: stored)
                case .file(let url):
                    DetailFileView(url: url, thumbnail: entry.thumbnail)
                }
            }
            .ignoresSafeArea(edges: .top)
            .overlay(alignment: .bottomTrailing) {
                GlassPill(
                    copyAction: { manager.copyToClipboardAndBringToTop(entry) },
                    deleteAction: { manager.delete(entry) }
                )
                .padding(12)
            }
        } else {
            VStack(spacing: 16) {
                Image(systemName: "doc.on.clipboard").font(.system(size: 40)).foregroundStyle(.quaternary)
                Text("选择一条记录查看详情").font(.system(size: 14)).foregroundStyle(.tertiary)
            }.frame(maxWidth: .infinity, maxHeight: .infinity)
        }
    }


}

// MARK: - Detail Image View

struct DetailImageView: View {
    let storedImage: StoredImage
    @State private var containerSize: CGSize = .zero

    var body: some View {
        let img = storedImage.nsImage
        let _ = dbg("[DETAIL] oid=\(ObjectIdentifier(img)) type=\(type(of: img)) size=\(img.size)")

        GeometryReader { geo in
            ScrollView([.horizontal, .vertical]) {
                Image(nsImage: img)
                    .resizable()
                    .scaledToFit()
                    .frame(
                        maxWidth: max(geo.size.width - 40, 100),
                        maxHeight: max(geo.size.height - 40, 100)
                    )
                    .padding(20)
            }
            .onAppear {
                containerSize = geo.size
                dbg("[DETAIL.Geo] container=\(geo.size)")
            }
        }
    }
}

// MARK: - QuickLook Preview (NSView wrapper)

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

// MARK: - Detail File View

struct DetailFileView: View {
    let url: URL
    let thumbnail: StoredImage?

    private var fileExtension: String { url.pathExtension.lowercased() }

    private var isImageFile: Bool {
        ["png", "jpg", "jpeg", "gif", "bmp", "tiff", "tif", "heic", "webp", "ico"].contains(fileExtension)
    }

    private var isTextFile: Bool {
        ["txt", "md", "csv", "json", "xml", "html", "css", "js", "ts",
         "swift", "py", "rb", "go", "rs", "c", "h", "cpp", "java", "sh",
         "yaml", "yml", "toml", "ini", "cfg", "log", "plist", "strings",
         "svg", "tex", "r", "sql", "php", "scala", "kt", "hs", "lua",
         "mm", "m", "hpp", "vue", "svelte", "astro", "jsx", "tsx", "gradle",
         "cmake", "makefile", "dockerfile", "gitignore", "env"].contains(fileExtension)
    }

    private var isDocumentFile: Bool {
        ["docx", "doc", "pdf", "xlsx", "xls", "pptx", "ppt",
         "pages", "numbers", "keynote", "odt", "ods", "odp",
         "rtf", "rtfd"].contains(fileExtension)
    }

    var body: some View {
        if isImageFile, let nsImage = NSImage(contentsOf: url) {
            imagePreview(nsImage)
        } else if isTextFile {
            textPreview
        } else if isDocumentFile {
            documentPreview
        } else {
            fallbackView
        }
    }

    // MARK: - Image Preview

    private func imagePreview(_ nsImage: NSImage) -> some View {
        let _ = dbg("[FILE-DETAIL] loaded image from disk: \(url.path) size=\(nsImage.size)")
        return GeometryReader { geo in
            ScrollView([.horizontal, .vertical]) {
                Image(nsImage: nsImage)
                    .resizable()
                    .scaledToFit()
                    .frame(
                        maxWidth: max(geo.size.width - 40, 100),
                        maxHeight: max(geo.size.height - 40, 100)
                    )
                    .padding(20)
            }
        }
    }

    // MARK: - Text Preview

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

    // MARK: - Document Preview (QuickLook)

    private var documentPreview: some View {
        QuickLookPreview(url: url)
    }

    // MARK: - Fallback

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

// MARK: - Glass Circle Button

struct GlassCircleButton: View {
    let symbol: String
    let helpText: String
    let action: () -> Void
    @State private var isHovered = false

    var body: some View {
        Button(action: action) {
            Image(systemName: symbol)
                .font(.system(size: 16, weight: .medium))
                .frame(width: 40, height: 40)
                .background(
                    Circle()
                        .fill(.ultraThinMaterial)
                )
                .overlay(
                    Circle()
                        .stroke(.white.opacity(isHovered ? 0.4 : 0.15), lineWidth: 0.5)
                )
                .shadow(color: .black.opacity(isHovered ? 0.1 : 0.05), radius: isHovered ? 4 : 2, y: 1)
        }
        .buttonStyle(.plain)
        .scaleEffect(isHovered ? 1.05 : 1.0)
        .onHover { hovering in
            withAnimation(.easeInOut(duration: 0.15)) {
                isHovered = hovering
            }
        }
        .help(helpText)
    }
}

// MARK: - Glass Pill (胶囊操作按钮)

struct GlassPill: View {
    let copyAction: () -> Void
    let deleteAction: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            Button(action: copyAction) {
                Image(systemName: "doc.on.doc")
                    .font(.system(size: 18, weight: .medium))
                    .frame(width: 44, height: 44)
            }
            .buttonStyle(.plain)
            .help("再次复制")

            Rectangle()
                .fill(.white.opacity(0.15))
                .frame(width: 28, height: 1)

            Button(action: deleteAction) {
                Image(systemName: "trash")
                    .font(.system(size: 18, weight: .medium))
                    .frame(width: 44, height: 44)
            }
            .buttonStyle(.plain)
            .help("删除")
        }
        .background(
            Capsule()
                .fill(.ultraThinMaterial)
        )
        .overlay(
            Capsule()
                .stroke(.white.opacity(0.15), lineWidth: 0.5)
        )
        .shadow(color: .black.opacity(0.08), radius: 4, y: 2)
    }
}

// MARK: - History Row

struct HistoryRow: View {
    let entry: ClipboardManager.Entry
    let selected: Bool

    var body: some View {
        HStack(spacing: 8) {
            switch entry.content {
            case .text:
                Image(systemName: "doc.text")
                    .font(.system(size: 12)).foregroundStyle(.secondary).frame(width: 16)
            case .image(let stored):
                let img = stored.nsImage
                let _ = dbg("[SIDEBAR] oid=\(ObjectIdentifier(img)) type=\(type(of: img)) size=\(img.size)")

                Image(nsImage: img)
                    .resizable()
                    .aspectRatio(contentMode: .fill)
                    .frame(width: 16, height: 16)
                    .clipShape(RoundedRectangle(cornerRadius: 3))
                    .overlay(RoundedRectangle(cornerRadius: 3).stroke(Color.blue.opacity(0.3), lineWidth: 1))
            case .file:
                if let thumb = entry.thumbnail {
                    let _ = dbg("[SIDEBAR-FILE] thumb oid=\(ObjectIdentifier(thumb.nsImage)) size=\(thumb.nsImage.size)")
                    Image(nsImage: thumb.nsImage)
                        .resizable()
                        .aspectRatio(contentMode: .fill)
                        .frame(width: 16, height: 16)
                        .clipShape(RoundedRectangle(cornerRadius: 3))
                        .overlay(RoundedRectangle(cornerRadius: 3).stroke(Color.green.opacity(0.3), lineWidth: 1))
                } else {
                    Image(systemName: "doc")
                        .font(.system(size: 12)).foregroundStyle(.secondary).frame(width: 16)
                }
            }
            VStack(alignment: .leading, spacing: 2) {
                Text(entry.shortPreview)
                    .font(.system(size: 12)).lineLimit(2).truncationMode(.tail)
                Text(entry.timestamp, style: .relative)
                    .font(.system(size: 10)).foregroundStyle(.tertiary)
            }
        }
    }
}


// MARK: - Window Background (macOS 12/15 compat)

extension View {
    @ViewBuilder
    func windowBackground() -> some View {
        if #available(macOS 15, *) {
            self.containerBackground(.thickMaterial, for: .window)
        } else {
            self.background(.thickMaterial)
        }
    }
}
