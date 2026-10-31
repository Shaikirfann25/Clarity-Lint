# Clarity Lint — Annotation Guide

## 1. What Is Clarity Lint?

Clarity Lint is an NLP-powered tool that automatically detects ambiguous language in
sentences. "Ambiguous" means the sentence could be understood in more than one way, or
its meaning is unclear without extra context. Clear writing matters in software requirements,
academic papers, legal documents, and everyday communication.

The goal of annotation is to label each sentence with the **one main ambiguity type** that
makes it unclear (or confirm that it is clear). These labelled examples train and evaluate
the machine-learning models that power Clarity Lint.

---

## 2. The Five Labels

| Label         | Short name     | What it means |
|---------------|----------------|---------------|
| `vague`       | Vague language | Words or phrases with no precise, shared definition in context. The reader cannot determine the exact meaning. |
| `attachment`  | Attachment ambiguity | A modifier (adjective, adverb, or relative clause) can grammatically attach to more than one word, creating two different meanings. |
| `scope`       | Scope ambiguity | A quantifier (`all`, `every`, `not`, `some`) or negation applies to an uncertain part of the sentence. |
| `pronoun`     | Pronoun ambiguity | A pronoun (`he`, `she`, `it`, `they`, `this`) does not clearly refer to one specific noun. |
| `no_ambiguity`| Clear sentence | The sentence has one obvious, unambiguous meaning. |

---

## 3. Detailed Label Definitions and Decision Rules

### 3.1 `vague` — Vague Language

**When to use:** The key word or phrase lacks a measurable, agreed-upon meaning in the
given context. Replacing the vague word with a specific value would change the reader's
understanding.

**Common vague words:** *good, fast, soon, many, few, large, small, efficient, modern,
appropriate, reasonable, several, better, high-quality.*

**Decision rule:**
> Ask: "Can I replace this word with a number or a specific term without losing meaning?"
> If yes, the word is vague.

**Examples:**

| # | Sentence | Why it is `vague` |
|---|----------|-------------------|
| 1 | "The system should respond quickly." | "Quickly" has no defined threshold — 100 ms? 2 s? |
| 2 | "Please submit the report soon." | "Soon" could mean minutes, hours, or days. |
| 3 | "The database stores a large number of records." | "Large" is relative; 1 000 and 1 000 000 are both "large" depending on context. |

---

### 3.2 `attachment` — Attachment Ambiguity

**When to use:** A modifying word or phrase can logically belong to two different parts of
the sentence, resulting in two distinct meanings.

**Common triggers:** Participial phrases, prepositional phrases, relative clauses (who /
which / that), stacked adjectives.

**Decision rule:**
> Draw a tree: can the modifier sensibly attach to two different nouns or verbs?
> If yes, it is `attachment`.

**Examples:**

| # | Sentence | Two possible readings |
|---|----------|-----------------------|
| 1 | "She saw the man with the telescope." | (a) She used a telescope to see the man. (b) The man had a telescope. |
| 2 | "I photographed the students writing in the library." | (a) The students were writing in the library. (b) I was in the library when I photographed them. |
| 3 | "We need to hire an engineer with five years of experience who speaks French." | (a) Five years of experience AND speaks French. (b) Five years of experience in speaking French. |

---

### 3.3 `scope` — Scope Ambiguity

**When to use:** A quantifier (`all`, `every`, `each`, `some`, `none`, `not`, `only`) or a
negation applies to an uncertain range of the sentence, producing multiple valid logical
readings.

**Decision rule:**
> Rewrite the sentence substituting different scopes. If the meaning changes significantly,
> it is `scope`.

**Examples:**

| # | Sentence | Two possible scopes |
|---|----------|---------------------|
| 1 | "Every student did not pass the exam." | (a) No student passed. (b) Not every student passed (some failed). |
| 2 | "All managers approved the budget and the timeline." | (a) Every manager approved both. (b) All approved the budget; all approved the timeline (could be different sets). |
| 3 | "She does not like coffee or tea." | (a) She dislikes both. (b) She dislikes at least one (logical OR scope). |

