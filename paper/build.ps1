param([switch]$RefreshAssets, [switch]$UpdatePdf)
$ErrorActionPreference = 'Stop'
Push-Location -LiteralPath $PSScriptRoot
try {
    $buildArgs = @()
    if ($RefreshAssets) { $buildArgs += '--refresh-assets' }
    if ($UpdatePdf) { $buildArgs += '--update-pdf' }
    python -X utf8 build_paper.py @buildArgs
    if ($LASTEXITCODE -ne 0) { throw 'Paper build or verification failed.' }
}
finally { Pop-Location }
