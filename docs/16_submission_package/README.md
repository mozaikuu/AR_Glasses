# Submission package (`docs/16_submission_package`)

**Team:** Ahmed Mohamed Moussa (222101392) · Sandy Samy Samir (222101524) · Basma Ahmed Elmorsy (221101164)  
**Faculty:** Faculty of Computer Science and Engineering, New Mansoura University — Academic year 2025–2026

Version-controlled **Markdown sources** for:

1. **Presentation** → `presentation/slides.md` → `dist/SmartGlasses_Defense.pptx` **and** `dist/SmartGlasses_Defense.pdf` (via LibreOffice)
2. **Research paper** → `research_paper/paper.md` (+ `references.bib`) → `dist/SmartGlasses_ResearchPaper.docx` **and** `.pdf`
3. **Graduation project manual** → `full_documentation/*.md` (merged in `export.ps1` order) → `dist/SmartGlasses_ProjectManual.docx` **and** `.pdf` (manual includes a **TOC field** from Pandoc `--toc` for LibreOffice to refresh)

**Source of truth:** implementation under `app/`, `start.py`, `clients/`, `tests/`. See [SOURCE_ALIGNMENT.md](SOURCE_ALIGNMENT.md).

## Faculty template (OOXML `.docx`)

Official structure and styles: [docs/00_Materials/Graudation-project-template.docx](../00_Materials/Graudation-project-template.docx)

Chapter mapping Markdown → template sections: [GRADUATION_TEMPLATE_MAPPING.md](GRADUATION_TEMPLATE_MAPPING.md)

`build/export.ps1` uses Pandoc `--reference-doc` pointing at that template so headings and body text pick up **template styles** where Pandoc can map them.

### LibreOffice Writer (no Microsoft Word required)

1. Open `dist/SmartGlasses_ProjectManual.docx` in **LibreOffice Writer**.
2. Refresh dynamic content: **Tools → Update → Update All** (TOC and cross-references). The export script also runs **headless LibreOffice → PDF**, which normally refreshes the TOC in the generated PDF.
3. **List of Tables / List of Figures:** Pandoc does not emit those Word/OOXML index fields. Add them in Writer: **Insert → Table of Contents and Index → Index of Tables** (and the figure index the same way). Repeat after a full re-export if you discard the `.docx`.
4. Open `dist/SmartGlasses_Defense.pptx` in **LibreOffice Impress** for final slide polish.

### LibreOffice CLI (`soffice`) and PDFs

`export.ps1` looks for LibreOffice in this order:

1. `soffice` or `soffice.com` on your **PATH**
2. `%ProgramFiles%\LibreOffice\program\soffice.com`
3. `%ProgramFiles(x86)%\LibreOffice\program\soffice.com`

It runs **headless** conversion with a **separate user profile** (`%TEMP%\lo_profile_sgd_export`) so PDF export does not fight a Writer/Impress GUI session that is already open.

To add LibreOffice to PATH (optional): add `C:\Program Files\LibreOffice\program` to the user **Path** environment variable, then reopen the terminal.

## Prerequisites

- [Pandoc](https://pandoc.org/installing.html) 3.x on PATH. On Windows: `winget install --id JohnMacFarlane.Pandoc -e`
- [LibreOffice](https://www.libreoffice.org/download/download/) (Writer + Impress) so `soffice.com` exists for **PDF** output. Editing `.docx` / `.pptx` only needs the GUI install; PDF batch uses the same install.

## Regenerate long report body (optional)

The graduation manual body is generated for length and structure consistency:

```powershell
python docs/16_submission_package/build/generate_expanded_docs.py
```

Then export. Current generator output is on the order of **40k+ words** (~130+ single-spaced equivalent pages at ~300 words/page before styles and figures — adjust by removing `16_supplementary_engineering_topics.md` from `export.ps1` if the advisor wants a thinner bound volume).

## Direct `.docx` editing (python-docx)

Install once in your venv:

```powershell
pip install -r docs/16_submission_package/build/requirements-docx.txt
```

CLI: [build/docx_tool.py](build/docx_tool.py)

| Command | Purpose |
|---------|---------|
| `python build/docx_tool.py inspect <file.docx>` | Paragraph counts + first lines (ASCII-safe on Windows consoles) |
| `python build/docx_tool.py replace <src> <dst> "OLD" "NEW"` | Copy and global text replace in paragraphs, tables, headers, footers |
| `python build/docx_tool.py fill-template <template.docx> <metadata.yaml> <out.docx>` | Copy faculty template; fill title + team (3rd member inserted after row 2); advisor placeholder |
| `python build/docx_tool.py set-core-props <file.docx> <metadata.yaml>` | Set document **Title / Author / Comments** from YAML (in-place) |

`build/export.ps1` runs **`set-core-props`** on the Pandoc-produced manual and paper, and **`fill-template`** into `dist/Faculty_Template_Filled.docx` when the template path exists and `python-docx` is installed.

**Alternatives (not bundled):** [docxtpl](https://docxtpl.readthedocs.io/) if you refactor the template to Jinja2 tags; **pywin32** COM only if you must drive Microsoft Word on Windows.

## Build (Windows)

From repository root:

```powershell
powershell -ExecutionPolicy Bypass -File docs/16_submission_package/build/export.ps1
```

**Outputs** under `docs/16_submission_package/dist/` (gitignored):

| File | Role |
|------|------|
| `SmartGlasses_ProjectManual.docx` / `.pdf` | Full merged report (+ TOC in docx) |
| `SmartGlasses_ResearchPaper.docx` / `.pdf` | Short paper |
| `SmartGlasses_Defense.pptx` / `.pdf` | Slides |
| `Faculty_Template_Filled.docx` / `.pdf` | Faculty template with cover fields from `metadata.yaml` (if template + python-docx available) |

### Verify code paths in Markdown

```powershell
powershell -ExecutionPolicy Bypass -File docs/16_submission_package/build/verify-paths.ps1
```

## Metadata

Author list and title: [metadata.yaml](metadata.yaml) (used by Pandoc and `docx_tool.py`).
