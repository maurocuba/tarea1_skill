# Instala la skill dividir-gastos en Windows (PowerShell).
# Uso: .\install.ps1 [-Destino claude|codex|todos]
param([string]$Destino = "claude")
$Origen = Join-Path $PSScriptRoot "skills\dividir-gastos"
function Copiar($base) {
  New-Item -ItemType Directory -Force -Path $base | Out-Null
  $d = Join-Path $base "dividir-gastos"
  if (Test-Path $d) { Remove-Item -Recurse -Force $d }
  Copy-Item -Recurse $Origen $d
  Write-Host "Instalada en $d"
}
switch ($Destino) {
  "claude" { Copiar "$HOME\.claude\skills" }
  "codex"  { Copiar "$HOME\.codex\skills" }
  "todos"  { Copiar "$HOME\.claude\skills"; Copiar "$HOME\.codex\skills" }
  default  { Write-Host "Opción no válida: $Destino"; exit 1 }
}
