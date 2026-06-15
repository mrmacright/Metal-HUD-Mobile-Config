import Foundation

struct AppState: Codable {
    var hudSettings: HUDSettings = HUDSettings()
    var analyticsOptIn: Bool? = nil
    var analyticsPromptLaunchCount: Int = 0
    var firstDeviceScanNoticeShown: Bool = false
    var windowGeometry: String? = nil
    var lastDeviceScan: [Device] = []
    var selectedLibrary: String = ""
    var libraryPanelOpen: Bool = false
    var logPanelOpen: Bool = true
    var hiddenApps: [String] = []
    var pinnedApps: [String] = []
    var agreementsAccepted: Bool = false
    var performanceResultsOpen: Bool = false
    var commandHistory: [CommandHistoryEntry] = []
    var savedGames: [SavedGame] = []
    var detectedBundleIDs: [String: String] = [:]  // internalName → bundle ID, persisted from console detection
    var detectedPathNames: [String: String] = [:]  // appPath → displayName, for generic-named apps (avoids cross-app pollution)

    init() {}

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        hudSettings             = (try? c.decode(HUDSettings.self,              forKey: .hudSettings))             ?? HUDSettings()
        analyticsOptIn          =  try? c.decodeIfPresent(Bool.self,             forKey: .analyticsOptIn)
        analyticsPromptLaunchCount = (try? c.decodeIfPresent(Int.self,          forKey: .analyticsPromptLaunchCount)) ?? 0
        firstDeviceScanNoticeShown = (try? c.decodeIfPresent(Bool.self,         forKey: .firstDeviceScanNoticeShown)) ?? false
        windowGeometry          =  try? c.decodeIfPresent(String.self,           forKey: .windowGeometry)
        lastDeviceScan          = (try? c.decodeIfPresent([Device].self,         forKey: .lastDeviceScan))          ?? []
        selectedLibrary         = (try? c.decodeIfPresent(String.self,           forKey: .selectedLibrary))         ?? ""
        libraryPanelOpen        = (try? c.decodeIfPresent(Bool.self,             forKey: .libraryPanelOpen))        ?? false
        logPanelOpen            = (try? c.decodeIfPresent(Bool.self,             forKey: .logPanelOpen))            ?? true
        hiddenApps              = (try? c.decodeIfPresent([String].self,         forKey: .hiddenApps))              ?? []
        pinnedApps              = (try? c.decodeIfPresent([String].self,         forKey: .pinnedApps))              ?? []
        agreementsAccepted      = (try? c.decodeIfPresent(Bool.self,             forKey: .agreementsAccepted))      ?? false
        performanceResultsOpen  = (try? c.decodeIfPresent(Bool.self,             forKey: .performanceResultsOpen))  ?? false
        commandHistory          = (try? c.decodeIfPresent([CommandHistoryEntry].self, forKey: .commandHistory))     ?? []
        savedGames              = (try? c.decodeIfPresent([SavedGame].self,      forKey: .savedGames))              ?? []
        detectedBundleIDs       = (try? c.decodeIfPresent([String: String].self, forKey: .detectedBundleIDs))      ?? [:]
        detectedPathNames       = (try? c.decodeIfPresent([String: String].self, forKey: .detectedPathNames))      ?? [:]
    }
}

@MainActor
final class PersistenceService {
    static let shared = PersistenceService()

    private let dataURL: URL

    private init() {
        dataURL = PersistenceService.resolveDataURL()
        print("[MetalHUD] Data path: \(dataURL.path)")
    }

    private static func resolveDataURL() -> URL {
        #if canImport(AppKit)
        let containerDir = FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent("Library/Containers/com.stewie.metalhud/Data/Library/Application Support/com.stewie.metalhud")
        if FileManager.default.fileExists(atPath: containerDir.path) {
            return containerDir.appendingPathComponent("data.json")
        }
        #endif
        let appSupport = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
        let dir = appSupport.appendingPathComponent("com.stewie.metalhud")
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        return dir.appendingPathComponent("data.json")
    }

    func load() -> AppState {
        guard FileManager.default.fileExists(atPath: dataURL.path),
              let data = try? Data(contentsOf: dataURL) else {
            return AppState()
        }

        // Try Swift camelCase format first
        if let state = try? JSONDecoder().decode(AppState.self, from: data) {
            return state
        }

        // Fall back: migrate from old Python snake_case format
        return migrateFromPython(data)
    }

    func save(_ state: AppState) {
        do {
            let data = try JSONEncoder().encode(state)
            try data.write(to: dataURL, options: .atomicWrite)
        } catch {
            print("[MetalHUD] Save error: \(error)")
        }
    }

    private func migrateFromPython(_ data: Data) -> AppState {
        guard let raw = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            return AppState()
        }
        var state = AppState()
        state.agreementsAccepted     = raw["agreements_accepted"]          as? Bool   ?? false
        state.analyticsOptIn         = raw["analytics_opt_in"]             as? Bool
        state.analyticsPromptLaunchCount = raw["analytics_prompt_launch_count"] as? Int ?? 0
        state.firstDeviceScanNoticeShown = raw["first_device_scan_notice_shown"] as? Bool ?? false
        state.selectedLibrary        = raw["selected_library"]             as? String ?? ""
        state.libraryPanelOpen       = raw["library_panel_open"]           as? Bool   ?? false
        state.hiddenApps             = raw["hidden_apps"]                  as? [String] ?? []
        state.pinnedApps             = raw["pinned_apps"]                  as? [String] ?? []
        state.performanceResultsOpen = raw["performance_results_open"]     as? Bool   ?? false

        if let scanRaw = raw["last_device_scan"] as? [[String: Any]] {
            state.lastDeviceScan = scanRaw.compactMap { d in
                guard let name  = d["name"]       as? String,
                      let id    = d["identifier"] as? String,
                      let st    = d["state"]      as? String,
                      let model = d["model"]      as? String else { return nil }
                return Device(name: name, identifier: id, state: st, model: model)
            }
        }

        print("[MetalHUD] Migrated from Python format — overwriting with Swift format")
        save(state)  // immediately overwrite so next launch uses the Swift format
        return state
    }
}
