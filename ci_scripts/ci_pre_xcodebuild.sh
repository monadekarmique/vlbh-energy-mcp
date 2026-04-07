#!/bin/sh

# ci_pre_xcodebuild.sh
# Xcode Cloud — Script execute avant chaque xcodebuild
# Utilise pour la validation pre-build

set -e

echo "=== VLBH Energy Kit — Pre-Build Validation ==="
echo "Build action: $CI_XCODEBUILD_ACTION"

# Run Swift package build to catch compilation errors early
if [ "$CI_XCODEBUILD_ACTION" = "build" ] || [ "$CI_XCODEBUILD_ACTION" = "test" ]; then
    echo "Validating Swift package build..."
    swift build 2>&1 || {
        echo "ERROR: Swift package build failed"
        exit 1
    }
    echo "Swift package build OK"
fi

echo "=== Pre-build validation complete ==="
