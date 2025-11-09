Param(
    [string]$Root = "S:\\YDS-Lab\\01-struc"
)

$ErrorActionPreference = 'Stop'
Write-Host "开始生成部门文档索引..."

# 定义标准分类目录
$categories = @('规章制度','流程与SOP','模板','会议纪要','项目资料')

$deptDirs = Get-ChildItem -Directory -Path $Root | Where-Object { Test-Path (Join-Path $_.FullName 'docs') }
$timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

foreach($dept in $deptDirs){
    $docsPath = Join-Path $dept.FullName 'docs'
    $indexPath = Join-Path $docsPath 'INDEX.md'

    $lines = @()
    $lines += "# 部门文档自动索引"
    $lines += ""
    $lines += "- 部门目录: $($dept.Name)"
    $lines += "- 生成时间: $timestamp"
    $lines += "- 根路径: $docsPath"
    $lines += ""

    foreach($cat in $categories){
        $catPath = Join-Path $docsPath $cat
        if(Test-Path $catPath){
            $lines += "## $cat"
            $files = Get-ChildItem -Path $catPath -Recurse -File -ErrorAction SilentlyContinue -Include *.md,*.docx,*.xlsx,*.pptx,*.pdf,*.txt
            if($files.Count -eq 0){
                $lines += "- （暂无文件）"
            } else {
                foreach($f in $files){
                    $rel = $f.FullName.Substring($docsPath.Length).TrimStart('\\','/')
                    $rel = $rel -replace '\\','/'
                    $name = $f.Name
                    $lines += "- [$name]($rel)"
                }
            }
            $lines += ""
        } else {
            # 若分类目录不存在则创建，并在索引中标记
            New-Item -ItemType Directory -Path $catPath -ErrorAction SilentlyContinue | Out-Null
            $lines += "## $cat"
            $lines += "- （目录新建，暂无文件）"
            $lines += ""
        }
    }

    # 索引末尾标识（已移除中文行，避免编码问题）

    $lines | Out-File -FilePath $indexPath -Encoding utf8
    Write-Host "已生成: $indexPath"
}

Write-Host "部门文档索引生成完成，共处理 $($deptDirs.Count) 个部门。"