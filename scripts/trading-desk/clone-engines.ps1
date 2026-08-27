[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'Medium')]
param(
    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$TargetRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-CanonicalPath {
    param(
        [Parameter(Mandatory)]
        [string]$Path
    )

    $currentPath = [System.IO.Path]::GetFullPath($Path)
    $missingSegments = [System.Collections.Generic.Stack[string]]::new()

    while (-not (Test-Path -LiteralPath $currentPath)) {
        $leaf = [System.IO.Path]::GetFileName($currentPath)
        $parent = [System.IO.Path]::GetDirectoryName($currentPath)
        if ([string]::IsNullOrWhiteSpace($leaf) -or [string]::IsNullOrWhiteSpace($parent)) {
            throw "Cannot resolve path '$Path' from an existing parent."
        }

        $missingSegments.Push($leaf)
        $currentPath = $parent
    }

    $resolvedPath = (Resolve-Path -LiteralPath $currentPath).ProviderPath
    while ($missingSegments.Count -gt 0) {
        $resolvedPath = Join-Path -Path $resolvedPath -ChildPath $missingSegments.Pop()
    }

    return [System.IO.Path]::GetFullPath($resolvedPath)
}

function Test-PathWithin {
    param(
        [Parameter(Mandatory)]
        [string]$Candidate,

        [Parameter(Mandatory)]
        [string]$Parent
    )

    $comparison = [System.StringComparison]::OrdinalIgnoreCase
    $trimmedParent = $Parent.TrimEnd(
        [System.IO.Path]::DirectorySeparatorChar,
        [System.IO.Path]::AltDirectorySeparatorChar
    )
    $parentPrefix = $trimmedParent + [System.IO.Path]::DirectorySeparatorChar

    return $Candidate.Equals($trimmedParent, $comparison) -or
        $Candidate.StartsWith($parentPrefix, $comparison)
}

function Invoke-Git {
    param(
        [Parameter(Mandatory)]
        [string[]]$Arguments
    )

    $output = @(& $script:GitExecutable @Arguments 2>&1)
    $exitCode = $LASTEXITCODE
    $textOutput = @($output | ForEach-Object { $_.ToString() })

    if ($exitCode -ne 0) {
        $commandText = 'git ' + ($Arguments -join ' ')
        $details = $textOutput -join [Environment]::NewLine
        throw "$commandText failed with exit code $exitCode.$([Environment]::NewLine)$details"
    }

    return $textOutput
}

function Get-GitHubRepositoryId {
    param(
        [Parameter(Mandatory)]
        [string]$RemoteUrl
    )

    $normalizedUrl = $RemoteUrl.Trim().Replace('\', '/')
    $match = [regex]::Match(
        $normalizedUrl,
        'github\.com(?::|/)(?<owner>[^/]+)/(?<repo>[^/]+?)(?:\.git)?/?$',
        [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
    )

    if (-not $match.Success) {
        return $null
    }

    return ('{0}/{1}' -f $match.Groups['owner'].Value, $match.Groups['repo'].Value).ToLowerInvariant()
}

function Sync-EngineRepository {
    param(
        [Parameter(Mandatory)]
        [pscustomobject]$Engine,

        [Parameter(Mandatory)]
        [string]$Root
    )

    $destination = Get-CanonicalPath -Path (Join-Path -Path $Root -ChildPath $Engine.Directory)
    if (-not (Test-PathWithin -Candidate $destination -Parent $Root)) {
        throw "Engine destination escapes TargetRoot: '$destination'."
    }

    if (Test-PathWithin -Candidate $destination -Parent $script:RepositoryRoot) {
        throw "Refusing to place an engine inside the hub repository: '$destination'."
    }

    if (-not (Test-Path -LiteralPath $destination)) {
        if ($PSCmdlet.ShouldProcess($destination, "Clone $($Engine.RepositoryId)")) {
            Invoke-Git -Arguments @('clone', '--origin', 'origin', $Engine.Url, $destination) |
                ForEach-Object { Write-Host $_ }
            return [pscustomobject]@{
                Engine = $Engine.Directory
                Status = 'Cloned'
                Detail = $Engine.RepositoryId
            }
        }

        return [pscustomobject]@{
            Engine = $Engine.Directory
            Status = 'Planned'
            Detail = 'Clone skipped by ShouldProcess'
        }
    }

    if (-not (Test-Path -LiteralPath $destination -PathType Container)) {
        throw "Destination exists but is not a directory: '$destination'."
    }

    $insideWorkTree = (Invoke-Git -Arguments @(
            '-C', $destination, 'rev-parse', '--is-inside-work-tree'
        ) | Select-Object -First 1)
    if ($insideWorkTree -ne 'true') {
        throw "Destination is not a Git worktree: '$destination'."
    }

    $workTreeRoot = Get-CanonicalPath -Path (
        Invoke-Git -Arguments @('-C', $destination, 'rev-parse', '--show-toplevel') |
            Select-Object -First 1
    )
    if (-not $workTreeRoot.Equals($destination, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Destination is nested in another Git worktree: '$destination'."
    }

    $originUrl = Invoke-Git -Arguments @(
        '-C', $destination, 'remote', 'get-url', 'origin'
    ) | Select-Object -First 1
    $originRepositoryId = Get-GitHubRepositoryId -RemoteUrl $originUrl
    if ($originRepositoryId -ne $Engine.RepositoryId.ToLowerInvariant()) {
        throw "Origin mismatch at '$destination': expected '$($Engine.RepositoryId)', found '$originUrl'."
    }

    $changes = @(Invoke-Git -Arguments @(
            '-C', $destination, 'status', '--porcelain=v1', '--untracked-files=normal'
        ))
    if ($changes.Count -gt 0) {
        Write-Warning "Skipping '$($Engine.Directory)': local changes or untracked files are present."
        return [pscustomobject]@{
            Engine = $Engine.Directory
            Status = 'Skipped'
            Detail = 'Dirty worktree'
        }
    }

    if (-not $PSCmdlet.ShouldProcess(
            $destination,
            'Fetch origin and fast-forward the checked-out branch when safe'
        )) {
        return [pscustomobject]@{
            Engine = $Engine.Directory
            Status = 'Planned'
            Detail = 'Safe update skipped by ShouldProcess'
        }
    }

    Invoke-Git -Arguments @('-C', $destination, 'fetch', '--prune', 'origin') |
        ForEach-Object { Write-Host $_ }

    $branch = Invoke-Git -Arguments @(
        '-C', $destination, 'rev-parse', '--abbrev-ref', 'HEAD'
    ) | Select-Object -First 1
    if ($branch -eq 'HEAD') {
        return [pscustomobject]@{
            Engine = $Engine.Directory
            Status = 'Fetched'
            Detail = 'Detached HEAD; no fast-forward attempted'
        }
    }

    try {
        $upstream = Invoke-Git -Arguments @(
            '-C', $destination, 'rev-parse', '--symbolic-full-name', '@{upstream}'
        ) | Select-Object -First 1
    }
    catch {
        return [pscustomobject]@{
            Engine = $Engine.Directory
            Status = 'Fetched'
            Detail = "Branch '$branch' has no upstream"
        }
    }

    if (-not $upstream.StartsWith(
            'refs/remotes/origin/',
            [System.StringComparison]::OrdinalIgnoreCase
        )) {
        return [pscustomobject]@{
            Engine = $Engine.Directory
            Status = 'Fetched'
            Detail = "Upstream '$upstream' is not on origin"
        }
    }

    $counts = Invoke-Git -Arguments @(
        '-C', $destination, 'rev-list', '--left-right', '--count', "HEAD...$upstream"
    ) | Select-Object -First 1
    $countMatch = [regex]::Match($counts, '^\s*(?<local>\d+)\s+(?<remote>\d+)\s*$')
    if (-not $countMatch.Success) {
        throw "Could not parse ahead/behind counts for '$destination': '$counts'."
    }

    $localAhead = [int]$countMatch.Groups['local'].Value
    $remoteAhead = [int]$countMatch.Groups['remote'].Value
    if ($localAhead -gt 0) {
        return [pscustomobject]@{
            Engine = $Engine.Directory
            Status = 'Fetched'
            Detail = "Local branch is ahead by $localAhead; no merge attempted"
        }
    }

    if ($remoteAhead -eq 0) {
        return [pscustomobject]@{
            Engine = $Engine.Directory
            Status = 'Current'
            Detail = "Branch '$branch' is up to date"
        }
    }

    Invoke-Git -Arguments @(
        '-C', $destination, 'merge', '--ff-only', '--no-edit', $upstream
    ) | ForEach-Object { Write-Host $_ }

    return [pscustomobject]@{
        Engine = $Engine.Directory
        Status = 'Updated'
        Detail = "Fast-forwarded '$branch' by $remoteAhead commit(s)"
    }
}

$script:GitExecutable = (Get-Command -Name 'git' -CommandType Application).Source
$script:RepositoryRoot = Get-CanonicalPath -Path (Join-Path -Path $PSScriptRoot -ChildPath '..\..')

if ([string]::IsNullOrWhiteSpace($TargetRoot)) {
    $projectsRoot = Split-Path -Parent (Split-Path -Parent $script:RepositoryRoot)
    $TargetRoot = Join-Path -Path $projectsRoot -ChildPath 'trading-engines'
}

$TargetRoot = Get-CanonicalPath -Path $TargetRoot
if (Test-PathWithin -Candidate $TargetRoot -Parent $script:RepositoryRoot) {
    throw "TargetRoot must be outside the hub repository. Refusing '$TargetRoot'."
}

if ((Test-Path -LiteralPath $TargetRoot) -and
    -not (Test-Path -LiteralPath $TargetRoot -PathType Container)) {
    throw "TargetRoot exists but is not a directory: '$TargetRoot'."
}

if (-not (Test-Path -LiteralPath $TargetRoot)) {
    if ($PSCmdlet.ShouldProcess($TargetRoot, 'Create engine workspace directory')) {
        New-Item -ItemType Directory -Path $TargetRoot | Out-Null
    }

    if (-not (Test-Path -LiteralPath $TargetRoot) -and -not $WhatIfPreference) {
        throw "TargetRoot was not created: '$TargetRoot'."
    }
}

$engines = @(
    [pscustomobject]@{
        Directory = 'freqtrade'
        RepositoryId = 'freqtrade/freqtrade'
        Url = 'https://github.com/freqtrade/freqtrade.git'
    }
    [pscustomobject]@{
        Directory = 'passivbot'
        RepositoryId = 'enarjord/passivbot'
        Url = 'https://github.com/enarjord/passivbot.git'
    }
    [pscustomobject]@{
        Directory = 'AI-Trader'
        RepositoryId = 'HKUDS/AI-Trader'
        Url = 'https://github.com/HKUDS/AI-Trader.git'
    }
    [pscustomobject]@{
        Directory = 'openalgo'
        RepositoryId = 'marketcalls/openalgo'
        Url = 'https://github.com/marketcalls/openalgo.git'
    }
    [pscustomobject]@{
        Directory = 'jesse'
        RepositoryId = 'jesse-ai/jesse'
        Url = 'https://github.com/jesse-ai/jesse.git'
    }
    [pscustomobject]@{
        Directory = 'octobot'
        RepositoryId = 'drakkar-software/octobot'
        Url = 'https://github.com/drakkar-software/octobot.git'
    }
    [pscustomobject]@{
        Directory = 'OpenAlice'
        RepositoryId = 'TraderAlice/OpenAlice'
        Url = 'https://github.com/TraderAlice/OpenAlice.git'
    }
)

$results = [System.Collections.Generic.List[object]]::new()
$failures = [System.Collections.Generic.List[string]]::new()

foreach ($engine in $engines) {
    try {
        $results.Add((Sync-EngineRepository -Engine $engine -Root $TargetRoot))
    }
    catch {
        $failures.Add($engine.Directory)
        $results.Add([pscustomobject]@{
                Engine = $engine.Directory
                Status = 'Failed'
                Detail = $_.Exception.Message
            })
    }
}

$results | Format-Table -AutoSize | Out-String | Write-Host

if ($failures.Count -gt 0) {
    throw "One or more engine operations failed: $($failures -join ', ')."
}
