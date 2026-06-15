import SwiftUI
#if canImport(AppKit)
import AppKit
#endif

private struct HelpSectionItem: Identifiable {
    let id: String
    let title: String
}

private let helpSections: [HelpSectionItem] = [
    HelpSectionItem(id: "launch",     title: "How to launch a game"),
    HelpSectionItem(id: "platforms",  title: "Supported platforms"),
    HelpSectionItem(id: "notconnect", title: "Device not connecting?"),
    HelpSectionItem(id: "appletv",    title: "How to connect to Apple TV"),
    HelpSectionItem(id: "custom",     title: "Custom HUD metrics"),
    HelpSectionItem(id: "states",     title: "Connection states"),
    HelpSectionItem(id: "gamemode",   title: "Why isn't Game Mode turning on?"),
    HelpSectionItem(id: "safe",       title: "Is it safe to use with online games?"),
    HelpSectionItem(id: "hudmissing", title: "Why isn't Metal HUD showing?"),
    HelpSectionItem(id: "rename",     title: "Why is a game called something different?"),
]

struct ConnectionHelpView: View {
    var initialSection: String? = nil
    @Environment(\.dismiss) private var dismiss
    @State private var activeSection: String = helpSections[0].id
    @State private var scrollProxy: ScrollViewProxy?

    var body: some View {
        VStack(spacing: 0) {
            // Toolbar
            HStack {
                Text("Connection Help")
                    .font(.system(size: 16, weight: .semibold))
                Spacer()
                Button("Done") { dismiss() }
                    .keyboardShortcut(.escape)
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 14)
            .background(Color.controlBg)

            Divider()

            HStack(spacing: 0) {
                // Sidebar
                VStack(spacing: 0) {
                    ScrollView {
                        VStack(alignment: .leading, spacing: 2) {
                            ForEach(helpSections) { section in
                                Button {
                                    activeSection = section.id
                                    withAnimation {
                                        scrollProxy?.scrollTo(section.id, anchor: .top)
                                    }
                                } label: {
                                    Text(section.title)
                                        .font(.system(size: 13))
                                        .frame(maxWidth: .infinity, alignment: .leading)
                                        .padding(.vertical, 6)
                                        .padding(.horizontal, 12)
                                        .background(
                                            activeSection == section.id
                                                ? Color.accentColor.opacity(0.15)
                                                : Color.clear
                                        )
                                        .foregroundStyle(
                                            activeSection == section.id
                                                ? Color.accentColor
                                                : Color.primary
                                        )
                                        .cornerRadius(6)
                                }
                                .buttonStyle(.plain)
                            }
                        }
                        .padding(8)
                    }
                }
                .frame(width: 220)
                .background(Color.controlBg)

                Divider()

                // Content
                ScrollViewReader { proxy in
                    ScrollView {
                        VStack(alignment: .leading, spacing: 0) {
                            LaunchSection()
                            HelpDivider()
                            PlatformsSection()
                            HelpDivider()
                            NotConnectingSection()
                            HelpDivider()
                            AppleTVSection()
                            HelpDivider()
                            CustomMetricsHelpSection()
                            HelpDivider()
                            ConnectionStatesSection()
                            HelpDivider()
                            GameModeSection()
                            HelpDivider()
                            SafetySection()
                            HelpDivider()
                            HUDMissingSection()
                            HelpDivider()
                            RenameSection()
                        }
                        .padding(28)
                    }
                    .onAppear {
                        scrollProxy = proxy
                        if let section = initialSection {
                            activeSection = section
                        }
                    }
                    .task(id: initialSection) {
                        guard let section = initialSection else { return }
                        // Wait for sheet to finish presenting before scrolling.
                        try? await Task.sleep(nanoseconds: 500_000_000)
                        withAnimation { proxy.scrollTo(section, anchor: .top) }
                    }
                }
            }
        }
        .frame(width: 1100, height: 680)
    }
}

// MARK: - Section views

private struct LaunchSection: View {
    var body: some View {
        HelpSection(id: "launch", title: "How to launch a game with Metal HUD") {
            SideBySide(imageFile: "iPhone 17 Pro Max_Metal HUD ON", subdirectory: "assets/Connection Help", imageLeading: true) {
                HelpText("Apps are only detectable when already open and in the foreground.")
                HelpStep(number: 1, text: "Launch the game on your device")
                HelpStep(number: 2, text: "Keep it open in the foreground")
                HelpStep(number: 3, text: "Click Show Running Games")
                HelpStep(number: 4, text: "Choose your game → Launch App with Metal HUD")
            }
        }
    }
}

