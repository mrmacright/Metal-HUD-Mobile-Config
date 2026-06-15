import SwiftUI
#if canImport(AppKit)
import AppKit
#endif

@main
struct FPSLoggerApp: App {
    #if canImport(AppKit)
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    #endif
    @State private var viewModel = MainViewModel()

    var body: some Scene {
        #if canImport(AppKit)
        WindowGroup(id: "main") {
            rootView
        }
        .windowStyle(.titleBar)
        .windowToolbarStyle(.unified)
        .commands {
            // Remove default menus — keep only FPS Logger (app menu) | Settings | Help
            SuppressedDefaultCommands()

            CommandGroup(after: .windowArrangement) {
                OpenMainWindowButton()
            }

            // MARK: Settings menu
            CommandMenu("Settings") {
                Menu("Metric Presets") {
                    ForEach(HUDSettings.HUDPreset.allCases) { preset in
                        Button {
                            viewModel.hudSettings.applyPreset(preset)
                            viewModel.save()
                        } label: {
                            let isActive = viewModel.hudSettings.preset == preset
                                && !(preset == .custom && viewModel.hudSettings.selectedSavedPresetID != nil)
                            Label(preset.rawValue, systemImage: isActive ? "checkmark" : "")
                        }
                    }

                    if !viewModel.hudSettings.savedCustomPresets.isEmpty {
                        Divider()
                        ForEach(viewModel.hudSettings.savedCustomPresets) { saved in
                            Button {
                                viewModel.hudSettings.preset = .custom
                                viewModel.hudSettings.customElements = saved.elements
                                viewModel.hudSettings.selectedSavedPresetID = saved.id
                                viewModel.save()
                            } label: {
                                Label(saved.name,
                                      systemImage: viewModel.hudSettings.selectedSavedPresetID == saved.id ? "checkmark" : "")
                            }
                        }
                    }
                }

                Menu("Position") {
                    ForEach(HUDSettings.HUDAlignment.allCases) { alignment in
                        Button {
                            viewModel.hudSettings.alignment = alignment
                            viewModel.save()
                        } label: {
                            Label(alignment.rawValue,
                                  systemImage: viewModel.hudSettings.alignment == alignment ? "checkmark" : "")
                        }
                    }
                }

                Menu("Scale") {
                    ForEach(HUDSettings.HUDScale.allCases) { scale in
                        Button {
                            viewModel.hudSettings.scale = scale
                            viewModel.save()
                        } label: {
                            Label(scale.rawValue,
                                  systemImage: viewModel.hudSettings.scale == scale ? "checkmark" : "")
                        }
                    }
                }

                Divider()

                Button("Custom Metrics…") {
                    NotificationCenter.default.post(name: .showCustomMetrics, object: nil)
                }

                Button("Reset Metrics") {
                    viewModel.hudSettings.reset()
                    viewModel.save()
                }

                Divider()

                Button("Performance Logging") {
                    NotificationCenter.default.post(name: .showAppStorePerfInfo, object: nil)
                }

                Divider()

                Button("Uninstall Xcode & Command Line Tools…") {
                    NotificationCenter.default.post(name: .showUninstallWindow, object: nil)
                }

                Divider()

                Button("Export Logs…") { viewModel.exportLogs() }
                    .disabled(viewModel.logBuffer.isEmpty)
            }

            CommandMenu("App Store") {
                Button("Download App Store Version") {
                    NSWorkspace.shared.open(URL(string: "https://apps.apple.com/app/id6763967836")!)
                }
            }

            // MARK: Help menu — replaces the system Help slot (no duplicate)
            CommandGroup(replacing: .help) {
                Button("Connection Help") {
                    NotificationCenter.default.post(name: .showConnectionHelp, object: nil)
                }
                Button("Contact Support") {
                    NotificationCenter.default.post(name: .showContactSupport, object: nil)
                }
                Divider()
                Button("Analytics Preferences…") {
                    NotificationCenter.default.post(name: .showAnalyticsPreferences, object: nil)
                }
                Button("License") {
                    NSWorkspace.shared.open(URL(string: "https://www.fpslogger.com/license")!)
                }
                Button("Privacy Policy") {
                    NSWorkspace.shared.open(URL(string: "https://www.fpslogger.com/privacy")!)
                }
            }
        }
        #else
        WindowGroup {
            rootView
        }
        #endif

        #if canImport(AppKit)
        WindowGroup("Uninstall Developer Tools", id: "uninstall-tools") {
            UninstallView()
                .environment(viewModel)
        }
        .windowResizability(.contentSize)
        #endif
    }

