param(
    [switch]$Sample,          
    [switch]$SkipTrain,       
    [int]$MaxUsers = 20000    
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root
$jdkCandidates = @(
    "C:\Program Files\Eclipse Adoptium\jdk-8.0.482.8-hotspot",
    "C:\Program Files\Eclipse Adoptium\jdk-17*",
    "C:\Program Files\Eclipse Adoptium\jdk-11*"
)
foreach ($c in $jdkCandidates) {
    $found = Get-Item $c -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) { $env:JAVA_HOME = $found.FullName; break }
}
Write-Host "JAVA_HOME = $env:JAVA_HOME" -ForegroundColor Cyan

$py = (Get-Command python).Source
$env:PYSPARK_PYTHON = $py
$env:PYSPARK_DRIVER_PYTHON = $py
$env:PYTHONUTF8 = "1"
$db = "$Root\serving\recsys.db"
$env:SQLITE_PATH = $db
$env:MOVIES_PATH = "./data/ml-25m/movies.csv"
$env:MYSQL_URL = ""
$env:ALS_RANK = "64"; $env:ALS_MAX_ITER = "10"; $env:ALS_TOP_N = "20"
$env:ALS_MAX_USERS = "$MaxUsers"; $env:SPARK_DRIVER_MEM = "6g"

if ($Sample) {
    if (-not (Test-Path "$Root\data\ratings_sample.csv")) {
        Get-Content "$Root\data\ml-25m\ratings.csv" -TotalCount 300001 |
            Set-Content "$Root\data\ratings_sample.csv" -Encoding utf8
    }
    $env:RATINGS_PATH = "./data/ratings_sample.csv"
    $env:POPULAR_MIN_RATINGS = "50"; $env:ALS_MAX_USERS = "300"
} else {
    $env:RATINGS_PATH = "./data/ml-25m/ratings.csv"
    $env:POPULAR_MIN_RATINGS = "1000"
}

if (-not $SkipTrain) {
    Write-Host "`n[1/3] Huan luyen ALS..." -ForegroundColor Green
    & $py batch\train_als.py
    if ($LASTEXITCODE -ne 0) { throw "Train ALS that bai" }

    Write-Host "`n[2/3] Dung user_history..." -ForegroundColor Green
    $env:DB_URL = "sqlite:///serving/recsys.db"
    & $py scripts\build_user_history.py
}

Write-Host "`n[3/3] Khoi dong Flask demo: http://localhost:5000" -ForegroundColor Green
Set-Location "$Root\serving"
$env:DB_URL = "sqlite:///./recsys.db"
& $py app.py
