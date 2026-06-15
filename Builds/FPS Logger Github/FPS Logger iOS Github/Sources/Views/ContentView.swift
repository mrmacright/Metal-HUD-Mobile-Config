import SwiftUI
#if canImport(AppKit)
import AppKit
#endif

struct ContentView: View {
    @Environment(MainViewModel.self) private var vm
    @Environment(\.openWindow) private var openWindow

    var body: some View {
        ZStack {
            MainView()
                .disabled(vm.xcodeRequired || vm.showPoliciesOverlay || vm.showAnalyticsOverlay)

            if vm.showPoliciesOverlay {
                PolicyOverlayView(onAccepted: {
                    vm.agreementsAccepted = true
                    vm.showPoliciesOverlay = false
                    vm.save()
                    showAnalyticsIfNeeded()
                })
                .transition(.opacity)
                .zIndex(13)
            }

            if vm.showAnalyticsOverlay {
                AnalyticsView(onDone: {
                    vm.showAnalyticsOverlay = false
                    vm.save()
                })
                .transition(.opacity)
                .zIndex(12)
            }

            #if canImport(AppKit)
            if vm.xcodeRequired {
                XcodeOverlayView(
                    title: "Xcode Required",
                    message: "Xcode \(XcodeManager.shared.requiredVersion) or later is required to connect to and launch apps on your iPhone, iPad, or Apple TV.",
                    showContinueButton: false,
                    onDismiss: { vm.xcodeRequired = false }
                )
                .disabled(vm.showAnalyticsOverlay || vm.showPoliciesOverlay)
                .transition(.opacity)
                .zIndex(11)
                .onAppear {
                    if vm.analyticsOptIn == nil {
                        DispatchQueue.main.asyncAfter(deadline: .now() + 0.4) {
                            vm.showAnalyticsOverlay = true
                        }
                    }
                }
            }
            #endif
        }
        .onReceive(NotificationCenter.default.publisher(for: .showAnalyticsPreferences)) { _ in
            vm.showAnalyticsOverlay = true
        }
        .onReceive(NotificationCenter.default.publisher(for: .showUninstallWindow)) { _ in
            openWindow(id: "uninstall-tools")
        }
    }

    private func showAnalyticsIfNeeded() {
        if vm.analyticsOptIn == nil {
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.4) {
                vm.showAnalyticsOverlay = true
            }
        }
    }
}
