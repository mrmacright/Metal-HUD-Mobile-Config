import Foundation

struct Device: Identifiable, Codable, Equatable {
    var id: String { identifier }
    let name: String
    let identifier: String
    var state: String
    let model: String

    enum ConnectionState: String {
        case availablePaired = "available (paired)"
        case availablePairing = "available (pairing)"
        case available = "available"
        case connected = "connected"
        case unavailable = "unavailable"
        case unsupported = "unsupported"
        case other
    }

    var sortPriority: Int {
        let normalized = displayState.lowercased()
        if normalized.hasPrefix("available (paired") { return 0 }
        if normalized.hasPrefix("available")         { return 1 }
        if normalized.hasPrefix("connect")             { return 2 }
        if state == "unsupported"                    { return 3 }
        if normalized.hasPrefix("unavailable")       { return 4 }
        return 99
    }

    var displayState: String {
        let raw = state
        let normalized = raw.lowercased()

        if normalized == "available (local)"        { return "This Device" }
        if normalized == "available"                { return "available (preparing)" }
        if normalized == "available (pairing)"      { return "available (pairing required)" }
        if normalized == "available (paired)"       { return "available (paired + wireless)" }
        if normalized.contains("no ddi")            { return "Connected (limited support)" }
        if normalized.hasPrefix("connected")        { return "Connected" }
        if normalized.hasPrefix("unavailable")      { return "unavailable (device offline)" }
        if normalized == "unsupported"              { return "Device Unsupported" }
        return raw
    }

    var deviceType: DeviceType {
        let normalized = DeviceModels.clean(model)
        if normalized.hasPrefix("Apple Vision")                                  { return .appleVisionPro }
        if normalized.hasPrefix("Apple TV") || normalized.hasPrefix("AppleTV")  { return .appleTV }
        if normalized.hasPrefix("Apple Watch") || normalized.hasPrefix("Watch") { return .appleWatch }
        if normalized.hasPrefix("iPad")                                          { return .iPad }
        if normalized.hasPrefix("iPhone")                                        { return .iPhone }
        return .unknown
    }

    enum DeviceType {
        case iPhone, iPad, appleTV, appleWatch, appleVisionPro, unknown
    }
}

extension Device: Comparable {
    static func < (lhs: Device, rhs: Device) -> Bool {
        if lhs.sortPriority != rhs.sortPriority {
            return lhs.sortPriority < rhs.sortPriority
        }
        return lhs.name.lowercased() < rhs.name.lowercased()
    }
}
