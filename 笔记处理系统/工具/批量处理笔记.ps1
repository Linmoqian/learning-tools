# Batch process note files
# 1. Remove note-to-note links in pre/post sections
# 2. Add wiki links to Core Entry Index

$notesPath = ".\笔记"
$processed = 0
$modified = 0

Get-ChildItem -Path $notesPath -Filter "*.md" -Recurse | ForEach-Object {
    $file = $_
    $content = Get-Content -Path $file.FullName -Raw -Encoding UTF8
    $fileChanged = $false

    # 1. Remove note links in pre/post sections
    $sections = @("前置依赖", "后续应用", "对比辨析")
    foreach ($section in $sections) {
        # Pattern: [[digits_title]]
        $pattern = "(### $section`r?`n)((?:[ ]*[-*][ ]*))\[\[(\d+[-_][^\]]+)\]\]( -- [^\r`n]+?)(?=`r?`n[ ]*[-*]|`r?`n[ ]*###|`r?`n##|`r?`n---)"
        if ($content -match $pattern) {
            $content = $content -replace $pattern, '$2$3$4'
            $fileChanged = $true
        }

        # Pattern: [[title]]
        $pattern2 = "(### $section`r?`n)((?:[ ]*[-*][ ]*))\[\[([^\]]+)\]\]( -- [^\r`n]+?)(?=`r?`n[ ]*[-*]|`r?`n[ ]*###|`r?`n##|`r?`n---)"
        if ($content -match $pattern2) {
            $content = $content -replace $pattern2, '$2$3$4'
            $fileChanged = $true
        }
    }

    # 2. Add wiki links to Core Entry Index table
    if ($content -match "(## (?:📚 )?核心词条索引`r?`n\|[^|]+|[^|]+|[^|]+`r?`n\|[-|: ]+|[^|]+|[^|]+`r?`n)((?:\|[^\r`n]+`r?`n)+)") {
        $tableRows = $matches[2]
        $newTableRows = ""

        $tableRows -split "`n" | ForEach-Object {
            $row = $_
            if ($row -match '^\|([^|]+)\|([^|]+)\|([^|]+)\|$') {
                $entry = $matches[1].Trim()
                $category = $matches[2].Trim()
                $keywords = $matches[3].Trim()

                if ($entry -notmatch '^\[\[') {
                    $entry = "[[$entry]]"
                }

                $newTableRows += "| $entry | $category | $keywords |`n"
            } else {
                $newTableRows += "$row`n"
            }
        }

        $content = $content -replace [regex]::Escape($matches[0]), $matches[1] + $newTableRows
        $fileChanged = $true
    }

    if ($fileChanged) {
        Set-Content -Path $file.FullName -Value $content -Encoding UTF8 -NoNewline
        $modified++
        Write-Host "Modified: $($file.Name)" -ForegroundColor Green
    }

    $processed++
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Done! Scanned $processed files, modified $modified files" -ForegroundColor Cyan