    @ViewBuilder
    private var rootView: some View {
        #if canImport(AppKit)
        ContentView()
            .environment(viewModel)
            .frame(minWidth: 960, minHeight: 580)
            .onAppear {
                performOnAppear()
                UserDefaults.standard.set(true, forKey: "mainWindowOpen")
            }
            .onDisappear {
                UserDefaults.standard.set(false, forKey: "mainWindowOpen")
            }
        #else
        ContentView()
            .environment(viewModel)
            .onAppear { performOnAppear() }
        #endif
    }

    private func performOnAppear() {
        viewModel.restoreDevicePreview()
        if !viewModel.agreementsAccepted {
            viewModel.showPoliciesOverlay = true
        } else if viewModel.analyticsOptIn == nil {
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.4) {
                viewModel.showAnalyticsOverlay = true
            }
        }
        viewModel.checkForUpdates()
    }
}

private struct OpenMainWindowButton: View {
    @Environment(\.openWindow) private var openWindow
    @AppStorage("mainWindowOpen") private var isOpen = true
    var body: some View {
        if !isOpen {
            Button("Re-open FPS Logger") {
                openWindow(id: "main")
            }
        }
    }
}

private struct SuppressedDefaultCommands: Commands {
    var body: some Commands {
        CommandGroup(replacing: .appInfo) {}
        CommandGroup(replacing: .newItem) {}
        CommandGroup(replacing: .saveItem) {}
        CommandGroup(replacing: .undoRedo) {}
        CommandGroup(replacing: .pasteboard) {}
        CommandGroup(replacing: .sidebar) {}
        CommandGroup(replacing: .toolbar) {}
    }
}

// MARK: - App Delegate

#if canImport(AppKit)
class AppDelegate: NSObject, NSApplicationDelegate {
    // SwiftUI re-renders commands on every state change, which restores View/Window.
    // applicationWillUpdate fires before every event cycle, keeping them removed.
    func applicationDidFinishLaunching(_ notification: Notification) {
        NSWindow.allowsAutomaticWindowTabbing = false
    }

    func applicationWillUpdate(_ notification: Notification) {
        for title in ["View"] {
            if let item = NSApplication.shared.mainMenu?.item(withTitle: title) {
                NSApplication.shared.mainMenu?.removeItem(item)
            }
        }
        // Hide unwanted items from the Window menu
        if let windowMenu = NSApplication.shared.mainMenu?.item(withTitle: "Window")?.submenu {
            for item in windowMenu.items {
                if item.action == #selector(NSWindow.performZoom(_:))
                    || item.title == "Remove Window from Set" {
                    item.isHidden = true
                }
            }
        }
    }
}
#endif

extension Notification.Name {
    static let showConnectionHelp       = Notification.Name("showConnectionHelp")
    static let showConnectionStateInfo  = Notification.Name("showConnectionStateInfo")
    static let showAnalyticsPreferences = Notification.Name("showAnalyticsPreferences")
    static let showCustomMetrics        = Notification.Name("showCustomMetrics")
    static let showUninstallWindow      = Notification.Name("showUninstallWindow")
    static let showAppStorePerfInfo     = Notification.Name("showAppStorePerfInfo")
    static let showContactSupport       = Notification.Name("showContactSupport")
}
