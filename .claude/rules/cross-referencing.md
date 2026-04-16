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
| README.md postulates | formalization/ | A postulate has a formal derivation |
| README.md phenomena | formalization/ sections | A phenomenon has a mathematical treatment |
| README.md predictions | formalization/ Section 14 | A prediction is listed in the table |
| formalization/ sections | earlier formalization/ sections | A derivation builds on a previous result |
| foundations/ | formalization/ | Foundational work references core derivations |
| foundations/ | extensions/ | Foundational work references open problems |
| extensions/ | formalization/ | Open problems reference core derivations |
| extensions/ | foundations/ | Open problems reference foundational theory |
| extensions/ | sibling extensions/ | Open problems cross-reference each other |
| applications/ | formalization/, extensions/, simulation/ | Applications reference theory they depend on |
| simulation/ | formalization/, extensions/ | Simulation references what it tests |

**Path conventions:** Use relative paths from the file's location.
- From formalization/ to extensions/: `../extensions/file.md`
- From foundations/ to formalization/: `../formalization/file.md`
- Between siblings in the same directory: `file.md`

## Principles

- Reference forward (README to formalization to foundations/extensions) more than backward.
- Within formalization/, reference earlier sections freely. Section 6 depends on Section 2; say so.
- One reference per concept. Don't scatter three links to the same derivation across a paragraph.
- If you are about to repeat an explanation that exists elsewhere, link to it instead.
