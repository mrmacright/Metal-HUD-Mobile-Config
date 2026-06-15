import Foundation

struct HUDSettings: Codable, Equatable {
    var preset: HUDPreset = .default
    var alignment: HUDAlignment = .topRight
    var scale: HUDScale = .default
    var advancedOpen: Bool = false
    var customElements: [String: Bool] = [:]
    var performanceLogging: Bool = false
    var shaderLogging: Bool = false
    var showMetricsRange: Bool = false
    var insightsEnabled: Bool = false
    var savedCustomPresets: [CustomPreset] = []
    var selectedSavedPresetID: UUID? = nil

    static let maxSavedCustomPresets = 5

    // MARK: - Decoder
    // Uses decodeIfPresent for every field so that new settings added in future
    // versions don't break existing saved state — missing keys fall back to defaults.

    init() {}

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        preset                = (try? c.decodeIfPresent(HUDPreset.self,      forKey: .preset))                ?? .default
        alignment             = (try? c.decodeIfPresent(HUDAlignment.self,   forKey: .alignment))             ?? .topRight
        scale                 = (try? c.decodeIfPresent(HUDScale.self,       forKey: .scale))                 ?? .default
        advancedOpen          = (try? c.decodeIfPresent(Bool.self,           forKey: .advancedOpen))          ?? false
        customElements        = (try? c.decodeIfPresent([String: Bool].self, forKey: .customElements))        ?? [:]
        performanceLogging    = (try? c.decodeIfPresent(Bool.self,           forKey: .performanceLogging))    ?? false
        shaderLogging         = (try? c.decodeIfPresent(Bool.self,           forKey: .shaderLogging))         ?? false
        showMetricsRange      = (try? c.decodeIfPresent(Bool.self,           forKey: .showMetricsRange))      ?? false
        insightsEnabled       = (try? c.decodeIfPresent(Bool.self,           forKey: .insightsEnabled))       ?? false
        savedCustomPresets    = (try? c.decodeIfPresent([CustomPreset].self, forKey: .savedCustomPresets))    ?? []
        selectedSavedPresetID = try? c.decodeIfPresent(UUID.self,            forKey: .selectedSavedPresetID)
    }

    // MARK: - Custom preset

    struct CustomPreset: Codable, Equatable, Identifiable {
        var id: UUID = UUID()
        var name: String
        var elements: [String: Bool]
    }

    // MARK: - Preset

    enum HUDPreset: String, CaseIterable, Codable, Identifiable {
        var id: String { rawValue }
        case `default`       = "Default"
        case simple          = "Simple"
        case fpsOnly         = "FPS Only"
        case thermals        = "Thermals"
        case compiledShaders = "Compiled Shaders"
        case rich            = "Rich"
        case full            = "Full"
        case custom          = "Custom"

        var displayElements: String {
            switch self {
            case .default:
                return "device,layersize,fps,frameinterval,gputime,frameintervalgraph"
            case .custom:
                return ""
            default:
                return elements ?? ""
            }
        }

        // MTL_HUD_ELEMENTS value — nil means omit the key (full default HUD)
        var elements: String? {
            switch self {
            case .default:
                return nil
            case .simple:
                return "device,layersize,fps"
            case .fpsOnly:
                return "fps"
            case .thermals:
                return "device,layersize,memory,fps,frameinterval,gputime,thermal,frameintervalgraph,metalfx"
            case .compiledShaders:
                return "device,layersize,memory,thermal,fps,gputime,frameinterval,frameintervalgraph,shaders,metalfx"
            case .rich:
                return "device,layersize,layerscale,gamemode,memory,refreshrate,fps,frameinterval,gputime,thermal,frameintervalgraph,presentdelay,metalcpu,shaders,metalfx"
            case .full:
                return "device,layersize,layerscale,memory,refreshrate,thermal,gamemode,fps,fpsgraph,framenumber,gputime,frameinterval,frameintervalgraph,frameintervalhistogram,presentdelay,metalcpu,gputimeline,shaders,metalfx"
            case .custom:
                return nil
            }
        }
    }

    // MARK: - Scale

    enum HUDScale: String, CaseIterable, Codable, Identifiable {
        var id: String { rawValue }
        case small   = "Small"
        case `default` = "Default"
        case large   = "Large"
        case larger  = "Larger"
        case max     = "Max"

        var envValue: String {
            switch self {
            case .small:   return "0.15"
            case .default: return "0.2"
            case .large:   return "0.3"
            case .larger:  return "0.4"
            case .max:     return "1.0"
            }
        }
    }

    // MARK: - Alignment

    enum HUDAlignment: String, CaseIterable, Codable, Identifiable {
        var id: String { rawValue }
        case topLeft      = "Top Left"
        case topCenter    = "Top Center"
        case topRight     = "Top Right"
        case centerLeft   = "Center Left"
        case centered     = "Centered"
        case centerRight  = "Center Right"
        case bottomLeft   = "Bottom Left"
        case bottomCenter = "Bottom Center"
        case bottomRight  = "Bottom Right"

        var envValue: String {
            switch self {
            case .topLeft:      return "topleft"
            case .topCenter:    return "topcenter"
            case .topRight:     return "topright"
            case .centerLeft:   return "centerleft"
            case .centered:     return "centered"
            case .centerRight:  return "centerright"
            case .bottomLeft:   return "bottomleft"
            case .bottomCenter: return "bottomcenter"
            case .bottomRight:  return "bottomright"
            }
        }
    }

    // MARK: - Custom element keys 

    static let customElementKeys: [(key: String, label: String)] = [
        ("device",                    "Metal Device"),
        ("layersize",                 "Layer Size & Present Mode"),
        ("layerscale",                "Layer Scale & Pixel Format"),
        ("memory",                    "Memory"),
        ("refreshrate",               "Refresh Rate"),
        ("thermal",                   "Thermal State"),
        ("gamemode",                  "Game Mode"),
        ("fps",                       "FPS"),
        ("fpsgraph",                  "FPS Graph"),
        ("framenumber",               "Frame Number"),
        ("gputime",                   "GPU Time"),
        ("frameinterval",             "Frame Interval"),
        ("frameintervalgraph",        "Frame Interval Graph"),
        ("frameintervalhistogram",    "Frame Interval Histogram"),
        ("presentdelay",              "Present Delay"),
        ("metalcpu",                  "Command Buffer & Encoder Count"),
        ("gputimeline",               "Encoder Time & GPU Timeline"),
        ("toplabeledcommandbuffers",  "Top Labeled Command Buffers"),
        ("toplabeledencoders",        "Top Labeled Encoders"),
        ("shaders",                   "Shader Compiler"),
        ("metalfx",                   "MetalFX"),
        ("disk",                      "Disk"),
    ]


    // MARK: - Environment variable builder

    func buildEnvironmentVariables() -> [String: String] {
        var env: [String: String] = ["MTL_HUD_ENABLED": "1"]

        if preset == .custom {
            let selected = HUDSettings.customElementKeys
                .filter { customElements[$0.key] == true }
                .map { $0.key }
            if !selected.isEmpty {
                env["MTL_HUD_ELEMENTS"] = selected.joined(separator: ",")
            }
        } else if let elements = preset.elements {
            env["MTL_HUD_ELEMENTS"] = elements
        }

        env["MTL_HUD_ALIGNMENT"] = alignment.envValue

        if scale != .default {
            env["MTL_HUD_SCALE"] = scale.envValue
        }

        if performanceLogging {
            env["MTL_HUD_LOG_ENABLED"] = "1"
            if shaderLogging {
                env["MTL_HUD_LOG_SHADER_ENABLED"] = "1"
            }
        }
        let needsEncoderTiming = customElements["toplabeledcommandbuffers"] == true
                              || customElements["toplabeledencoders"] == true
        if needsEncoderTiming {
            env["MTL_HUD_ENCODER_TIMING_ENABLED"] = "1"
        }
        if showMetricsRange {
            env["MTL_HUD_SHOW_VALUE_RANGE"] = "1"
        }
        if insightsEnabled {
            env["MTL_HUD_INSIGHTS_ENABLED"] = "1"
        }

        return env
    }

    mutating func applyPreset(_ newPreset: HUDPreset) {
        guard newPreset != .custom else { return }
        let elemStr = newPreset.displayElements
        if elemStr.isEmpty {
            customElements = [:]
        } else {
            let keys = Set(elemStr.components(separatedBy: ","))
            customElements = Dictionary(uniqueKeysWithValues:
                HUDSettings.customElementKeys.map { ($0.key, keys.contains($0.key)) }
            )
        }
        preset = newPreset
        selectedSavedPresetID = nil
    }

    mutating func reset() {
        preset = .default
        alignment = .topRight
        scale = .default
        customElements = [:]
        performanceLogging = false
        shaderLogging = false
        showMetricsRange = false
        insightsEnabled = false
        selectedSavedPresetID = nil
    }
}

// MARK: - Saved Game

struct SavedGame: Codable, Identifiable {
    var id: UUID = UUID()
    var name: String
    var deviceUDID: String
    var deviceName: String
    var appPath: String
    var appDisplayName: String
    var hudSettings: HUDSettings
}

// MARK: - Command history

struct CommandHistoryEntry: Codable, Identifiable {
    var id: UUID = UUID()
    let command: String
    let udid: String
    let deviceDisplay: String
    let appPath: String
    let hud: HUDSettings
    var date: Date = Date()

    var appName: String {
        let base = URL(fileURLWithPath: appPath).lastPathComponent
        return base.hasSuffix(".app") ? String(base.dropLast(4)) : base
    }

    var displayAppName: String {
        AppData.displayName(for: appName)
    }
}
