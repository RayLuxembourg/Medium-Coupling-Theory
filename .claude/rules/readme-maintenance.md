# README.md Maintenance Rule

When modifying any content in the MCT repository, check whether README.md needs updating.

## When to update README.md

- A new section is added to `formalization/mathematical-framework.md`: add a cross-reference from the relevant README section. If the new section addresses a phenomenon listed in Section 3, add a "See [Section N](formalization/, foundations/, extensions/, applications/...)" link. If it is a new testable prediction, add it to the predictions table in Section 5.
- A new phase directory is created (phase3/, phase4/): update the Roadmap in Section 6 with a link to the new content and mark the phase status.
- A derivation changes the status of a postulate (e.g., from qualitative to formally derived): update the corresponding postulate section in README to note this and link to the derivation.
- The project structure changes: update the file tree in CLAUDE.md.

## When NOT to update README.md

- Internal refactors within formalization/, foundations/, extensions/, applications/ that don't change what is derived or predicted.
- Fixing typos or formatting in formalization/, foundations/, extensions/, applications/ only.
- Adding conversation transcripts or development notes.

## Cross-reference format

Use relative markdown links with section anchors:

```markdown
See [Section 5](formalization/mathematical-framework.md#5-derivation-mass-quantization-from-angular-momentum) for the quantization argument.
```

Keep reference text short and specific. One sentence, pointing to one location. If a README section references multiple Phase 2 sections, list them at the end of the relevant paragraph rather than inline.

## Writing style

README.md follows the same writing rules as all project files (see CLAUDE.md, Style & Approach). No em dashes, no AI patterns, GitHub LaTeX for any math expressions.

README.md is the public-facing document. It should be readable by a physicist who has never seen the project before. Keep it at the conceptual level but always link to the formal treatment.
