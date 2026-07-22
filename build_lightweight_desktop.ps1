param(
    [string]$OutputName = "leakage_simulator_desktop_v0.9.11_lite"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ReleaseRoot = Join-Path $Root "release"
$OutputDir = Join-Path $ReleaseRoot $OutputName
$ZipPath = "$OutputDir.zip"
$SourcePython = Join-Path $Root "_tools\python313"
$SourceSitePackages = Join-Path $SourcePython "Lib\site-packages"
$TargetPython = Join-Path $OutputDir "_tools\python313"
$TargetSitePackages = Join-Path $TargetPython "Lib\site-packages"
$LauncherSource = Join-Path $Root "desktop_launcher\LeakageSimulatorDesktop.cs"
$Compiler = Join-Path $env:WINDIR "Microsoft.NET\Framework64\v4.0.30319\csc.exe"

function Get-DirectorySizeMB([string]$Path) {
    $sum = (Get-ChildItem -LiteralPath $Path -Recurse -File | Measure-Object Length -Sum).Sum
    return [math]::Round($sum / 1MB, 1)
}

function Copy-RequiredPath([string]$Source, [string]$Destination) {
    if (-not (Test-Path -LiteralPath $Source)) {
        throw "Required runtime path is missing: $Source"
    }
    Copy-Item -LiteralPath $Source -Destination $Destination -Recurse -Force
}

function Test-PackagedWebServer([string]$PythonExe, [string]$AppRoot) {
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
    $listener.Start()
    $port = ([System.Net.IPEndPoint]$listener.LocalEndpoint).Port
    $listener.Stop()

    $process = $null
    try {
        $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
        $startInfo.FileName = $PythonExe
        $startInfo.Arguments = '-u "{0}" --port {1} --strict-port' -f (Join-Path $AppRoot "run_web.py"), $port
        $startInfo.WorkingDirectory = $AppRoot
        $startInfo.UseShellExecute = $false
        $startInfo.CreateNoWindow = $true
        $startInfo.RedirectStandardOutput = $true
        $startInfo.RedirectStandardError = $true
        $process = [System.Diagnostics.Process]::Start($startInfo)

        $deadline = [DateTime]::UtcNow.AddSeconds(90)
        $healthy = $false
        while ([DateTime]::UtcNow -lt $deadline -and -not $process.HasExited) {
            try {
                $health = Invoke-RestMethod -Uri "http://127.0.0.1:$port/health" -TimeoutSec 2
                if ($health -match "ok web_ui_version=0.9.11") {
                    $healthy = $true
                    break
                }
            }
            catch {
            }
            Start-Sleep -Milliseconds 300
        }
        if (-not $healthy) {
            if (-not $process.HasExited) {
                $process.Kill()
                $process.WaitForExit()
            }
            $stdout = $process.StandardOutput.ReadToEnd()
            $stderr = $process.StandardError.ReadToEnd()
            throw "Packaged web server health validation failed.`nSTDOUT:`n$stdout`nSTDERR:`n$stderr"
        }
    }
    finally {
        if ($process -and -not $process.HasExited) {
            $process.Kill()
            $process.WaitForExit()
        }
    }
}

if (-not (Test-Path -LiteralPath $SourcePython)) {
    throw "Source embedded Python was not found: $SourcePython"
}
if (-not (Test-Path -LiteralPath $Compiler)) {
    throw "C# compiler was not found: $Compiler"
}

$resolvedRelease = [System.IO.Path]::GetFullPath($ReleaseRoot)
$resolvedOutput = [System.IO.Path]::GetFullPath($OutputDir)
if (-not $resolvedOutput.StartsWith($resolvedRelease, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Output path must remain inside the release folder."
}

if (Test-Path -LiteralPath $OutputDir) {
    Remove-Item -LiteralPath $OutputDir -Recurse -Force
}
if (Test-Path -LiteralPath $ZipPath) {
    Remove-Item -LiteralPath $ZipPath -Force
}

New-Item -ItemType Directory -Path $TargetSitePackages -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $OutputDir "outputs") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $OutputDir "_uploads") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $OutputDir "desktop_runtime") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $OutputDir "docs") -Force | Out-Null

Write-Host "[1/8] Copying minimal Python runtime..."
Get-ChildItem -LiteralPath $SourcePython -File | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $TargetPython -Force
}

