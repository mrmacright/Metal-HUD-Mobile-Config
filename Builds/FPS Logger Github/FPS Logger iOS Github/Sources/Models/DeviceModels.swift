import Foundation

enum DeviceModels {
    static let friendlyNames: [String: String] = [
        // iPhone XS / XR
        "iPhone11,2": "iPhone XS",
        "iPhone11,4": "iPhone XS Max",
        "iPhone11,6": "iPhone XS Max Global",
        "iPhone11,8": "iPhone XR",
        // iPhone 11
        "iPhone12,1": "iPhone 11",
        "iPhone12,3": "iPhone 11 Pro",
        "iPhone12,5": "iPhone 11 Pro Max",
        // iPhone 12
        "iPhone13,1": "iPhone 12 Mini",
        "iPhone13,2": "iPhone 12",
        "iPhone13,3": "iPhone 12 Pro",
        "iPhone13,4": "iPhone 12 Pro Max",
        // iPhone 13
        "iPhone14,2": "iPhone 13 Pro",
        "iPhone14,3": "iPhone 13 Pro Max",
        "iPhone14,4": "iPhone 13 Mini",
        "iPhone14,5": "iPhone 13",
        // iPhone SE
        "iPhone12,8": "iPhone SE (2nd generation)",
        "iPhone14,6": "iPhone SE (3rd generation)",
        // iPhone 14
        "iPhone14,7": "iPhone 14",
        "iPhone14,8": "iPhone 14 Plus",
        "iPhone15,2": "iPhone 14 Pro",
        "iPhone15,3": "iPhone 14 Pro Max",
        // iPhone 15
        "iPhone15,4": "iPhone 15",
        "iPhone15,5": "iPhone 15 Plus",
        "iPhone16,1": "iPhone 15 Pro",
        "iPhone16,2": "iPhone 15 Pro Max",
        // iPhone 16
        "iPhone17,1": "iPhone 16 Pro",
        "iPhone17,2": "iPhone 16 Pro Max",
        "iPhone17,3": "iPhone 16",
        "iPhone17,4": "iPhone 16 Plus",
        "iPhone17,5": "iPhone 16e",
        // iPhone 17
        "iPhone18,1": "iPhone 17 Pro",
        "iPhone18,2": "iPhone 17 Pro Max",
        "iPhone18,3": "iPhone 17",
        // iPhone Air
        "iPhone18,4": "iPhone Air",
        // iPad
        "iPad7,5":   "iPad (6th generation)",
        "iPad7,6":   "iPad (6th generation)",
        "iPad7,11":  "iPad (7th generation)",
        "iPad7,12":  "iPad (7th generation)",
        "iPad11,6":  "iPad (8th generation)",
        "iPad11,7":  "iPad (8th generation)",
        "iPad12,1":  "iPad (9th generation)",
        "iPad12,2":  "iPad (9th generation)",
        "iPad13,18": "iPad (10th generation)",
        "iPad13,19": "iPad (10th generation)",
        "iPad15,7":  "iPad (A16)",
        "iPad15,8":  "iPad (A16)",
        // iPad mini
        "iPad11,1": "iPad mini (5th generation)",
        "iPad11,2": "iPad mini (5th generation)",
        "iPad14,1": "iPad mini (6th generation)",
        "iPad14,2": "iPad mini (6th generation)",
        "iPad16,1": "iPad mini (A17 Pro)",
        "iPad16,2": "iPad mini (A17 Pro)",
        // iPad Air
        "iPad11,3":  "iPad Air (3rd generation)",
        "iPad11,4":  "iPad Air (3rd generation)",
        "iPad13,1":  "iPad Air (4th generation)",
        "iPad13,2":  "iPad Air (4th generation)",
        "iPad13,16": "iPad Air (5th generation)",
        "iPad13,17": "iPad Air (5th generation)",
        "iPad14,8":  "iPad Air 11-inch (M2)",
        "iPad14,9":  "iPad Air 11-inch (M2)",
        "iPad14,10": "iPad Air 13-inch (M2)",
        "iPad14,11": "iPad Air 13-inch (M2)",
        "iPad15,3":  "iPad Air 11-inch (M3)",
        "iPad15,4":  "iPad Air 11-inch (M3)",
        "iPad15,5":  "iPad Air 13-inch (M3)",
        "iPad15,6":  "iPad Air 13-inch (M3)",
        "iPad16,7":  "iPad Air 11-inch (M4)",
        "iPad16,8":  "iPad Air 11-inch (M4)",
        // iPad Pro
        "iPad7,1":   "iPad Pro (12.9-inch) (2nd generation)",
        "iPad7,2":   "iPad Pro (12.9-inch) (2nd generation)",
        "iPad7,3":   "iPad Pro (10.5-inch)",
        "iPad7,4":   "iPad Pro (10.5-inch)",
        "iPad8,1":   "iPad Pro (11-inch) (1st generation)",
        "iPad8,2":   "iPad Pro (11-inch) (1st generation)",
        "iPad8,3":   "iPad Pro (11-inch) (1st generation)",
        "iPad8,4":   "iPad Pro (11-inch) (1st generation)",
        "iPad8,5":   "iPad Pro (12.9-inch) (3rd generation)",
        "iPad8,6":   "iPad Pro (12.9-inch) (3rd generation)",
        "iPad8,7":   "iPad Pro (12.9-inch) (3rd generation)",
        "iPad8,8":   "iPad Pro (12.9-inch) (3rd generation)",
        "iPad8,9":   "iPad Pro (11-inch) (2nd generation)",
        "iPad8,10":  "iPad Pro (11-inch) (2nd generation)",
        "iPad8,11":  "iPad Pro (12.9-inch) (4th generation)",
        "iPad8,12":  "iPad Pro (12.9-inch) (4th generation)",
        "iPad13,4":  "iPad Pro (11-inch) (3rd generation)",
        "iPad13,5":  "iPad Pro (11-inch) (3rd generation)",
        "iPad13,6":  "iPad Pro (11-inch) (3rd generation)",
        "iPad13,7":  "iPad Pro (11-inch) (3rd generation)",
        "iPad13,8":  "iPad Pro (12.9-inch) (5th generation)",
        "iPad13,9":  "iPad Pro (12.9-inch) (5th generation)",
        "iPad13,10": "iPad Pro (12.9-inch) (5th generation)",
        "iPad13,11": "iPad Pro (12.9-inch) (5th generation)",
        "iPad14,3":  "iPad Pro (11-inch) (4th generation)",
        "iPad14,4":  "iPad Pro (11-inch) (4th generation)",
        "iPad14,5":  "iPad Pro (12.9-inch) (6th generation)",
        "iPad14,6":  "iPad Pro (12.9-inch) (6th generation)",
        "iPad16,3":  "iPad Pro 11-inch (M4)",
        "iPad16,4":  "iPad Pro 11-inch (M4)",
        "iPad16,5":  "iPad Pro 13-inch (M4)",
        "iPad16,6":  "iPad Pro 13-inch (M4)",
        "iPad17,1":  "iPad Pro 11-inch (M5)",
        "iPad17,2":  "iPad Pro 11-inch (M5)",
        "iPad17,3":  "iPad Pro 13-inch (M5)",
        "iPad17,4":  "iPad Pro 13-inch (M5)",
        // Apple TV
        "AppleTV5,3":  "Apple TV (4th generation)",
        "AppleTV6,2":  "Apple TV 4K",
        "AppleTV11,1": "Apple TV 4K (2nd generation)",
        "AppleTV14,1": "Apple TV 4K (3rd generation)",
    ]

    private static let friendlyToRaw: [String: String] = Dictionary(
        friendlyNames.map { ($0.value, $0.key) },
        uniquingKeysWith: { first, _ in first }
    )

    static func resolve(_ model: String) -> String {
        friendlyNames[model] ?? model
    }

    static func clean(_ model: String) -> String {
        // Strip trailing (ModelCode) e.g. "iPhone 16 Pro (iPhone17,1)" → "iPhone 16 Pro"
        let stripped = model.replacingOccurrences(
            of: #"\s*\([A-Za-z]+\d+,\d+\)$"#,
            with: "",
            options: .regularExpression
        ).trimmingCharacters(in: .whitespaces)
        return resolve(stripped)
    }

    static func reverseModelLookup(_ friendlyName: String) -> String {
        friendlyToRaw[friendlyName] ?? friendlyName
    }
}
