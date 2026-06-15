import Foundation

@MainActor
final class AnalyticsService {
    static let shared = AnalyticsService()

    private let analyticsURL = URL(string: "https://script.google.com/macros/s/AKfycbzlfap_uHHIys-_tRiQSTIw1ZGqgjt-pDNlYDVjIA5_hkw6nujAkWmTeWofAri6B6IJ/exec")!
    private let token = "mhmc-2025-a7f3k9"

    var isOptedIn: Bool = false
    var appVersion: String = ""
    var getDisplayState: (String) -> String = { $0 }

    private init() {}

    func sendLaunchEvent(
        deviceModel: String,
        appName: String,
        connectionState: String,
        iconURL: String = "",
        rawAppName: String = "",
        metricPreset: String = ""
    ) {
        guard isOptedIn else { return }

        let deviceModelReal = DeviceModels.reverseModelLookup(deviceModel)
        let connectionReal = getDisplayState(connectionState)

        let payload: [String: Any] = [
            "token": token,
            "type": "launch",
            "app_version": appVersion,
            "device_model": deviceModel,
            "device_model_real": deviceModelReal,
            "connection_state": connectionState,
            "connection_real": connectionReal,
            "app_name": appName,
            "raw_app_name": rawAppName,
            "app_icon_url": iconURL,
            "metric_preset": metricPreset,
        ]
        sendPayload(payload)
    }

    func sendAppReport(
        internalName: String,
        displayName: String,
        iconURL: String,
        reportType: String,
        suggestedName: String = ""
    ) {
        var payload: [String: Any] = [
            "token": token,
            "type": "icon_report",
            "app_version": appVersion,
            "report_type": reportType,
            "raw_app_name": internalName,
            "app_name": displayName,
            "app_icon_url": iconURL,
        ]
        if !suggestedName.isEmpty {
            payload["suggested_name"] = suggestedName
        }
        sendPayload(payload)
    }

    private func sendPayload(_ payload: [String: Any]) {
        guard let data = try? JSONSerialization.data(withJSONObject: payload) else { return }
        let url = analyticsURL
        Task.detached(priority: .background) {
            do {
                var request = URLRequest(url: url)
                request.httpMethod = "POST"
                request.setValue("application/json", forHTTPHeaderField: "Content-Type")
                request.httpBody = data
                let (_, _) = try await URLSession.shared.data(for: request)
            } catch {
                print("[Analytics] Send failed: \(error)")
            }
        }
    }
}
