#!/bin/sh

# ci_post_xcodebuild.sh
# Xcode Cloud — Script execute apres chaque xcodebuild
# Utilise pour les rapports post-build

set -e

echo "=== VLBH Energy Kit — Post-Build Report ==="
echo "Build action: $CI_XCODEBUILD_ACTION"
echo "Build exit code: $CI_XCODEBUILD_EXIT_CODE"

if [ "$CI_XCODEBUILD_EXIT_CODE" -eq 0 ]; then
    echo "Build SUCCESS"
else
    echo "Build FAILED with exit code $CI_XCODEBUILD_EXIT_CODE"
fi

# Report test results if available
if [ "$CI_XCODEBUILD_ACTION" = "test" ]; then
    echo "Test action completed."
    if [ -d "$CI_RESULT_BUNDLE_PATH" ]; then
        echo "Result bundle: $CI_RESULT_BUNDLE_PATH"
    fi
fi

echo "=== Post-build report complete ==="
