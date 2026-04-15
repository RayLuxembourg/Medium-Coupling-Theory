# Cross-Referencing Rule

All files in the MCT repository should reference each other where relevant. This keeps readers oriented and avoids duplicating content.

## Format

```markdown
See [Section Title](relative/path/to/file.md#anchor) for details.
```

GitHub auto-generates anchors from headings. The anchor is the heading text, lowercased, spaces replaced with hyphens, special characters removed. For example:

- `## 2. Derivation: Newtonian Gravity from Medium Flow` becomes `#2-derivation-newtonian-gravity-from-medium-flow`
- `### 14.3 Prediction 2: CMB Toroidal Topology Signatures` becomes `#143-prediction-2-cmb-toroidal-topology-signatures`

## Reference map

These are the standard reference patterns in this project:

| From | To | When |
|---|---|---|
| README.md postulates | phase2/ derivations | A postulate has a formal derivation |
| README.md phenomena | phase2/ sections | A phenomenon has a mathematical treatment |
| README.md predictions | phase2/ Section 14 | A prediction is listed in the table |
| phase2/ sections | earlier phase2/ sections | A derivation builds on a previous result |
| CLAUDE.md roadmap | phase2/, phase3/, phase4/ | A phase has content |

## Principles

- Reference forward (README to phase2) more than backward. The reader moves from conceptual to formal.
- Within phase2/, reference earlier sections freely. Section 6 depends on Section 2; say so.
- One reference per concept. Don't scatter three links to the same derivation across a paragraph.
- If you are about to repeat an explanation that exists elsewhere, link to it instead.
