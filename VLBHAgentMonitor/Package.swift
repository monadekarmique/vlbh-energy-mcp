// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "VLBHAgentMonitor",
    platforms: [.macOS(.v14)],
    products: [
        .executable(name: "VLBHAgentMonitor", targets: ["VLBHAgentMonitor"])
    ],
    dependencies: [
        .package(url: "https://github.com/apple/swift-collections.git", from: "1.1.0"),
        .package(url: "https://github.com/apple/swift-async-algorithms.git", from: "1.0.0"),
    ],
    targets: [
        .executableTarget(
            name: "VLBHAgentMonitor",
            dependencies: [
                .product(name: "Collections", package: "swift-collections"),
                .product(name: "AsyncAlgorithms", package: "swift-async-algorithms"),
            ],
            path: "VLBHAgentMonitor"
        )
    ]
)
