# Remove note-to-note links in pre/post sections
# Convert [[XX_title]] to plain text

$notesPath = ".\笔记"
$processed = 0
$modified = 0

Get-ChildItem -Path $notesPath -Filter "*.md" -Recurse | ForEach-Object {
    $file = $_
    $content = Get-Content -Path $file.FullName -Raw -Encoding UTF8
    $fileChanged = $false

    # Pattern 1: [[digits_title]] -- description
    # e.g. [[01_计算机系统概述]] -- description
    $content = $content -replace '\[\[(\d+[-_])([^\]]+)\]\] -- ', '$2 -- '
    if ($content -ne (Get-Content -Path $file.FullName -Raw -Encoding UTF8)) {
        $fileChanged = $true
    }

    # Pattern 2: [[title]] -- description (in pre/post sections)
    # e.g. [[三极管]] -- description
    # Only apply to lines that look like note links
    $content = $content -replace '(### (?:前置依赖|后续应用|对比辨析)[^\n]*\n(?:[ \t]*[-*][ \t]*))\[\[([^\]]+)\]\] -- ', '$1$2 -- '

    if ($fileChanged -or $content -ne (Get-Content -Path $file.FullName -Raw -Encoding UTF8)) {
        Set-Content -Path $file.FullName -Value $content -Encoding UTF8 -NoNewline
        $modified++
        Write-Host "Modified: $($file.Name)" -ForegroundColor Green
    }

    $processed++
}

Write-Host ""
Write-Host "Done! Scanned $processed files, modified $modified files" -ForegroundColor Cyan
