#!/usr/bin/env bash
#
# Deploy backend to IBM Cloud Functions.
#
# Prerequisites:
#   - IBM Cloud CLI installed (ibmcloud)
#   - Logged in: ibmcloud login
#   - Cloud Functions plugin: ibmcloud plugin install cloud-functions
#   - Target set: ibmcloud target -r <region> -g <resource-group>
#
# Usage:
#   ./deploy.sh                    # Deploy all functions
#   ./deploy.sh process_new_photo  # Deploy a single function
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_NAME="familyframe"

# Load settings from local.settings.json if it exists
SETTINGS_FILE="$SCRIPT_DIR/local.settings.json"
PARAMS=""
if [ -f "$SETTINGS_FILE" ]; then
    echo "Loading parameters from local.settings.json..."
    # Convert JSON key-value pairs to -p key value flags
    PARAMS=$(python3 -c "
import json
with open('$SETTINGS_FILE') as f:
    settings = json.load(f)
for k, v in settings.items():
    print(f'-p {k} {v}')
" | tr '\n' ' ')
fi

# Create or update the package with default parameters
echo "Creating/updating package '$PACKAGE_NAME'..."
ibmcloud fn package update "$PACKAGE_NAME" $PARAMS

deploy_function() {
    local func_name=$1
    local func_dir="$SCRIPT_DIR/packages/$func_name"

    if [ ! -d "$func_dir" ]; then
        echo "ERROR: Function directory not found: $func_dir"
        return 1
    fi

    echo ""
    echo "=== Deploying $func_name ==="

    # Create a temporary zip with the function code and shared modules
    local tmpdir
    tmpdir=$(mktemp -d)
    local zipfile="$tmpdir/${func_name}.zip"

    # Copy function code
    cp "$func_dir/__main__.py" "$tmpdir/__main__.py"

    # Copy shared modules
    cp -r "$SCRIPT_DIR/shared" "$tmpdir/shared"

    # Install dependencies into the package
    pip3 install -q -r "$SCRIPT_DIR/requirements.txt" -t "$tmpdir" 2>/dev/null || true

    # Create zip
    (cd "$tmpdir" && zip -r "$zipfile" . -x "*.pyc" "__pycache__/*" > /dev/null)

    # Determine if this is a web action
    local web_flag="--web true"

    # Deploy
    ibmcloud fn action update "$PACKAGE_NAME/$func_name" \
        "$zipfile" \
        --kind python:3.11 \
        $web_flag \
        --timeout 60000 \
        --memory 256

    # Clean up
    rm -rf "$tmpdir"

    echo "Deployed: $func_name"
}

# Deploy functions
FUNCTIONS=("process_new_photo" "display_sync_api" "refresh_subscription" "admin_api" "whatsapp_webhook")

if [ $# -gt 0 ]; then
    # Deploy only specified function(s)
    for func in "$@"; do
        deploy_function "$func"
    done
else
    # Deploy all functions
    for func in "${FUNCTIONS[@]}"; do
        if [ -d "$SCRIPT_DIR/packages/$func" ]; then
            deploy_function "$func"
        fi
    done
fi

echo ""
echo "=== Setting up cron trigger for refresh_subscription ==="
# Create alarm trigger that fires daily at 3:00 AM UTC
ibmcloud fn trigger update daily_refresh \
    --feed /whisk.system/alarms/alarm \
    --param cron "0 3 * * *" \
    --param trigger_payload '{}' 2>/dev/null || true

# Create rule connecting trigger to the function
ibmcloud fn rule update refresh_rule daily_refresh "$PACKAGE_NAME/refresh_subscription" 2>/dev/null || true

echo ""
echo "=== Deployment complete ==="
echo ""
echo "Endpoints:"
NAMESPACE=$(ibmcloud fn namespace get --properties | grep "ID" | awk '{print $2}' 2>/dev/null || echo "<namespace>")
REGION=$(ibmcloud target | grep "Region" | awk '{print $2}' 2>/dev/null || echo "<region>")
BASE="https://${REGION}.functions.appdomain.cloud/api/v1/web/${NAMESPACE}/${PACKAGE_NAME}"
echo "  process_new_photo: ${BASE}/process_new_photo"
echo "  display_sync_api:  ${BASE}/display_sync_api"
echo "  refresh_subscription: ${BASE}/refresh_subscription"