Write-Host "[2/8] Copying STEP and ray tracing dependencies..."
$RuntimePackages = @(
    "OCP",
    "cadquery_ocp",
    "cadquery_ocp-7.9.3.1.1.dist-info",
    "cadquery_ocp_proxy",
    "cadquery_ocp_proxy-7.9.3.1.1.dist-info",
    "numpy",
    "numpy-2.4.6.dist-info",
    "numpy.libs"
)
foreach ($package in $RuntimePackages) {
    Copy-RequiredPath (Join-Path $SourceSitePackages $package) $TargetSitePackages
}
$DependencyScript = Join-Path $Root "scripts\copy_pe_dependency_closure.py"
$DependencyManifest = Join-Path $OutputDir "runtime_dependency_manifest.json"
& (Join-Path $SourcePython "python.exe") $DependencyScript `
    --seed (Join-Path $SourceSitePackages "OCP\OCP.cp313-win_amd64.pyd") `
    --source-dir (Join-Path $SourceSitePackages "cadquery_ocp.libs") `
    --source-dir (Join-Path $SourceSitePackages "vtk.libs") `
    --target-root $TargetSitePackages `
    --manifest $DependencyManifest
if ($LASTEXITCODE -ne 0) {
    throw "OCP dependency closure copy failed."
}

Write-Host "[3/8] Copying simulator application files..."
Copy-RequiredPath (Join-Path $Root "src") $OutputDir
Copy-RequiredPath (Join-Path $Root "web") $OutputDir
Copy-RequiredPath (Join-Path $Root "samples") $OutputDir
Copy-Item -LiteralPath (Join-Path $Root "run_web.py") -Destination $OutputDir -Force
Copy-Item -LiteralPath (Join-Path $Root "check_cad_import.py") -Destination $OutputDir -Force
Copy-Item -LiteralPath (Join-Path $Root "README.md") -Destination $OutputDir -Force
Copy-Item -LiteralPath (Join-Path $Root "COMPANY_PC_QUICK_START.md") -Destination $OutputDir -Force
Copy-Item -LiteralPath (Join-Path $Root "requirements-dev.txt") -Destination $OutputDir -Force
Copy-Item -LiteralPath (Join-Path $Root "docs\cad-intersection-backend-contract.md") -Destination (Join-Path $OutputDir "docs") -Force
Copy-Item -LiteralPath (Join-Path $Root "docs\performance-acceleration-plan.md") -Destination (Join-Path $OutputDir "docs") -Force
Copy-Item -LiteralPath (Join-Path $Root "docs\desktop-exe-packaging.md") -Destination (Join-Path $OutputDir "docs") -Force

$WebViewCandidates = @(
    (Join-Path $Root "release\leakage_simulator_desktop_v0.1"),
    "C:\Program Files\Microsoft Office\root\Office16\ADDINS\Microsoft Power Query for Excel Integrated\bin"
)
$WebViewSource = $null
foreach ($candidate in $WebViewCandidates) {
    if (
        (Test-Path -LiteralPath (Join-Path $candidate "Microsoft.Web.WebView2.Core.dll")) -and
        (Test-Path -LiteralPath (Join-Path $candidate "Microsoft.Web.WebView2.WinForms.dll"))
    ) {
        $WebViewSource = $candidate
        break
    }
}
if (-not $WebViewSource) {
    throw "WebView2 managed DLLs were not found."
}

Write-Host "[4/8] Building desktop launcher..."
$WebViewCore = Join-Path $WebViewSource "Microsoft.Web.WebView2.Core.dll"
$WebViewWinForms = Join-Path $WebViewSource "Microsoft.Web.WebView2.WinForms.dll"
$WebViewLoaderCandidates = @(
    (Join-Path $WebViewSource "WebView2Loader.dll"),
    "C:\Program Files\Microsoft Office\root\Office16\ADDINS\Microsoft Power Query for Excel Integrated\bin\WebView2Loader.dll"
)
$WebViewLoader = $WebViewLoaderCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $WebViewLoader) {
    throw "WebView2Loader.dll was not found."
}
$LauncherExe = Join-Path $OutputDir "LeakageSimulator.exe"
& $Compiler /nologo /target:winexe /platform:x64 /optimize+ /out:$LauncherExe `
    /r:System.dll `
    /r:System.Core.dll `
    /r:System.Drawing.dll `
    /r:System.Windows.Forms.dll `
    /r:$WebViewCore `
    /r:$WebViewWinForms `
    $LauncherSource
if ($LASTEXITCODE -ne 0) {
    throw "Desktop launcher compilation failed."
}
Copy-Item -LiteralPath $WebViewCore -Destination $OutputDir -Force
Copy-Item -LiteralPath $WebViewWinForms -Destination $OutputDir -Force
Copy-Item -LiteralPath $WebViewLoader -Destination $OutputDir -Force

@"
TV Leakage Simulator Desktop Lite v0.9.11

1. Double-click LeakageSimulator.exe.
2. Wait until the simulator window opens.
3. Import STEP/STP CAD from Model Import.
4. Emitter, Receiver, optical property, RT-2C reflection, PERF-1 and PERF-2 BVH are included.

Important:
- Keep all files and folders together.
- X_T direct import is not implemented in this lite build.
- If embedded WebView2 is unavailable, the launcher opens the local UI in the default browser.
"@ | Set-Content -LiteralPath (Join-Path $OutputDir "START_HERE.txt") -Encoding utf8

