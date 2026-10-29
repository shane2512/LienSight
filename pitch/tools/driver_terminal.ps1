# Types real commands (human cadence) into a real terminal and runs them for real.
$ErrorActionPreference = 'Continue'
$root = 'C:\dfol\legalhk'
$flag = Join-Path $root 'pitch\raw\go.flag'
$done = Join-Path $root 'pitch\raw\done.flag'
$ready = Join-Path $root 'pitch\raw\ready.flag'
Remove-Item $flag, $done, $ready -ErrorAction SilentlyContinue
$Host.UI.RawUI.WindowTitle = 'liensight-demo'
Set-Location $root
$env:PATH = (Join-Path $root 'workflow\node_modules\.bin') + ';' + $env:PATH   # bun for the CRE compiler (not shown)
Clear-Host
New-Item $ready -ItemType File | Out-Null
while (-not (Test-Path $flag)) { Start-Sleep -Milliseconds 100 }
function Say([string]$t, [int]$ms = 38) {
  Write-Host -NoNewline (prompt)
  foreach ($c in $t.ToCharArray()) { Write-Host -NoNewline $c; Start-Sleep -Milliseconds ($ms + (Get-Random -Minimum 0 -Maximum 30)) }
  Start-Sleep -Milliseconds 450; Write-Host ''
  Invoke-Expression $t
}
Start-Sleep -Milliseconds 1200
Say 'forge test --root contracts'
Start-Sleep -Milliseconds 1800
Say 'npm --prefix workflow test'
Start-Sleep -Milliseconds 1800
Say 'cre workflow simulate ./workflow -T staging-settings --non-interactive --trigger-index 0 --broadcast' 22
Start-Sleep -Milliseconds 2500
Say 'cast call 0xf813c584Fe5e8c86A3F6c7265923CeE0850604aE "restricted()(bool)" --rpc-url https://ethereum-sepolia-rpc.publicnode.com' 18
Start-Sleep -Milliseconds 1500
Say 'cast call 0xf813c584Fe5e8c86A3F6c7265923CeE0850604aE "transfer(address,uint256)(bool)" 0x000000000000000000000000000000000000dEaD 1 --from 0xd51E7130B55f10595939f274cCB8c00b52C915b4 --rpc-url https://ethereum-sepolia-rpc.publicnode.com' 12
Start-Sleep -Milliseconds 3500
Write-Host -NoNewline (prompt)
Start-Sleep -Milliseconds 800
New-Item $done -ItemType File | Out-Null
Start-Sleep -Milliseconds 600
exit
