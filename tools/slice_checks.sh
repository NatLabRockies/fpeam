#!/usr/bin/env bash
# Per-slice validation harness for the MOVES5 default-refresh slice plan.
# Deliberately uses `set -uo pipefail` (NOT -e) so individual grep misses do not
# abort the script; each check reports pass/fail and we aggregate an exit code.
#
# Usage: bash tools/slice_checks.sh <SLICE_ID>
set -uo pipefail

SLICE="${1:?usage: slice_checks.sh <SLICE_ID>}"
FAIL=0

pass() { printf 'PASS  %s\n' "$1"; }
fail() { printf 'FAIL  %s\n' "$1"; FAIL=1; }

# assert a fixed string IS present in a file
must_have() {
  local file="$1" needle="$2"
  if grep -Fq -- "$needle" "$file" 2>/dev/null; then
    pass "$file contains: $needle"
  else
    fail "$file missing:   $needle"
  fi
}

# assert a fixed string is ABSENT from a file
must_not_have() {
  local file="$1" needle="$2"
  if grep -Fq -- "$needle" "$file" 2>/dev/null; then
    fail "$file still has:  $needle"
  else
    pass "$file free of:   $needle"
  fi
}

py_compiles() {
  local file="$1"
  if python -c "import py_compile,sys; py_compile.compile(sys.argv[1], doraise=True)" "$file" >/dev/null 2>&1; then
    pass "python compiles: $file"
  else
    fail "syntax error:   $file"
  fi
}

SPEC="src/FPEAM/configs/moves.spec"
AVS="src/FPEAM/gui/AttributeValueStorage.py"
AMT="src/FPEAM/gui/AllModuleTab.py"

case "$SLICE" in
  S01)
    # moves.spec: MOVES database / version / path refreshed to MOVES5
    must_have     "$SPEC" "moves_database = string(default='movesdb20241112')"
    must_have     "$SPEC" "moves_version = string(default='MOVES5')"
    must_have     "$SPEC" "moves_path = filepath(default='C:/MOVES5.0')"
    must_not_have "$SPEC" "movesdb2220802"
    must_not_have "$SPEC" "default='MOVES3'"
    must_not_have "$SPEC" "default='C:/MOVES3.0'"
    ;;
  S02)
    # GUI MOVES-field defaults refreshed; NONROAD (N-suffixed) fields untouched.
    must_have     "$AVS" 'self.dbName = "movesdb20241112"'
    must_have     "$AVS" 'self.movesPath = r"C:\MOVES5.0"'
    must_not_have "$AVS" 'self.dbName = "movesdb20180517"'
    must_not_have "$AVS" 'self.movesPath = r"C:\MOVES2014b"'
    # NONROAD default must be preserved
    must_have     "$AVS" 'self.dbNameN = "movesdb20180517"'

    must_have     "$AMT" 'self.lineEditDbName.setText("movesdb20241112")'
    must_not_have "$AMT" 'self.lineEditDbName.setText("movesdb20180517")'
    must_have     "$AMT" 'self.lineEditMovesPath.setText(r"C:\MOVES5.0")'
    must_have     "$AMT" 'self.lineEditMovesPath.setText("C:/MOVES5.0")'
    must_not_have "$AMT" 'self.lineEditMovesPath.setText(r"C:\MOVES2014b")'
    must_not_have "$AMT" 'self.lineEditMovesPath.setText("C:/MOVES2014b")'
    # NONROAD line-edit defaults must be preserved
    must_have     "$AMT" 'self.lineEditDbNameN.setText("movesdb20180517")'
    must_have     "$AMT" 'self.lineEditNonExePath.setText("C:/MOVES2014b/NONROAD/NR08a")'

    py_compiles   "$AVS"
    py_compiles   "$AMT"
    ;;
  *)
    echo "unknown slice: $SLICE" >&2
    exit 2
    ;;
esac

if [[ "$FAIL" -ne 0 ]]; then
  echo "SLICE $SLICE: FAILED"
  exit 1
fi
echo "SLICE $SLICE: OK"
