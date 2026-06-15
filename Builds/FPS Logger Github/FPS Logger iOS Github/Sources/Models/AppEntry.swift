import Foundation
#if canImport(AppKit)
import AppKit
#endif

struct AppEntry: Identifiable, Equatable {
    var id: String { appPath.isEmpty ? internalName : appPath }
    let internalName: String
    var displayName: String
    let appPath: String
    var detectedAt: Date = Date()
    #if canImport(AppKit)
    var icon: NSImage?
    #endif

    var metalHUDStatus: (text: String, isPositive: Bool)? {
        AppData.metalHUDStatus(internal: internalName, display: displayName)
    }

    var skipIconLookup: Bool {
        AppData.skipIconLookup.contains(internalName)
    }

    static func == (lhs: AppEntry, rhs: AppEntry) -> Bool {
        lhs.appPath == rhs.appPath && lhs.internalName == rhs.internalName
    }
}
