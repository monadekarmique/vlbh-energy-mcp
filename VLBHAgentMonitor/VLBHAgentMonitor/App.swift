import SwiftUI

@main
struct VLBHAgentMonitorApp: App {
    @StateObject private var agentCoordinator = AgentCoordinator()
    @StateObject private var processMonitor = ProcessMonitor()
    @StateObject private var leakDetector = LeakDetector()

    var body: some Scene {
        WindowGroup {
            DashboardView()
                .environmentObject(agentCoordinator)
                .environmentObject(processMonitor)
                .environmentObject(leakDetector)
                .frame(minWidth: 1200, minHeight: 800)
        }
        .windowStyle(.titleBar)
        .defaultSize(width: 1400, height: 900)

        MenuBarExtra("VLBH Monitor", systemImage: "waveform.path.ecg") {
            MenuBarView()
                .environmentObject(agentCoordinator)
                .environmentObject(processMonitor)
        }
        .menuBarExtraStyle(.window)

        Settings {
            SettingsView()
                .environmentObject(agentCoordinator)
        }
    }
}
