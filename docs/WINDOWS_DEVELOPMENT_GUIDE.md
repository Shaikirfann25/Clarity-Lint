# Clarity Lint - Windows Development Guide

## Open project
Set-Location "C:\Users\chaitanya\Downloads\clarity_lint\Clarity_Lint_Imperial_Jade"

## Backend tests
python -m pytest -q

## Frontend build
Set-Location .\web
npm run build

## Git workflow
git status
git diff
git add <file>
git commit -m "docs: describe the actual change"
git push origin main

Use PowerShell for the Windows development workflow.
