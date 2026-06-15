import Foundation
#if canImport(AppKit)
import AppKit
typealias PlatformImage = NSImage
typealias PlatformProcess = Process
#else
import UIKit
typealias PlatformImage = UIImage
final class PlatformProcess { func terminate() {} }
#endif
import SwiftUI

// MARK: - Time formatting

func formatElapsed(_ seconds: Int) -> String {
    let h = seconds / 3600
    let m = (seconds % 3600) / 60
    let s = seconds % 60
    return h > 0 ? String(format: "%d:%02d:%02d", h, m, s) : String(format: "%d:%02d", m, s)
}

// MARK: - String helpers

extension String {
    var cleanedQuotes: String {
        replacingOccurrences(of: "?", with: "'")
    }

    #if canImport(AppKit)
    func truncated(toWidth maxWidth: CGFloat, font: NSFont) -> String {
        let attrs: [NSAttributedString.Key: Any] = [.font: font]
        guard (self as NSString).size(withAttributes: attrs).width > maxWidth else { return self }
        var result = self
        while !result.isEmpty && ((result + "…") as NSString).size(withAttributes: attrs).width > maxWidth {
            result = String(result.dropLast())
        }
        return result.trimmingCharacters(in: .whitespaces) + "…"
    }
    #endif
}

// MARK: - Version comparison

extension [Int] {
    func isNewerThan(_ other: [Int]) -> Bool {
        let maxLen = Swift.max(count, other.count)
        for i in 0..<maxLen {
            let a = i < count ? self[i] : 0
            let b = i < other.count ? other[i] : 0
            if a != b { return a > b }
        }
        return false
    }
}

// MARK: - NSImage helpers

#if canImport(AppKit)
extension NSImage {
    func resized(to size: NSSize) -> NSImage {
        let result = NSImage(size: size)
        result.lockFocus()
        draw(in: NSRect(origin: .zero, size: size),
             from: NSRect(origin: .zero, size: self.size),
             operation: .copy, fraction: 1.0)
        result.unlockFocus()
        return result
    }
}

// MARK: - NSWorkspace helper

extension NSWorkspace {
    func openMail(to: String, subject: String) {
        let encoded = subject.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? subject
        if let url = URL(string: "mailto:\(to)?subject=\(encoded)") {
            open(url)
        }
    }
}
#endif

// MARK: - Color palette

extension Color {
    static let fpsAccent     = Color(red: 0/255, green: 122/255, blue: 255/255)
    static let fpsGreen      = Color(red: 52/255, green: 199/255, blue: 89/255)
    static let fpsRed        = Color(red: 255/255, green: 59/255, blue: 48/255)
    static let fpsOrange     = Color(red: 255/255, green: 149/255, blue: 0/255)
    static var fpsSurface: Color {
        #if canImport(AppKit)
        Color(NSColor.textBackgroundColor)
        #else
        Color(UIColor.systemBackground)
        #endif
    }
    static var fpsBG: Color {
        #if canImport(AppKit)
        Color(NSColor.windowBackgroundColor)
        #else
        Color(UIColor.systemGroupedBackground)
        #endif
    }
    static let fpsBorder     = Color(red: 224/255, green: 224/255, blue: 229/255)
    static let fpsSelection  = Color(red: 204/255, green: 228/255, blue: 255/255)
    static var controlBg: Color {
        #if canImport(AppKit)
        Color(NSColor.controlBackgroundColor)
        #else
        Color(UIColor.secondarySystemBackground)
        #endif
    }
    static var textBg: Color {
        #if canImport(AppKit)
        Color(NSColor.textBackgroundColor)
        #else
        Color(UIColor.systemBackground)
        #endif
    }
    static var windowBg: Color {
        #if canImport(AppKit)
        Color(NSColor.windowBackgroundColor)
        #else
        Color(UIColor.systemBackground)
        #endif
    }
    static var separator: Color {
        #if canImport(AppKit)
        Color(NSColor.separatorColor)
        #else
        Color(UIColor.separator)
        #endif
    }
    static var label: Color {
        #if canImport(AppKit)
        Color(NSColor.labelColor)
        #else
        Color(UIColor.label)
        #endif
    }
    static var secondaryLabel: Color {
        #if canImport(AppKit)
        Color(NSColor.secondaryLabelColor)
        #else
        Color(UIColor.secondaryLabel)
        #endif
    }
}

// MARK: - AppKit appearance helpers

#if canImport(AppKit)
@MainActor func setWindowAppearance(_ window: NSWindow) {
    window.titlebarAppearsTransparent = false
    window.isMovableByWindowBackground = false
}
#endif

// MARK: - Conditional modifiers

extension View {
    @ViewBuilder func colorInvert(_ condition: Bool) -> some View {
        if condition { self.colorInvert() } else { self }
    }
}

// MARK: - HUDSettings Codable helpers

extension HUDSettings {
    // Ensure custom elements are preserved across JSON round-trips
    mutating func sanitize() {
        for (key, _) in customElements {
            if !HUDSettings.customElementKeys.map(\.key).contains(key) {
                customElements.removeValue(forKey: key)
            }
        }
    }
}
