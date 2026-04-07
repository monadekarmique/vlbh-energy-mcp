#!/usr/bin/env python3
"""
Render Deploy CLI — gère le déploiement vlbh-energy-mcp via l'API Render.
Usage:
  python deploy_render.py setup <RENDER_API_KEY>   # Configure et active l'auto-deploy
  python deploy_render.py status                    # Vérifie le statut du service
  python deploy_render.py deploy                    # Déclenche un deploy manuel
  python deploy_render.py logs                      # Affiche les derniers logs
"""
import sys
import os
import json
import time

try:
    import httpx
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx", "-q"])
    import httpx

RENDER_API = "https://api.render.com/v1"
SERVICE_NAME = "vlbh-energy-mcp"
KEY_FILE = os.path.join(os.path.dirname(__file__), ".render_key")


def _load_key() -> str:
    if os.path.exists(KEY_FILE):
        return open(KEY_FILE).read().strip()
    key = os.environ.get("RENDER_API_KEY", "")
    if not key:
        print("No Render API key found. Run: python deploy_render.py setup <YOUR_KEY>")
        sys.exit(1)
    return key


def _headers(key: str) -> dict:
    return {"Authorization": f"Bearer {key}", "Accept": "application/json"}


def _find_service(client: httpx.Client, key: str) -> dict | None:
    resp = client.get(f"{RENDER_API}/services", headers=_headers(key),
                      params={"name": SERVICE_NAME, "limit": 10})
    resp.raise_for_status()
    for item in resp.json():
        svc = item.get("service", item)
        if svc.get("name") == SERVICE_NAME:
            return svc
    return None


def cmd_setup(key: str):
    """Store key, find or report service, enable auto-deploy."""
    with open(KEY_FILE, "w") as f:
        f.write(key)
    os.chmod(KEY_FILE, 0o600)
    print(f"API key saved to {KEY_FILE}")

    client = httpx.Client(timeout=15)
    # Verify key
    resp = client.get(f"{RENDER_API}/owners", headers=_headers(key))
    if resp.status_code == 401:
        print("Invalid API key.")
        os.remove(KEY_FILE)
        sys.exit(1)
    resp.raise_for_status()
    owners = resp.json()
    if owners:
        owner = owners[0].get("owner", owners[0])
        print(f"Authenticated as: {owner.get('name', owner.get('email', 'OK'))}")

    svc = _find_service(client, key)
    if svc:
        svc_id = svc["id"]
        print(f"Service found: {svc['name']} ({svc_id})")
        print(f"  URL: {svc.get('serviceDetails', {}).get('url', 'N/A')}")
        print(f"  Branch: {svc.get('branch', 'N/A')}")
        print(f"  Auto-Deploy: {svc.get('autoDeploy', 'N/A')}")

        if svc.get("autoDeploy") != "yes":
            print("Enabling auto-deploy...")
            resp = client.patch(f"{RENDER_API}/services/{svc_id}",
                                headers={**_headers(key), "Content-Type": "application/json"},
                                json={"autoDeploy": "yes"})
            resp.raise_for_status()
            print("Auto-deploy enabled!")
        else:
            print("Auto-deploy already active.")
    else:
        print(f"Service '{SERVICE_NAME}' not found on Render.")
        print("Create it via Blueprint: dashboard.render.com → New → Blueprint → connect this repo.")
    client.close()


def cmd_status():
    key = _load_key()
    client = httpx.Client(timeout=15)
    svc = _find_service(client, key)
    if not svc:
        print("Service not found.")
        sys.exit(1)
    svc_id = svc["id"]
    print(f"Service: {svc['name']} ({svc_id})")
    print(f"  URL: {svc.get('serviceDetails', {}).get('url', 'N/A')}")
    print(f"  Branch: {svc.get('branch', 'N/A')}")
    print(f"  Auto-Deploy: {svc.get('autoDeploy', 'N/A')}")

    # Latest deploy
    resp = client.get(f"{RENDER_API}/services/{svc_id}/deploys",
                      headers=_headers(key), params={"limit": 1})
    resp.raise_for_status()
    deploys = resp.json()
    if deploys:
        d = deploys[0].get("deploy", deploys[0])
        print(f"  Latest deploy: {d.get('status', '?')} ({d.get('finishedAt') or d.get('createdAt', '?')})")
        if d.get("commit"):
            print(f"  Commit: {d['commit'].get('message', '')[:80]}")
    client.close()


def cmd_deploy():
    key = _load_key()
    client = httpx.Client(timeout=15)
    svc = _find_service(client, key)
    if not svc:
        print("Service not found.")
        sys.exit(1)
    svc_id = svc["id"]
    print(f"Triggering deploy for {svc['name']}...")
    resp = client.post(f"{RENDER_API}/services/{svc_id}/deploys",
                       headers={**_headers(key), "Content-Type": "application/json"},
                       json={})
    resp.raise_for_status()
    d = resp.json().get("deploy", resp.json())
    print(f"Deploy triggered: {d.get('id', '?')} — status: {d.get('status', '?')}")

    # Poll status
    deploy_id = d.get("id")
    if deploy_id:
        for i in range(30):
            time.sleep(5)
            r = client.get(f"{RENDER_API}/services/{svc_id}/deploys/{deploy_id}",
                           headers=_headers(key))
            r.raise_for_status()
            dd = r.json().get("deploy", r.json())
            status = dd.get("status", "?")
            print(f"  [{i*5+5}s] {status}")
            if status in ("live", "deactivated", "build_failed", "update_failed", "canceled"):
                break
    client.close()


def cmd_logs():
    key = _load_key()
    client = httpx.Client(timeout=15)
    svc = _find_service(client, key)
    if not svc:
        print("Service not found.")
        sys.exit(1)
    svc_id = svc["id"]
    # Get latest deploy logs
    resp = client.get(f"{RENDER_API}/services/{svc_id}/deploys",
                      headers=_headers(key), params={"limit": 1})
    resp.raise_for_status()
    deploys = resp.json()
    if not deploys:
        print("No deploys found.")
        return
    d = deploys[0].get("deploy", deploys[0])
    deploy_id = d.get("id")
    print(f"Logs for deploy {deploy_id} ({d.get('status', '?')}):")
    resp = client.get(f"{RENDER_API}/services/{svc_id}/deploys/{deploy_id}/logs",
                      headers=_headers(key))
    if resp.status_code == 200:
        for line in resp.json():
            print(f"  {line.get('timestamp', '')} {line.get('message', line)}")
    else:
        print(f"  (logs not available: {resp.status_code})")
    client.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "setup":
        if len(sys.argv) < 3:
            print("Usage: python deploy_render.py setup <RENDER_API_KEY>")
            sys.exit(1)
        cmd_setup(sys.argv[2])
    elif cmd == "status":
        cmd_status()
    elif cmd == "deploy":
        cmd_deploy()
    elif cmd == "logs":
        cmd_logs()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
