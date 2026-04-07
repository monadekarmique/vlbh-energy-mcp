#!/bin/sh

# ci_post_clone.sh
# Xcode Cloud — Script execute apres le clonage du repo
# Documentation: https://developer.apple.com/documentation/xcode/writing-custom-build-scripts

set -e

echo "=== VLBH Energy Kit — Xcode Cloud Post-Clone ==="
echo "Build number: $CI_BUILD_NUMBER"
echo "Branch: $CI_BRANCH"
echo "Commit: $CI_COMMIT"
echo "Workflow: $CI_WORKFLOW"

# Resolve SPM dependencies
echo "Resolving Swift Package Manager dependencies..."
swift package resolve

echo "=== Post-clone complete ==="
