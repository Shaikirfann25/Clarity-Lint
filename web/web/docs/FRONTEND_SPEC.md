# Clarity Lint Frontend — Product and Engineering Specification

## Product intent
The frontend is a human-in-the-loop NLP review workspace. It should make it easy to inspect possible ambiguity, understand why a span was flagged, compare interpretations, and evaluate detection methods without overstating the reliability of heuristic or synthetic data.

## Reference direction
The supplied Canonry website is used as a design reference for a complete multi-workspace product: editorial hierarchy, generous page composition, consistent navigation, clear page-level workflows, and detailed panels. Clarity Lint retains its own Imperial Jade palette, typography choices, product language, and NLP-specific information architecture.

## Information architecture
1. Overview — project orientation, pipeline, system pulse and quick actions.
2. Analyze Text — one-sentence analysis, findings, readings, rewrites and raw run details.
3. Document Review — document-level input, sentence-by-sentence review, counts, distribution and JSON export.
4. Evaluation Lab — synthetic fixture, labelled CSV upload, metrics and confusion matrices.
5. Error Analysis — curated failure-mode examples and filters.
6. Integration Centre — health/status checks, endpoint inventory and operational guidance.
7. Viva & Demo — project questions, demo script and architecture walkthrough.
8. Settings — theme, compact navigation and review policy.

## Visual language
- Background: deep evergreen; surfaces: layered jade; accent: antique gold.
- Display type: editorial serif; interface type: neutral sans-serif; metadata: monospaced.
- Cards use restrained borders and low-contrast surfaces. Gold is reserved for emphasis and key actions.
- The interface avoids a wall of equally weighted widgets. Each page has a single clear primary task.
- The sidebar groups workflows by Workspace, Quality and Project.
- Topbar provides workspace context, API state, time, command search and theme control.

## Interaction principles
- Every primary button has an action and a disabled/loading state where needed.
- API errors are surfaced in a toast or local status panel without destroying user input.
- Long lists are grouped and expandable. Findings expose evidence, reason and source.
- Command search opens with Ctrl+K or Cmd+K and closes with Escape.
- Theme selection persists in local browser storage.
- Responsive navigation becomes a mobile drawer at narrow widths.
- Export actions generate a local JSON download and do not mutate backend state.

## Data integrity
- `demo_fallback` means heuristic fallback, not a trained model.
- Demo evaluation examples are synthetic interface fixtures.
- Error analysis cases are illustrative teaching examples, not empirical rates.
- A clean result means no configured pattern was triggered; it is not proof of unambiguous text.
- Clarity indicator is a project-defined summary and not a legal-risk score.
- Predictions from rules, model and prompt baselines remain separate.

## API contracts
- `GET /health`: service health.
- `GET /api/status`: integration status.
- `POST /api/analyze`: JSON body `{ text }`; returns detections, explanation, readings, rewrites, mode and latency.
- `POST /api/document`: JSON body `{ text }`; returns sentence analyses and document statistics.
- `GET /api/evaluation/demo`: returns synthetic demonstration metrics.
- `POST /api/evaluate`: multipart CSV with `gold_label` and one or more prediction columns.

## CSV requirements
- Required gold column: `gold_label`.
- Supported prediction columns: `rules_pred`, `model_pred`, `prompt_pred`.
- Supported labels: `no_ambiguity`, `vague`, `attachment`, `scope`, `pronoun`.
- Use the same frozen examples for all compared methods.
- Gold labels should be reviewed by humans before reporting results.

## Accessibility checklist
- All actions use semantic buttons or form controls.
- Inputs have clear nearby labels and character counts.
- Focus indicators remain visible against both themes.
- Status uses text and not colour alone.
- Responsive layout avoids requiring horizontal scrolling for primary workflows.
- Text sizes remain readable and line lengths are controlled.
- Motion is decorative and not necessary for task completion.

## Security and privacy notes
- The frontend sends submitted text to the configured API endpoint.
- The default API endpoint is local (`127.0.0.1:8000`).
- Do not place API secrets in client-side environment variables.
- Do not persist submitted legal or policy text to browser storage by default.
- Review uploaded CSV files before sharing them; they may contain sensitive content.

## Manual verification sequence
1. Start the FastAPI service.
2. Start Next.js in a separate terminal.
3. Confirm the overview health status.
4. Analyze a vague sentence and inspect the evidence span.
5. Review a multi-sentence document and expand each row.
6. Load synthetic evaluation and confirm the synthetic label is visible.
7. Upload a labelled CSV and inspect actual computed metrics.
8. Filter the illustrative error cases.
9. Refresh integration checks.
10. Open the viva script and switch themes.

## Known limitations
- Sentence splitting is performed by the backend integration layer and may not handle all abbreviations or complex punctuation.
- The demo fallback is deliberately lightweight and conservative.
- Error analysis examples are static teaching fixtures until a real prediction log is connected.
- Evaluation views depend on the shape returned by the existing API.
- The frontend does not claim to persist document history or create accounts.