private struct PlatformsSection: View {
    var body: some View {
        HelpSection(id: "platforms", title: "Supported platforms for Metal HUD") {
            HelpBullet("iOS 17 or later")
            HelpBullet("iPadOS 17 or later")
            HelpBullet("Apple TV 4K (1st gen, 2017) or later")
            HelpNote("System-wide HUD support is not possible")
        }
    }
}

private struct NotConnectingSection: View {
    var body: some View {
        HelpSection(id: "notconnect", title: "Device not connecting?") {
            SideBySide(imageFile: "Trust This Computer", subdirectory: "assets/Connection Help", imageLeading: false) {
                HelpStep(number: 1, text: "Connect your iPhone or iPad via USB")
                HelpStep(number: 2, text: "Unlock the device")
                HelpStep(number: 3, text: "Tap Trust This Computer if prompted")
                HelpStep(number: 4, text: "On Mac, click Allow if asked to connect the accessory")
                HelpText("If the trust prompt was dismissed:")
                HelpBullet("Settings → General → Transfer or Reset iPhone → Reset → Reset Location & Privacy")
            }
        }
    }
}

private struct AppleTVSection: View {
    var body: some View {
        HelpSection(id: "appletv", title: "How to connect to Apple TV") {
            HelpStep(number: 1, text: "On Apple TV go to Settings > Remotes and Devices > Remote App and Devices")
            HelpStep(number: 2, text: "Open Xcode → Window → Devices and Simulators → Discovered")
            HelpStep(number: 3, text: "Pair Apple TV → enter verification code → Connect")
            HelpStep(number: 4, text: "Open FPS Logger → List Devices")
            HelpNote("You might need to re-pair after tvOS/macOS updates")
            HelpNote("Apple TV HD is not supported")
        }
    }
}

private struct CustomMetricsHelpSection: View {
    var body: some View {
        HelpSection(id: "custom", title: "Custom HUD metrics not working?") {
            SideBySide(imageFile: "Metal HUD_iOS 26", subdirectory: "assets/Connection Help", imageLeading: true) {
                HelpText("Custom metrics, position, and scale require iOS 26, iPadOS 26, or tvOS 26 or later.")
                HelpText("iOS 17–18 only support the Default preset.")
            }
        }
    }
}

private struct ConnectionStatesSection: View {
    var body: some View {
        HelpSection(id: "states", title: "Connection states") {
            VStack(alignment: .leading, spacing: 14) {
                StateRow(state: "available (paired + wireless)",
                         description: "Paired and reachable over Wi-Fi — no USB cable needed.")

                StateRow(state: "Connected",
                         description: "Device is connected via USB and ready. Wireless support may still be preparing.")

                StateRow(state: "connecting",
                         description: "Device is connected via USB and ready. Wireless support may still be preparing.")

                VStack(alignment: .leading, spacing: 6) {
                    StateRow(state: "Available (preparing)",
                             description: "Device is visible but still preparing. Pairing may be required. Metal HUD may still work.")
                    VStack(alignment: .leading, spacing: 2) {
                        Text("If device isn't ready:")
                            .font(.system(size: 12))
                            .foregroundStyle(.secondary)
                            .padding(.leading, 32)
                        HelpBullet("Disconnect and reconnect the USB cable")
                            .padding(.leading, 32)
                        HelpBullet("Unlock the device and tap Trust if prompted")
                            .padding(.leading, 32)
                    }
                }

                StateRow(state: "available (pairing required)",
                         description: "Device is visible but may need pairing or trust confirmation. Connect via USB and tap Trust if prompted.")

                StateRow(state: "connected (limited support)",
                         description: "This device may have trouble enabling Metal HUD. If you can't connect, try updating your device or Xcode, or download Xcode beta from the App Store or developer.apple.com. You can still try Show Running Games.")

                StateRow(state: "unavailable (device offline)",
                         description: "Device is offline, turned off, or not reachable on the same Wi-Fi network.")

                StateRow(state: "Unsupported",
                         description: "This device does not support Metal HUD.")
            }
        }
    }
}

private struct GameModeSection: View {
    var body: some View {
        HelpSection(id: "gamemode", title: "Why isn't Game Mode turning on?") {
            SideBySide(imageFile: "Game Mode", subdirectory: "assets/Connection Help", imageLeading: false) {
                HelpText("Game Mode turns on automatically for supported games.")
                HelpText("If it isn't turning on, the game likely doesn't support Game Mode yet. This can only be enabled by the game developer — external tools cannot force it on.")
            }
        }
    }
}

