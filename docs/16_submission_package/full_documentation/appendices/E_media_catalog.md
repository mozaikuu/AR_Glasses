# Appendix E — Figure and media catalog

The project asset library is `docs/00_Materials/`. As of the documentation freeze date for this export, the folder contains **213** files (photos, videos, documents, and other capture formats).

## Conventions for the bound report

1. **Prefer PNG or JPEG** for figures embedded in Word; convert HEIC/MOV sources externally.
2. **Number figures** consistently (Figure 4.x for results chapter, etc.) per faculty template.
3. **One-line caption** per figure: what the reader should conclude (not only “screenshot”).

## Suggested figure set (edit filenames to match your picks)

| ID | Suggested source type | Chapter |
|----|------------------------|---------|
| Fig. 1 | Team photo / hardware on bench | Introduction |
| Fig. 2 | `GET /` health JSON in browser | Methodology / Results |
| Fig. 3 | Expo navigation or GLB viewer screen | Methodology |
| Fig. 4 | Android client assistant screen | Methodology |
| Fig. 5 | ESP32 serial log showing HTTP success | Hardware appendix |
| Fig. 6 | QR demo marker in environment | Methodology |

## Video supplements

Short MP4/MOV clips in `docs/00_Materials/` may be referenced on a USB appendix or online gallery link approved by the advisor. Note: Pandoc does not embed video inside `.docx`; insert via Word.

## Automated listing (optional)

For an exhaustive file list, run from repository root:

`Get-ChildItem docs/00_Materials -File | Sort-Object Name | Export-Csv docs/16_submission_package/assets/media_index.csv`

Then import the CSV into Word as an auxiliary table if the committee requests full inventory.