---

### 3.4 `pronoun` — Pronoun Ambiguity

**When to use:** A pronoun (`he`, `she`, `it`, `they`, `this`, `that`, `these`, `those`)
in the sentence does not clearly refer to exactly one specific noun in the same or previous
sentence.

**Decision rule:**
> Replace the pronoun with each candidate noun and check if both sentences make
> grammatical and logical sense. If more than one substitution works, label it `pronoun`.

**Examples:**

| # | Sentence | Ambiguous pronoun | Candidates |
|---|----------|-------------------|------------|
| 1 | "When Priya called Ananya, she was upset." | she | Priya or Ananya? |
| 2 | "The developers told the managers that they needed more time." | they | The developers or the managers? |
| 3 | "The cat sat on the mat and then it fell." | it | The cat or the mat? |

---

### 3.5 `no_ambiguity` — Clear Sentence

**When to use:** The sentence has exactly one reasonable interpretation. All pronouns,
modifiers, quantifiers, and terms are clearly defined in context.

**Examples:**

| # | Sentence | Why it is clear |
|---|----------|-----------------|
| 1 | "The server must respond within 200 milliseconds." | Specific, measurable threshold; one reading. |
| 2 | "Maria submitted the assignment on Friday." | One subject, one action, one time — unambiguous. |
| 3 | "The red button on the left panel opens the emergency door." | Modifier "on the left panel" clearly belongs to "button"; no other reading is natural. |

---

## 4. Labeling Rules for Annotators

1. **Pick exactly one label per sentence.** If you think a sentence has more than one
   ambiguity type, choose the *most prominent* one (see Section 5 below).

2. **Label the sentence as given.** Do not mentally add context that is not in the
   sentence.

3. **Focus on structural or semantic ambiguity.** Do not label a sentence as ambiguous
   just because you find the topic confusing.

4. **When in doubt, write a short explanation.** The `explanation` column in the dataset
   exists for this reason.

5. **Do not label a sentence `vague` simply because it uses abstract language.** The
   word or phrase must genuinely lack a common measurable definition in context.

---

## 5. Handling Sentences That Fit Multiple Categories

Some sentences seem to fit more than one label. Use this priority order to decide:

```
attachment  >  pronoun  >  scope  >  vague  >  no_ambiguity
```

**Why this order?**

- `attachment` is a structural ambiguity that creates two different sentence meanings —
  it is the clearest form of ambiguity and should be recognised first.
- `pronoun` is next because unclear reference creates a different subject or object,
  which changes the core meaning.
- `scope` is chosen when a quantifier or negation is the primary source of confusion.
- `vague` is chosen last among ambiguity types because it is about imprecision rather
  than structural ambiguity.

**Example of overlap:**

> "He gave the old man and woman a gift."

This sentence has both an `attachment` ambiguity ("old" modifies only "man", or both
"man and woman") and could be read as slightly `vague` ("old" is imprecise). Because
`attachment` takes priority, label it `attachment`.

---

## 6. Dataset Files

| File | Rows | Schema | Purpose |
|------|------|--------|---------|
| `data/clarity_lint_dataset.csv` | 20 | sentence, label, explanation, source_type | Initial starter sample used for guide validation |
| `data/clarity_lint_full_dataset.csv` | 507 | sentence_id, text, label, explanation, source_type | Full labeled dataset for model training and evaluation |

All sentences in both files are **synthetic** — they were written specifically for this project and are not collected from real documents.

---

## 7. Quick Reference Checklist

Before submitting each annotation, verify:

- [ ] I have read the full sentence at least twice.
- [ ] I checked all pronouns — each refers to exactly one noun.
- [ ] I checked all modifiers — each clearly attaches to one word.
- [ ] I checked all quantifiers/negations — scope is unambiguous.
- [ ] All key terms have a clear, measurable meaning in context.
- [ ] I chose exactly one label.
- [ ] I wrote a brief explanation justifying my label.
