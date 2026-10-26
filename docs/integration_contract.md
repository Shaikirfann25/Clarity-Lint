# Integration Contract — Team Coordination

## Label vocabulary
- `no_ambiguity`
- `vague`
- `attachment`
- `scope`
- `pronoun`

## Required detection fields
- `source`: e.g. `rules`, `model`, `prompt_baseline`
- `label`: one of the five agreed labels
- `span`: exact substring when available, else null
- `confidence`: model-provided score or null; never invent one
- `reason`: short reason

## Ownership
- Person 1: dataset, annotation, preprocessing and frozen splits
- Person 2: rules detector and unit tests
- Person 3: DistilBERT model and prediction function
- Person 4: explanations, rewrites and prompt baseline
- Person 5: adapters, Streamlit UI, evaluation, error analysis and demo

Person 5 may normalize interfaces at the integration boundary, but should not silently rewrite teammates' core logic.
