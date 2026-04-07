# Ecosysteme VLBH Energy — Architecture & CI/CD

> Digital Shaman Lab — monadekarmique | Avril 2026

```mermaid
graph TD
    subgraph APPS["📱 Apps iOS → TestFlight"]
        SVLBH["SVLBH Panel<br/>.xcodeproj"]
        CHRONO["Chrono Fu<br/>.xcodeproj"]
        TF(("TestFlight<br/>App Store"))
    end

    subgraph PKG["📦 Swift Package (SPM) ⭐"]
        KIT["VLBHEnergyKit<br/>Models + Service<br/>ViewModel + Views"]
        TESTS["Tests<br/>8 unit tests<br/>Codable round-trip"]
        CISCRIPTS["ci_scripts/<br/>post_clone<br/>pre/post_xcodebuild"]
        CLAUDE["CLAUDE.md<br/>+ SessionStart hook"]
    end

    subgraph CICD["⚙️ CI/CD ⭐"]
        GHA["GitHub Actions<br/>swift-ci.yml<br/>python-ci.yml"]
        XCC["Xcode Cloud<br/>⏳ a activer<br/>depuis les apps"]
        RENDER["Render.com<br/>auto-deploy<br/>Python backend"]
        GH["GitHub<br/>monadekarmique/<br/>vlbh-energy-mcp"]
    end

    subgraph BACKEND["🔴 Backend API (Python) ⭐"]
        API["FastAPI<br/>/tore /session /slm<br/>/sla /lead · 14 routes"]
        MAKE[("Make.com EU2<br/>Webhooks<br/>+ Datastores")]
        WP["vlbh.energy<br/>WordPress"]
    end

    SVLBH -->|import SPM| KIT
    CHRONO -->|import SPM| KIT
    SVLBH -->|deploy| TF
    CHRONO -->|deploy| TF

    KIT -->|push triggers| GHA
    TESTS -->|tests| XCC
    GHA -->|validates| API
    GH -.->|agent reads| CLAUDE

    KIT -.->|HTTP calls| API
    RENDER -->|hosts| API
    API -->|webhooks| MAKE

    style APPS fill:#dbeafe,stroke:#3b82f6,color:#1e3a5f
    style PKG fill:#dcfce7,stroke:#22c55e,color:#14532d
    style CICD fill:#ffedd5,stroke:#f97316,color:#7c2d12
    style BACKEND fill:#fee2e2,stroke:#ef4444,color:#7f1d1d
    style TF fill:#ede9fe,stroke:#8b5cf6,color:#4c1d95
    style MAKE fill:#fecaca,stroke:#ef4444,color:#7f1d1d
    style XCC fill:#fed7aa,stroke:#f97316,color:#7c2d12
```

## Ce qui a ete realise dans cette session ⭐

| Composant | Detail |
|---|---|
| **VLBHEnergyKit** | Swift Package iOS 16+ / macOS 13+ — modeles publics Sendable, ToreService, ViewModel, vues SwiftUI |
| **Tests** | 8 tests unitaires (Codable round-trip, enums, nil handling) |
| **GitHub Actions** | `swift-ci.yml` (Xcode 15.4 sur macos-14 + Xcode 16.2 sur macos-15) + `python-ci.yml` |
| **ci_scripts/** | Scripts Xcode Cloud (post_clone, pre/post_xcodebuild) |
| **CLAUDE.md** | Regles projet, credentials, comportement agent, checklist validation |
| **SessionStart hook** | Install pip deps + validate FastAPI au demarrage de session |
| **PR #1** | Creee, CI verte, mergee dans main |

## Prochaines etapes

| Action | Qui | Ou |
|---|---|---|
| Integrer VLBHEnergyKit dans SVLBH Panel | Claude local (Mac) | `File > Add Package Dependencies` |
| Integrer VLBHEnergyKit dans Chrono Fu | Claude local (Mac) | `File > Add Package Dependencies` |
| Activer Xcode Cloud | Depuis Xcode | `Integrate > Create Workflow` (sur les apps, pas le package) |
| Deploy sur TestFlight | Xcode Cloud | Automatique apres activation |