private struct SafetySection: View {
    var body: some View {
        HelpSection(id: "safe", title: "Is it safe to use with online games?") {
            SideBySide(imageFile: "PUBG Mobile with Metal HUD", subdirectory: "assets/Connection Help", imageLeading: true) {
                HelpText("Metal Performance HUD has been widely used in games like PUBG MOBILE, COD: Mobile, and Genshin Impact.")
                HelpText("However, some anti-cheat systems may detect it and block the game from launching.")
                HelpText("Use at your own risk, especially in competitive online games.")
            }
        }
    }
}

private struct HUDMissingSection: View {
    var body: some View {
        HelpSection(id: "hudmissing", title: "Why isn't Metal HUD showing?") {
            HelpText("If the game launches but the Metal HUD does not appear, the game is likely not using Metal graphics (for example, it may use OpenGL instead).")
            HelpText("Metal HUD only works with games powered by Metal.")
        }
    }
}

private struct RenameSection: View {
    var body: some View {
        HelpSection(id: "rename", title: "Why is a game called something different than its actual name?") {
            HelpText("This app detects the game's internal app name from the App Store package. Some developers do not use the official game title internally, so certain games may appear with generic names like \"Game\".")
        }
    }
}

// MARK: - Reusable subviews

struct HelpSection<Content: View>: View {
    let id: String
    let title: String
    @ViewBuilder let content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(title)
                .font(.system(size: 15, weight: .semibold))
            content
        }
        .id(id)
    }
}

private struct HelpDivider: View {
    var body: some View {
        Divider()
            .padding(.vertical, 24)
    }
}

// Image on one side, content on the other
private struct SideBySide<Content: View>: View {
    let imageFile: String
    let subdirectory: String
    let imageLeading: Bool
    @ViewBuilder let content: Content

    var body: some View {
        #if canImport(AppKit)
        if let img = loadImage() {
            HStack(alignment: .top, spacing: 24) {
                if imageLeading {
                    Image(nsImage: img)
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                        .frame(maxWidth: 340)
                        .cornerRadius(8)
                    VStack(alignment: .leading, spacing: 10) { content }
                } else {
                    VStack(alignment: .leading, spacing: 10) { content }
                    Image(nsImage: img)
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                        .frame(maxWidth: 340)
                        .cornerRadius(8)
                }
            }
        } else {
            VStack(alignment: .leading, spacing: 10) { content }
        }
        #else
        VStack(alignment: .leading, spacing: 10) { content }
        #endif
    }

    #if canImport(AppKit)
    private func loadImage() -> NSImage? {
        guard let url = Bundle.main.url(forResource: imageFile, withExtension: "png",
                                        subdirectory: subdirectory) else { return nil }
        return NSImage(contentsOf: url)
    }
    #endif
}

struct HelpText: View {
    let text: String
    init(_ text: String) { self.text = text }

    var body: some View {
        Text(text)
            .font(.system(size: 13))
            .foregroundStyle(.primary)
            .fixedSize(horizontal: false, vertical: true)
    }
}

struct HelpBullet: View {
    let text: String
    init(_ text: String) { self.text = text }

    var body: some View {
        HStack(alignment: .firstTextBaseline, spacing: 6) {
            Text("•").font(.system(size: 13))
            Text(text)
                .font(.system(size: 13))
                .fixedSize(horizontal: false, vertical: true)
        }
    }
}

struct HelpStep: View {
    let number: Int
    let text: String

    var body: some View {
        HStack(alignment: .firstTextBaseline, spacing: 8) {
            Text("\(number).")
                .font(.system(size: 13, weight: .medium))
                .foregroundStyle(.secondary)
                .frame(width: 18, alignment: .trailing)
            Text(text)
                .font(.system(size: 13))
                .fixedSize(horizontal: false, vertical: true)
        }
    }
}

private struct HelpNote: View {
    let text: String
    init(_ text: String) { self.text = text }

    var body: some View {
        HStack(alignment: .firstTextBaseline, spacing: 6) {
            Text("Note:")
                .font(.system(size: 13, weight: .medium))
                .foregroundStyle(.secondary)
            Text(text)
                .font(.system(size: 13))
                .foregroundStyle(.secondary)
                .fixedSize(horizontal: false, vertical: true)
        }
    }
}

private struct StateRow: View {
    let state: String
    let description: String

    var body: some View {
        HStack(alignment: .top, spacing: 10) {
            ConnectionIconView(state: state)
                .frame(width: 22, height: 16)
                .padding(.top, 2)
            VStack(alignment: .leading, spacing: 2) {
                Text(state)
                    .font(.system(size: 13, weight: .medium))
                Text(description)
                    .font(.system(size: 12))
                    .foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }
}
