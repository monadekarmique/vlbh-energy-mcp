// swift-tools-version: 5.9

import PackageDescription

let package = Package(
    name: "VLBHEnergyKit",
    platforms: [
        .iOS(.v16),
        .macOS(.v13)
    ],
    products: [
        .library(
            name: "VLBHEnergyKit",
            targets: ["VLBHEnergyKit"]
        )
    ],
    targets: [
        .target(
            name: "VLBHEnergyKit",
            path: "Sources/VLBHEnergyKit"
        ),
        .testTarget(
            name: "VLBHEnergyKitTests",
            dependencies: ["VLBHEnergyKit"],
            path: "Tests/VLBHEnergyKitTests"
        )
    ]
)
