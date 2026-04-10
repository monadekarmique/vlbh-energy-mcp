#!/usr/bin/env python3
"""
update_testflight_info.py
=========================

Remplit la section "Test Information" TestFlight pour l'app SVLBH Panel via
l'App Store Connect API, afin que les testeurs externes (Yvette, Daphne, ...)
du groupe "SVLBH Bash 3 a 5 externe" puissent utiliser l'app.

Ce que ce script met a jour:
  1. `betaAppLocalizations` (description, feedback email, marketing URL,
     privacy policy URL, TOS URL) pour la locale fr-FR.
  2. `betaAppReviewDetails` (contact pour l'Apple Beta Review Team).
  3. `betaBuildLocalizations.whatToTest` pour le build le plus recent du groupe
     "SVLBH Bash 3 a 5 externe" (si le groupe existe).

Utilisation locale (Mac de Patrick)
-----------------------------------
    export APP_STORE_CONNECT_KEY_ID="XXXXXXXXXX"
    export APP_STORE_CONNECT_ISSUER_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    export APP_STORE_CONNECT_PRIVATE_KEY="$(cat ~/.appstoreconnect/AuthKey_XXXXXXXXXX.p8)"
    python ci_scripts/update_testflight_info.py

Utilisation via GitHub Actions
------------------------------
Voir `.github/workflows/testflight-info.yml` (workflow_dispatch). Patrick doit
ajouter 3 secrets dans le repo GitHub:
  - APP_STORE_CONNECT_KEY_ID
  - APP_STORE_CONNECT_ISSUER_ID
  - APP_STORE_CONNECT_PRIVATE_KEY (contenu complet du .p8, y compris
    "-----BEGIN PRIVATE KEY-----" et "-----END PRIVATE KEY-----")

Dependances: `pip install pyjwt cryptography requests`.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import jwt  # PyJWT
import requests

API_BASE = "https://api.appstoreconnect.apple.com/v1"
CONFIG_PATH = Path(__file__).parent / "testflight_info.json"


# ---------------------------------------------------------------------------
# Authentification
# ---------------------------------------------------------------------------
def make_jwt(key_id: str, issuer_id: str, private_key: str) -> str:
    """Genere un JWT ES256 valide 15 minutes pour l'App Store Connect API."""
    now = int(time.time())
    payload = {
        "iss": issuer_id,
        "iat": now,
        "exp": now + 15 * 60,
        "aud": "appstoreconnect-v1",
    }
    headers = {"alg": "ES256", "kid": key_id, "typ": "JWT"}
    return jwt.encode(payload, private_key, algorithm="ES256", headers=headers)


def auth_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


# ---------------------------------------------------------------------------
# Helpers HTTP
# ---------------------------------------------------------------------------
def _get(token: str, path: str, params: dict[str, Any] | None = None) -> dict:
    url = path if path.startswith("http") else f"{API_BASE}{path}"
    r = requests.get(url, headers=auth_headers(token), params=params, timeout=30)
    if r.status_code >= 400:
        raise RuntimeError(f"GET {url} -> {r.status_code}: {r.text}")
    return r.json()


def _patch(token: str, path: str, body: dict) -> dict:
    url = f"{API_BASE}{path}"
    r = requests.patch(url, headers=auth_headers(token), json=body, timeout=30)
    if r.status_code >= 400:
        raise RuntimeError(f"PATCH {url} -> {r.status_code}: {r.text}")
    return r.json()


def _post(token: str, path: str, body: dict) -> dict:
    url = f"{API_BASE}{path}"
    r = requests.post(url, headers=auth_headers(token), json=body, timeout=30)
    if r.status_code >= 400:
        raise RuntimeError(f"POST {url} -> {r.status_code}: {r.text}")
    return r.json()


# ---------------------------------------------------------------------------
# Lookups
# ---------------------------------------------------------------------------
def find_app_id(token: str, bundle_id: str, override: str | None) -> str:
    if override:
        print(f"[INFO] Utilisation de l'app_id_override: {override}")
        return override
    data = _get(token, "/apps", {"filter[bundleId]": bundle_id, "limit": 1})
    items = data.get("data", [])
    if not items:
        raise RuntimeError(f"Aucune app trouvee avec bundle_id={bundle_id}")
    app_id = items[0]["id"]
    print(f"[OK] App trouvee: {bundle_id} -> id={app_id}")
    return app_id


def find_beta_group(token: str, app_id: str, group_name: str) -> dict | None:
    data = _get(
        token,
        "/betaGroups",
        {"filter[app]": app_id, "filter[name]": group_name, "limit": 10},
    )
    items = data.get("data", [])
    if not items:
        return None
    return items[0]


def get_latest_build_id(token: str, app_id: str, group_id: str | None) -> str | None:
    """Recupere le build le plus recent de l'app (ou filtre par groupe si fourni)."""
    params: dict[str, Any] = {
        "filter[app]": app_id,
        "sort": "-uploadedDate",
        "limit": 1,
    }
    if group_id:
        params["filter[betaGroups]"] = group_id
    data = _get(token, "/builds", params)
    items = data.get("data", [])
    if not items:
        return None
    return items[0]["id"]


