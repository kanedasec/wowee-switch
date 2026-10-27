#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
NRO="${1:-$ROOT/../build-switch/wowee.nro}"
OUTPUT="${2:-$ROOT/out/switch/WoWee-forwarder.nsp}"
NTON_BIN="${NTON:-nton}"
KEYS="${NTON_KEYS:-$HOME/.switch/prod.keys}"
TITLE_ID="01A57EE0C0DE1000"
TITLE_ID_LOWER="${TITLE_ID,,}"
VERSION="2.12.0"

command -v "$NTON_BIN" >/dev/null || {
    echo "nton is required: https://github.com/rlaphoenix/nton" >&2
    exit 1
}
[ -f "$NRO" ] || { echo "NRO not found: $NRO" >&2; exit 1; }
[ -f "$KEYS" ] || {
    echo "Your own prod.keys is required at $KEYS (or set NTON_KEYS)." >&2
    exit 1
}

NRO="$(realpath "$NRO")"
ICON="$(realpath "$ROOT/assets/switch/wowee-icon.jpg")"
OUTPUT="$(realpath -m "$OUTPUT")"
KEYS="$(realpath "$KEYS")"
KEY_WORK="$(mktemp -d)"
trap 'rm -rf "$KEY_WORK"' EXIT
ln -s "$KEYS" "$KEY_WORK/prod.keys"

# nton looks for ./prod.keys or ~/.switch/prod.keys. Running from the key's
# temporary directory supports an explicit NTON_KEYS without copying it.
(
    cd "$KEY_WORK"
    "$NTON_BIN" build "$NRO" \
        --sdmc /switch/wowee/wowee.nro \
        --name WoWee \
        --publisher "WoWee contributors" \
        --version "$VERSION" \
        --icon "$ICON" \
        --id "$TITLE_ID"
)

BUILT="$HOME/Desktop/NTON/WoWee v$VERSION by WoWee contributors [$TITLE_ID_LOWER].nsp"
[ -f "$BUILT" ] || { echo "nton completed but its expected NSP was not found: $BUILT" >&2; exit 1; }
mkdir -p "$(dirname "$OUTPUT")"
cp "$BUILT" "$OUTPUT"
echo "Forwarder: $OUTPUT"
