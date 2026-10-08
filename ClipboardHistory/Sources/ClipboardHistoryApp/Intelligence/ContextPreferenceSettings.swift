import Foundation

@MainActor
final class ContextPreferenceSettings: ObservableObject {
    @Published var canReadWindowTitle: Bool {
        didSet {
            guard oldValue != canReadWindowTitle else { return }
            UserDefaults.standard.set(canReadWindowTitle, forKey: Key.windowTitle)
        }
    }

    @Published var canReadBrowserDomain: Bool {
        didSet {
            guard oldValue != canReadBrowserDomain else { return }
            UserDefaults.standard.set(canReadBrowserDomain, forKey: Key.browserDomain)
        }
    }

    @Published var canReadFinderDirectory: Bool {
        didSet {
            guard oldValue != canReadFinderDirectory else { return }
            UserDefaults.standard.set(canReadFinderDirectory, forKey: Key.finderDirectory)
        }
    }

    @Published var canReadFinderSelection: Bool {
        didSet {
            guard oldValue != canReadFinderSelection else { return }
            UserDefaults.standard.set(canReadFinderSelection, forKey: Key.finderSelection)
        }
    }

    @Published var canFilterSensitiveContent: Bool {
        didSet {
            guard oldValue != canFilterSensitiveContent else { return }
            UserDefaults.standard.set(canFilterSensitiveContent, forKey: Key.filterSensitive)
        }
    }

    var permissionState: ContextPermissionState {
        ContextPermissionState(
            canReadFrontmostApplication: true,
            canReadWindowTitle: canReadWindowTitle,
            canReadBrowserDomain: canReadBrowserDomain,
            canReadFinderDirectory: canReadFinderDirectory,
            canReadFinderSelection: canReadFinderSelection
        )
    }

    init() {
        let defaults = UserDefaults.standard
        canReadWindowTitle = defaults.bool(forKey: Key.windowTitle)
        canReadBrowserDomain = defaults.bool(forKey: Key.browserDomain)
        canReadFinderDirectory = defaults.bool(forKey: Key.finderDirectory)
        canReadFinderSelection = defaults.bool(forKey: Key.finderSelection)
        canFilterSensitiveContent = defaults.object(forKey: Key.filterSensitive) == nil
            ? true  // 默认开启
            : defaults.bool(forKey: Key.filterSensitive)
    }

    private enum Key {
        static let windowTitle = "ContextPreference.windowTitle"
        static let browserDomain = "ContextPreference.browserDomain"
        static let finderDirectory = "ContextPreference.finderDirectory"
        static let finderSelection = "ContextPreference.finderSelection"
        static let filterSensitive = "ContextPreference.filterSensitive"
    }
}
