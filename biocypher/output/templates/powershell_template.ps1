$banner = @"
# ============================================================================== #
# ========                   Import Script for Powershell               ======== #
# ============================================================================== #
"@
Write-Host $banner -ForegroundColor Cyan
Write-Host "[$(Get-Date -Format 'u')] Starting Neo4j import process..." -ForegroundColor Cyan

# ================================ #
#      Neo4j Binary Settings       #
# ================================ #
{neo4j_bin_path}
Write-Host "[$(Get-Date -Format 'u')] Neo4j bin path set to: $NEO4J_BIN_PATH_WINDOWS"

{neo4j_version_check}
Write-Host "[$(Get-Date -Format 'u')] Detected Neo4j version: $version"

$major_version = $version.Trim().Split('.')[0]
$major = [int]$major_version


# ================================ #
#    Neo4j import arguments        #
# ================================ #

if ( $major -lt 5 )
{{
    $args_neo4j=@(
@'
{args_neo4j_v4}
'@
)
    Write-Host "[$(Get-Date -Format 'u')] Detected Neo4j v4 - using legacy import command." -ForegroundColor Yellow
    Write-Host "[$(Get-Date -Format 'u')] Args for Neo4j v4:"
    $args_neo4j -split ' ' | ForEach-Object {{ Write-Host "`t$_" }}
}}
else
{{
    $args_neo4j = @(
@'
{args_neo4j_v5}
'@
)
    Write-Host "[$(Get-Date -Format 'u')] Detected Neo4j v5 or newer - using modern import command." -ForegroundColor Yellow
    Write-Host "[$(Get-Date -Format 'u')] Args for Neo4j >= v5:"
    $args_neo4j -split ' ' | ForEach-Object {{ Write-Host "`t$_" }}
}}

# ================================ #
#    Neo4j-admin import call       #
# ================================ #
Write-Host "[$(Get-Date -Format 'u')] Running import command..." -ForegroundColor Cyan

Invoke-Expression "$NEO4J_BIN_PATH_WINDOWS $args_neo4j"
if ($LASTEXITCODE -eq 0) {{
    Write-Host "[$(Get-Date -Format 'u')] Import completed successfully!" -ForegroundColor Green
}} else {{
    Write-Host "[$(Get-Date -Format 'u')] Import failed with exit code $LASTEXITCODE." -ForegroundColor Red
}}
Write-Host "[$(Get-Date -Format 'u')] Script finished." -ForegroundColor Cyan
