#!/usr/bin/env bash
# Instala la skill dividir-gastos para Claude Code y/o Codex.
# Uso: ./install.sh [claude|codex|proyecto|todos]   (por defecto: claude)
set -euo pipefail
ORIGEN="$(cd "$(dirname "$0")" && pwd)/skills/dividir-gastos"
DESTINO="${1:-claude}"
copiar() { mkdir -p "$1"; rm -rf "$1/dividir-gastos"; cp -r "$ORIGEN" "$1/"; echo "Instalada en $1/dividir-gastos"; }
command -v python3 >/dev/null || { echo "ERROR: se necesita Python 3.8+"; exit 1; }
case "$DESTINO" in
  claude)   copiar "$HOME/.claude/skills" ;;
  codex)    copiar "$HOME/.codex/skills" ;;
  proyecto) copiar "$PWD/.claude/skills"; copiar "$PWD/.codex/skills" ;;
  todos)    copiar "$HOME/.claude/skills"; copiar "$HOME/.codex/skills" ;;
  *) echo "Opción no válida: $DESTINO (usa claude|codex|proyecto|todos)"; exit 1 ;;
esac
