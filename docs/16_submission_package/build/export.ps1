$ErrorActionPreference = "Stop"
$PackageRoot = Split-Path -Parent $PSScriptRoot
$RepoRoot = (Resolve-Path (Join-Path $PackageRoot "..\..")).Path
$DistDir = Join-Path $PackageRoot "dist"

if (-not (Get-Command pandoc -ErrorAction SilentlyContinue)) {
    Write-Error "Pandoc not found on PATH. Install from https://pandoc.org/installing.html"
}

New-Item -ItemType Directory -Force -Path $DistDir | Out-Null

$Meta = Join-Path $PackageRoot "metadata.yaml"
$RefDoc = Join-Path $RepoRoot "docs\00_Materials\Graudation-project-template.docx"
$useRefDoc = Test-Path -LiteralPath $RefDoc
if ($useRefDoc) {
    Write-Host "Using OOXML reference document (faculty template): $RefDoc"
}
else {
    Write-Warning "Graduation template not found at $RefDoc - export will use Pandoc defaults. Copy the template to that path or update export.ps1."
}

# Chapter order follows Faculty graduation project template (see GRADUATION_TEMPLATE_MAPPING.md)
$ManualParts = @(
    "00_cover_title_page.md",
    "01_abstract_acknowledgements.md",
    "02_chapter1_introduction.md",
    "03_chapter2_related_work_part1.md",
    "04_chapter2_related_work_part2.md",
    "05_chapter2_related_work_part3.md",
    "06_chapter2_related_work_part4.md",
    "07_chapter3_methodology_requirements_design.md",
    "08_chapter3_system_architecture.md",
    "09_chapter3_implementation_gateway.md",
    "10_chapter3_implementation_services.md",
    "11_chapter3_clients_firmware_testing.md",
    "12_chapter4_experimental_results.md",
    "13_chapter5_discussion.md",
    "14_chapter6_conclusions.md",
    "15_references.md",
    "16_supplementary_engineering_topics.md",
    "appendices\A_api_routes_from_code.md",
    "appendices\B_testing_matrix.md",
    "appendices\C_settings_environment.md",
    "appendices\D_hardware_integration.md",
    "appendices\E_media_catalog.md"
) | ForEach-Object { Join-Path $PackageRoot "full_documentation\$_" }

foreach ($p in $ManualParts) {
    if (-not (Test-Path -LiteralPath $p)) {
        Write-Error "Missing manual part: $p"
    }
}

$Slides = Join-Path $PackageRoot "presentation\slides.md"
$Paper = Join-Path $PackageRoot "research_paper\paper.md"
$Bib = Join-Path $PackageRoot "research_paper\references.bib"
$outManual = Join-Path $DistDir "SmartGlasses_ProjectManual.docx"
$outPaper = Join-Path $DistDir "SmartGlasses_ResearchPaper.docx"
$outSlides = Join-Path $DistDir "SmartGlasses_Defense.pptx"
$filledTpl = Join-Path $DistDir "Faculty_Template_Filled.docx"

Write-Host "Exporting manual -> SmartGlasses_ProjectManual.docx (with TOC field for LibreOffice)"
if ($useRefDoc) {
    & pandoc @ManualParts --metadata-file=$Meta "--reference-doc=$RefDoc" --toc --toc-depth=3 -o $outManual
}
else {
    & pandoc @ManualParts --metadata-file=$Meta --toc --toc-depth=3 -o $outManual
}

Write-Host "Exporting paper -> SmartGlasses_ResearchPaper.docx"
if ($useRefDoc) {
    & pandoc $Paper --metadata-file=$Meta "--reference-doc=$RefDoc" --bibliography=$Bib --citeproc -o $outPaper
}
else {
    & pandoc $Paper --metadata-file=$Meta --bibliography=$Bib --citeproc -o $outPaper
}

Write-Host "Exporting slides -> SmartGlasses_Defense.pptx"
& pandoc $Slides --metadata-file=$Meta -o $outSlides

$DocxTool = Join-Path $PackageRoot "build\docx_tool.py"
# Python writes ImportError tracebacks to stderr; with $ErrorActionPreference = Stop that would abort the script.
$oldEaCheck = $ErrorActionPreference
$ErrorActionPreference = "SilentlyContinue"
python -c "import docx, yaml" 2>&1 | Out-Null
$pyOk = ($LASTEXITCODE -eq 0)
$ErrorActionPreference = $oldEaCheck

if ($pyOk) {
    Write-Host "Patching .docx with python-docx (core properties + filled faculty template copy)"
    python $DocxTool set-core-props $outManual $Meta
    python $DocxTool set-core-props $outPaper $Meta
    if ($useRefDoc) {
        python $DocxTool fill-template $RefDoc $Meta $filledTpl
    }
}
else {
    Write-Warning "python-docx / PyYAML not installed. Skipping docx_tool.py steps. Run: pip install -r build/requirements-docx.txt"
}

# --- LibreOffice headless: .docx / .pptx -> PDF (no Microsoft Word required) ---
$soffice = $null
$cmdSoffice = Get-Command soffice -ErrorAction SilentlyContinue
if ($cmdSoffice) {
    $soffice = $cmdSoffice.Source
}
if (-not $soffice) {
    $cmdSofficeCom = Get-Command soffice.com -ErrorAction SilentlyContinue
    if ($cmdSofficeCom) {
        $soffice = $cmdSofficeCom.Source
    }
}
if (-not $soffice) {
    foreach ($candidate in @(
            "$env:ProgramFiles\LibreOffice\program\soffice.com",
            "${env:ProgramFiles(x86)}\LibreOffice\program\soffice.com")) {
        if (Test-Path -LiteralPath $candidate) {
            $soffice = $candidate
            break
        }
    }
}

if ($soffice) {
    Write-Host "LibreOffice PDF export using: $soffice"
    $loProfileDir = Join-Path $env:TEMP "lo_profile_sgd_export"
    New-Item -ItemType Directory -Force -Path $loProfileDir | Out-Null
    $loProfileUrl = "file:///" + (($loProfileDir -replace '\\', '/') -replace ' ', '%20')
    $userInstArg = "-env:UserInstallation=$loProfileUrl"

    $pdfInputs = @($outManual, $outPaper, $outSlides)
    if ($pyOk -and $useRefDoc -and (Test-Path -LiteralPath $filledTpl)) {
        $pdfInputs += $filledTpl
    }

    $oldEa = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        foreach ($f in $pdfInputs) {
            if (-not (Test-Path -LiteralPath $f)) {
                continue
            }
            Write-Host "  -> PDF: $(Split-Path -Leaf $f)"
            & $soffice $userInstArg --headless --norestore --nologo --convert-to pdf --outdir $DistDir $f 2>&1 | Out-Null
            if ($LASTEXITCODE -ne 0) {
                Write-Warning "soffice exit code $LASTEXITCODE for $f"
            }
        }
    }
    finally {
        $ErrorActionPreference = $oldEa
    }
}
else {
    Write-Warning "LibreOffice (soffice) not found on PATH or in Program Files - skipping PDF export. Install LibreOffice or add soffice to PATH."
}

Write-Host ('Done. Outputs in ' + $DistDir)
