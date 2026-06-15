import SwiftUI
#if canImport(AppKit)
import AppKit
#endif

struct LibraryView: View {
    @Environment(MainViewModel.self) private var vm

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("Library")
                    .font(.system(size: 13, weight: .semibold))
                Spacer()
                Button {
                    vm.showLibrary = false
                } label: {
                    Image(systemName: "xmark")
                        .font(.system(size: 11))
                }
                .buttonStyle(.plain)
                .foregroundStyle(.secondary)
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 10)
            .background(Color.controlBg)

            Divider()

            ScrollView {
                VStack(spacing: 0) {
                    PreviousGamesSection()
                }
                .padding(.vertical, 8)
            }
            .background(Color.textBg)
        }
    }
}

// MARK: - Saved Games

private struct SavedGamesSection: View {
    @Environment(MainViewModel.self) private var vm
    @State private var showSaveAlert = false
    @State private var saveName = ""

    var body: some View {
        Group {
            HStack {
                Text("SAVED GAMES")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundStyle(.secondary)
                    .tracking(0.3)
                Spacer()
                Button {
                    saveName = defaultSaveName
                    showSaveAlert = true
                } label: {
                    Image(systemName: "plus")
                        .font(.system(size: 11))
                }
                .buttonStyle(.plain)
                .foregroundStyle(.secondary)
                .disabled(vm.selectedDevice == nil || vm.selectedApp == nil)
                .help("Save current device + app + HUD settings")
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 5)

            if vm.savedGames.isEmpty {
                LibraryEmptyLabel("No saved games yet")
            } else {
                ForEach(vm.savedGames) { game in
                    LibraryRow(
                        title: game.name,
                        subtitle: game.deviceName,
                        onTap: { vm.loadSavedGame(game) },
                        onDelete: { vm.deleteSavedGame(game) }
                    )
                }
            }
        }
        .alert("Save Current Setup", isPresented: $showSaveAlert) {
            TextField("Name", text: $saveName)
            Button("Save") {
                let trimmed = saveName.trimmingCharacters(in: .whitespaces)
                if !trimmed.isEmpty { vm.saveGame(name: trimmed) }
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("Enter a name for this device + app + HUD configuration.")
        }
    }

    private var defaultSaveName: String {
        let app = vm.selectedApp?.displayName ?? "Game"
        let device = vm.selectedDevice?.name ?? "Device"
        return "\(app) – \(device)"
    }
}

// MARK: - Previous Games

private struct PreviousGamesSection: View {
    @Environment(MainViewModel.self) private var vm

    var body: some View {
        VStack(spacing: 0) {
            HStack {
                Text("PREVIOUS GAMES")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundStyle(.secondary)
                    .tracking(0.3)
                Spacer()
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 5)

            if vm.commandHistory.isEmpty {
                LibraryEmptyLabel("No recent launches")
            } else {
                ForEach(vm.commandHistory) { entry in
                    LibraryRow(
                        title: entry.displayAppName,
                        subtitle: entry.deviceDisplay,
                        date: entry.date,
                        isSelected: vm.selectedHistoryEntry?.id == entry.id,
                        onTap: { vm.loadHistoryEntry(entry) },
                        onDelete: nil
                    )
                }
            }
        }
    }
}

// MARK: - Hidden Games

private struct HiddenGamesSection: View {
    @Environment(MainViewModel.self) private var vm

    private var hiddenList: [(internalName: String, displayName: String)] {
        vm.hiddenApps.sorted().map { name in
            (name, AppData.displayName(for: name, liveDisplayNames: vm.liveDisplayNames))
        }
    }

    var body: some View {
        VStack(spacing: 0) {
            HStack {
                Text("HIDDEN GAMES")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundStyle(.secondary)
                    .tracking(0.3)
                Spacer()
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 5)

            if hiddenList.isEmpty {
                LibraryEmptyLabel("No hidden games")
            } else {
                ForEach(hiddenList, id: \.internalName) { item in
                    HStack {
                        Text(item.displayName)
                            .font(.system(size: 12))
                            .lineLimit(1)
                        Spacer()
                        Button("Unhide") {
                            vm.unhideApp(item.internalName)
                        }
                        .font(.system(size: 11))
                        #if canImport(AppKit)
                        .buttonStyle(.link)
                        #else
                        .buttonStyle(.plain)
                        #endif
                    }
                    .padding(.horizontal, 14)
                    .padding(.vertical, 5)
                }
            }
        }
    }
}

// MARK: - Shared subviews

private struct LibraryEmptyLabel: View {
    let text: String
    init(_ text: String) { self.text = text }

    var body: some View {
        Text(text)
            .font(.system(size: 12))
            .foregroundStyle(.tertiary)
            .padding(.horizontal, 14)
            .padding(.vertical, 4)
    }
}

private struct LibraryRow: View {
    let title: String
    let subtitle: String
    var date: Date? = nil
    var isSelected: Bool = false
    let onTap: () -> Void
    let onDelete: (() -> Void)?

    var body: some View {
        HStack(spacing: 6) {
            VStack(alignment: .leading, spacing: 1) {
                Text(title)
                    .font(.system(size: 12))
                    .lineLimit(1)
                Text(subtitle)
                    .font(.system(size: 10))
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
                if let date {
                    Text(date.formatted(date: .abbreviated, time: .shortened))
                        .font(.system(size: 10))
                        .foregroundStyle(.tertiary)
                        .lineLimit(1)
                }
            }
            Spacer()
            if let onDelete {
                Button(role: .destructive) {
                    onDelete()
                } label: {
                    Image(systemName: "trash")
                        .font(.system(size: 11))
                }
                .buttonStyle(.plain)
                .foregroundStyle(.red)
            }
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 5)
        .contentShape(Rectangle())
        .background(isSelected ? Color.accentColor.opacity(0.15) : Color.clear)
        .onTapGesture { onTap() }
    }
}