# ---------------------------------------------------------------------------
# Updates
# ---------------------------------------------------------------------------
def upsert_beta_app_localization(
    token: str, app_id: str, locale: str, attrs: dict[str, Any]
) -> None:
    """Cree ou met a jour le betaAppLocalization pour la locale donnee."""
    data = _get(token, f"/apps/{app_id}/betaAppLocalizations", {"limit": 50})
    existing = None
    for item in data.get("data", []):
        if item.get("attributes", {}).get("locale") == locale:
            existing = item
            break

    # Mapping des noms de champs: notre JSON utilise snake_case, l'API camelCase.
    mapping = {
        "feedback_email": "feedbackEmail",
        "marketing_url": "marketingUrl",
        "privacy_policy_url": "privacyPolicyUrl",
        "tos_url": "tosUrl",
        "description": "description",
    }
    api_attrs = {mapping[k]: v for k, v in attrs.items() if k in mapping and v}

    if existing:
        loc_id = existing["id"]
        body = {
            "data": {
                "type": "betaAppLocalizations",
                "id": loc_id,
                "attributes": api_attrs,
            }
        }
        _patch(token, f"/betaAppLocalizations/{loc_id}", body)
        print(f"[OK] betaAppLocalization ({locale}) mis a jour")
    else:
        body = {
            "data": {
                "type": "betaAppLocalizations",
                "attributes": {"locale": locale, **api_attrs},
                "relationships": {
                    "app": {"data": {"type": "apps", "id": app_id}}
                },
            }
        }
        _post(token, "/betaAppLocalizations", body)
        print(f"[OK] betaAppLocalization ({locale}) cree")


def update_beta_app_review_detail(
    token: str, app_id: str, attrs: dict[str, Any]
) -> None:
    data = _get(token, f"/apps/{app_id}/betaAppReviewDetail")
    detail_id = data.get("data", {}).get("id")
    if not detail_id:
        raise RuntimeError("betaAppReviewDetail introuvable pour cette app")

    mapping = {
        "contact_first_name": "contactFirstName",
        "contact_last_name": "contactLastName",
        "contact_email": "contactEmail",
        "contact_phone": "contactPhone",
        "demo_account_name": "demoAccountName",
        "demo_account_password": "demoAccountPassword",
        "demo_account_required": "demoAccountRequired",
        "notes": "notes",
    }
    api_attrs = {mapping[k]: v for k, v in attrs.items() if k in mapping}

    body = {
        "data": {
            "type": "betaAppReviewDetails",
            "id": detail_id,
            "attributes": api_attrs,
        }
    }
    _patch(token, f"/betaAppReviewDetails/{detail_id}", body)
    print("[OK] betaAppReviewDetail mis a jour")


def update_what_to_test(
    token: str, build_id: str, locale: str, what_to_test: str
) -> None:
    """Cree ou met a jour betaBuildLocalizations.whatToTest pour un build."""
    data = _get(token, f"/builds/{build_id}/betaBuildLocalizations", {"limit": 50})
    existing = None
    for item in data.get("data", []):
        if item.get("attributes", {}).get("locale") == locale:
            existing = item
            break

    if existing:
        loc_id = existing["id"]
        body = {
            "data": {
                "type": "betaBuildLocalizations",
                "id": loc_id,
                "attributes": {"whatToTest": what_to_test},
            }
        }
        _patch(token, f"/betaBuildLocalizations/{loc_id}", body)
        print(f"[OK] betaBuildLocalization ({locale}) mis a jour pour build {build_id}")
    else:
        body = {
            "data": {
                "type": "betaBuildLocalizations",
                "attributes": {"locale": locale, "whatToTest": what_to_test},
                "relationships": {
                    "build": {"data": {"type": "builds", "id": build_id}}
                },
            }
        }
        _post(token, "/betaBuildLocalizations", body)
        print(f"[OK] betaBuildLocalization ({locale}) cree pour build {build_id}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    key_id = os.environ.get("APP_STORE_CONNECT_KEY_ID", "").strip()
    issuer_id = os.environ.get("APP_STORE_CONNECT_ISSUER_ID", "").strip()
    private_key = os.environ.get("APP_STORE_CONNECT_PRIVATE_KEY", "").strip()

    if not (key_id and issuer_id and private_key):
        print(
            "[ERREUR] Variables manquantes: APP_STORE_CONNECT_KEY_ID, "
            "APP_STORE_CONNECT_ISSUER_ID, APP_STORE_CONNECT_PRIVATE_KEY",
            file=sys.stderr,
        )
        return 2

    if not CONFIG_PATH.exists():
        print(f"[ERREUR] Config introuvable: {CONFIG_PATH}", file=sys.stderr)
        return 2

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    bundle_id = config["bundle_id"]
    locale = config.get("locale", "fr-FR")
    group_name = config.get("beta_group_name", "")

    token = make_jwt(key_id, issuer_id, private_key)

    app_id = find_app_id(token, bundle_id, config.get("app_id_override"))

    # 1. Beta App Localization (description, feedback email, URLs)
    upsert_beta_app_localization(
        token, app_id, locale, config["beta_app_localization"]
    )

    # 2. Beta App Review Detail (contact Apple)
    update_beta_app_review_detail(token, app_id, config["beta_app_review_detail"])

    # 3. "What to Test" sur le build le plus recent du groupe
    group = find_beta_group(token, app_id, group_name) if group_name else None
    if group:
        print(f"[OK] Groupe beta trouve: '{group_name}' -> id={group['id']}")
        build_id = get_latest_build_id(token, app_id, group["id"])
    else:
        if group_name:
            print(
                f"[WARN] Groupe '{group_name}' introuvable. "
                "Fallback sur le build le plus recent de l'app."
            )
        build_id = get_latest_build_id(token, app_id, None)

    what_to_test = config.get("beta_build_localization_what_to_test", "").strip()
    if build_id and what_to_test:
        update_what_to_test(token, build_id, locale, what_to_test)
    elif not build_id:
        print("[WARN] Aucun build trouve, 'What to Test' non mis a jour.")

    print("\n[SUCCES] Test Information TestFlight mis a jour.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
