# Clarity Lint - Dashboard Architecture

## Frontend
- components: Shared dashboard components
- features/overview: Overview workspace
- features/analyze: Text analysis
- features/documents: Document review
- features/evaluation: Evaluation workspace
- features/errors: Error analysis
- features/integrations: Integration workspace
- features/viva: Viva and demonstration
- features/settings: Settings
- lib/api.ts: API utilities

## Backend
- api: API entry point
- app: Application interface
- evaluation: Evaluation implementation
- tests: Automated test suite

The architecture separates shared components from feature-specific workspaces.
