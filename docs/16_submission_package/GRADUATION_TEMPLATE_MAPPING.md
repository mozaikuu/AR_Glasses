# Graduation project template alignment

The official OOXML structure is defined in:

`docs/00_Materials/Graudation-project-template.docx`

(New Mansoura University — Faculty of Computer Science and Engineering.)

## How this repository maps to that template

| Template section | Source in `docs/16_submission_package/full_documentation/` |
|------------------|----------------------------------------------------------|
| Cover (title, team, IDs, advisor line, faculty, year) | `00_cover_title_page.md` |
| Abstract, Acknowledgements, TOC note, symbols | `01_abstract_acknowledgements.md` |
| Chapter 1 — Introduction (1.1–1.5) | `02_chapter1_introduction.md` |
| Chapter 2 — Related work (2.1–2.3) | `03_` … `06_chapter2_related_work_part*.md` |
| Chapter 3 — Methodology (requirements, design, architecture, implementation, testing, tools) | `07_` … `11_chapter3_*.md` |
| Chapter 4 — Experimental results | `12_chapter4_experimental_results.md` |
| Chapter 5 — Discussion | `13_chapter5_discussion.md` |
| Chapter 6 — Conclusions | `14_chapter6_conclusions.md` |
| References | `15_references.md` (convert to faculty citation style in LibreOffice Writer if required) |
| Supplementary engineering narrative (extends page depth) | `16_supplementary_engineering_topics.md` |
| Appendices | `appendices/A_*.md` … `E_*.md` |

## Final deliverables (`dist/`)

After `build/export.ps1`, expect these **primary** files (exact set depends on optional steps):

| Deliverable | Format | Notes |
|-------------|--------|--------|
| Full report | `SmartGlasses_ProjectManual.docx`, `.pdf` | Pandoc `--reference-doc` + `--toc --toc-depth=3`; PDF via LibreOffice headless |
| Research summary | `SmartGlasses_ResearchPaper.docx`, `.pdf` | Same reference doc when template exists |
| Defense deck | `SmartGlasses_Defense.pptx`, `.pdf` | Impress opens `.pptx`; PDF via LibreOffice |
| Filled faculty cover | `Faculty_Template_Filled.docx`, `.pdf` | From `docx_tool.py fill-template` when `python-docx` + template path are available |

**What to upload:** follow faculty rules — some portals want **PDF only**, others want **editable `.docx`**. Keep both from each export.

## Exporting with template styles (LibreOffice-friendly)

`build/export.ps1` passes `--reference-doc` pointing at `docs/00_Materials/Graudation-project-template.docx` so Pandoc maps paragraphs to the template’s **styles** where possible.

**After export in LibreOffice Writer:** open `dist/SmartGlasses_ProjectManual.docx`, use **Tools → Update → Update All** if any TOC or index fields look stale. Add **Index of Tables** / **Index of Figures** if your committee requires them (Pandoc does not generate those fields).

**Direct template copy:** when `python-docx` is installed (`build/requirements-docx.txt`), `export.ps1` also writes **`dist/Faculty_Template_Filled.docx`** (and its **`.pdf`** when LibreOffice is found) — the faculty `.docx` with title and team placeholders replaced from `metadata.yaml`.

## Regenerating long body text

Run:

```text
python docs/16_submission_package/build/generate_expanded_docs.py
```

Then run `build/export.ps1`. The generator is intentionally verbose to reach graduation report length; tighten or remove `16_supplementary_engineering_topics.md` from `export.ps1` if your advisor prefers a shorter bound volume.