Write-Host "[5/8] Validating minimal runtime and STEP import..."
$TargetPythonExe = Join-Path $TargetPython "python.exe"
& $TargetPythonExe -c "import OCP, numpy; print('runtime ok', numpy.__version__)"
if ($LASTEXITCODE -ne 0) {
    throw "Minimal Python runtime import validation failed."
}
& $TargetPythonExe (Join-Path $OutputDir "check_cad_import.py") `
    --cad (Join-Path $OutputDir "samples\tv_leakage_full_assembled_no_gap.stp") `
    --output-dir (Join-Path $OutputDir "outputs") `
    --no-dialog
if ($LASTEXITCODE -ne 0) {
    throw "STEP import validation failed."
}
& $TargetPythonExe -m unittest discover -s (Join-Path $Root "tests") -p "test_*.py"
if ($LASTEXITCODE -ne 0) {
    throw "Ray tracing regression tests failed with the minimal runtime."
}

Write-Host "[6/8] Cleaning generated cache files..."
Get-ChildItem -LiteralPath $OutputDir -Recurse -Directory -Filter "__pycache__" | ForEach-Object {
    Remove-Item -LiteralPath $_.FullName -Recurse -Force
}
Get-ChildItem -LiteralPath (Join-Path $OutputDir "outputs") -File -ErrorAction SilentlyContinue | Remove-Item -Force

Write-Host "[7/8] Creating ZIP package..."
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory(
    $OutputDir,
    $ZipPath,
    [System.IO.Compression.CompressionLevel]::Optimal,
    $true
)
$archive = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)
try {
    if ($archive.Entries.Count -lt 10) {
        throw "ZIP validation failed: too few entries."
    }
    $requiredEntries = @(
        "$OutputName/LeakageSimulator.exe",
        "$OutputName/run_web.py",
        "$OutputName/_tools/python313/python.exe",
        "$OutputName/_tools/python313/Lib/site-packages/OCP/__init__.py",
        "$OutputName/WebView2Loader.dll"
    )
    $entryNames = @($archive.Entries | ForEach-Object { $_.FullName.Replace("\", "/") })
    foreach ($entry in $requiredEntries) {
        if ($entryNames -notcontains $entry) {
            throw "ZIP validation failed: missing $entry"
        }
    }
}
finally {
    $archive.Dispose()
}

Write-Host "[8/8] Extracting ZIP and validating STEP import again..."
$VerifyDir = Join-Path $ReleaseRoot ("_verify_" + $OutputName)
$resolvedVerify = [System.IO.Path]::GetFullPath($VerifyDir)
if (-not $resolvedVerify.StartsWith($resolvedRelease, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Verification path must remain inside the release folder."
}
if (Test-Path -LiteralPath $VerifyDir) {
    Remove-Item -LiteralPath $VerifyDir -Recurse -Force
}
New-Item -ItemType Directory -Path $VerifyDir -Force | Out-Null
try {
    [System.IO.Compression.ZipFile]::ExtractToDirectory($ZipPath, $VerifyDir)
    $ExtractedRoot = Join-Path $VerifyDir $OutputName
    $ExtractedPython = Join-Path $ExtractedRoot "_tools\python313\python.exe"
    & $ExtractedPython -c "import OCP, numpy; print('extracted runtime ok', numpy.__version__)"
    if ($LASTEXITCODE -ne 0) {
        throw "Extracted ZIP runtime validation failed."
    }
    & $ExtractedPython (Join-Path $ExtractedRoot "check_cad_import.py") `
        --cad (Join-Path $ExtractedRoot "samples\tv_leakage_full_assembled_no_gap.stp") `
        --output-dir (Join-Path $ExtractedRoot "outputs") `
        --no-dialog
    if ($LASTEXITCODE -ne 0) {
        throw "Extracted ZIP STEP import validation failed."
    }
    Test-PackagedWebServer $ExtractedPython $ExtractedRoot
}
finally {
    if (Test-Path -LiteralPath $VerifyDir) {
        Remove-Item -LiteralPath $VerifyDir -Recurse -Force
    }
}

$Hash = (Get-FileHash -LiteralPath $ZipPath -Algorithm SHA256).Hash.ToLowerInvariant()
$HashPath = "$ZipPath.sha256"
"$Hash  $([System.IO.Path]::GetFileName($ZipPath))" | Set-Content -LiteralPath $HashPath -Encoding ascii

$FolderMB = Get-DirectorySizeMB $OutputDir
$ZipMB = [math]::Round((Get-Item -LiteralPath $ZipPath).Length / 1MB, 1)
Write-Host "Lightweight desktop package completed."
Write-Host "Folder: $OutputDir ($FolderMB MB)"
Write-Host "ZIP:    $ZipPath ($ZipMB MB)"
Write-Host "SHA256: $HashPath"
