# CLAUDE.md — Instructions pour l'agent Claude Code

## CI/CD Rules

### GitHub Actions
- **macos-14** : Xcode 15.0 a 15.4 uniquement
- **macos-15** : Xcode 16.0+ uniquement
- Ne jamais utiliser `macos-14` avec Xcode 16.x (n'existe pas sur ce runner)
- Toujours utiliser `actions/checkout@v4`
- Pour les builds iOS Simulator, toujours specifier `-skipPackagePluginValidation`

### Swift Package
- Le package cible iOS 16+ et macOS 13+
- Tous les types publics doivent etre `Sendable`
- Les vues SwiftUI doivent etre encapsulees dans `#if canImport(SwiftUI)`
- Utiliser `@available(iOS 16.0, macOS 13.0, *)` sur les types SwiftUI

### Python Backend
- Python 3.11.9 (voir runtime.txt)
- FastAPI avec pydantic v2
- Deploiement sur Render.com (voir render.yaml)
- Tous les endpoints requierent le header `X-VLBH-Token`

## Git Conventions
- Messages de commit en anglais, prefixes: feat/fix/chore/ci/docs
- Toujours pusher sur la branche designee, jamais directement sur main
- Creer les PR via les outils GitHub MCP quand disponibles

## Validation Checklist (avant push)
- [ ] Les versions Xcode correspondent aux runners GitHub Actions
- [ ] Les tests compilent (`swift build` ne doit pas echouer)
- [ ] Les imports Python sont valides (`python -c "from main import app"`)
- [ ] Pas de secrets (.env, tokens) dans les fichiers commites
