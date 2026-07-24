# MOVES5 default-refresh plan (FPEAM)

Refreshes stale MOVES version/database defaults in FPEAM to the current MOVES5
release. Addresses the "stale version defaults" finding from the EPA-feedback
audit. Scope is intentionally narrow:

- **In scope:** the MOVES default database name, MOVES version label, and MOVES
  install path defaults in `moves.spec` and the GUI prefill defaults.
- **Out of scope (do NOT change):** NONROAD defaults (the `*N` / `Non` /
  `NonExe` / `dbNameN` fields, `nonroad.spec`), `skipdomaindatabasevalidation`
  (kept as-is by decision), study parameters like `year`/`yearMoves`, and any
  runtime logic. This is a defaults-only refresh.

Target values (MOVES5, confirmed with user):
- MOVES default database: `movesdb2220802` / `movesdb20180517` -> `movesdb20241112`
- MOVES version label: `MOVES3` -> `MOVES5`
- MOVES install path: `C:/MOVES3.0` (spec) and `C:\MOVES2014b` (GUI) -> `C:/MOVES5.0`

Validation for every slice: `bash tools/slice_checks.sh <SLICE_ID>`.

---

### Slice S01: Refresh MOVES defaults in moves.spec

**Phase:** 1
**Estimated size:** small
**Files to create/modify:**
  - src/FPEAM/configs/moves.spec (edit)

Update three default values in `src/FPEAM/configs/moves.spec`:
  - `moves_database = string(default='movesdb2220802')`
    -> `moves_database = string(default='movesdb20241112')`
  - `moves_version = string(default='MOVES3')`
    -> `moves_version = string(default='MOVES5')`
  - `moves_path = filepath(default='C:/MOVES3.0')`
    -> `moves_path = filepath(default='C:/MOVES5.0')`

Also update the adjacent human-readable comment `# ... (Windows: C:/MOVES3.0)`
to say `C:/MOVES5.0` so the doc matches the default. Do NOT touch the `year`
default, the DB host/port/user/pass options, `nonroad.spec`, or any NONROAD path.

**Acceptance criteria:**
  - [ ] moves.spec defaults are movesdb20241112 / MOVES5 / C:/MOVES5.0.
  - [ ] No `movesdb2220802`, `default='MOVES3'`, or `default='C:/MOVES3.0'` remain.
  - [ ] `bash tools/slice_checks.sh S01` passes.

---

### Slice S02: Refresh MOVES GUI prefill defaults

**Phase:** 1
**Depends on:** S01
**Estimated size:** small
**Files to create/modify:**
  - src/FPEAM/gui/AttributeValueStorage.py (edit)
  - src/FPEAM/gui/AllModuleTab.py (edit)

Update ONLY the MOVES-module prefill defaults. The NONROAD fields use an `N`
suffix (`dbNameN`, `lineEditDbNameN`, `lineEditNonExePath`) and MUST be left
unchanged.

In `src/FPEAM/gui/AttributeValueStorage.py`:
  - `self.dbName = "movesdb20180517"`  -> `self.dbName = "movesdb20241112"`
  - `self.movesPath = r"C:\MOVES2014b"` -> `self.movesPath = r"C:\MOVES5.0"`
  - Leave `self.dbNameN = "movesdb20180517"` (NONROAD) unchanged.

In `src/FPEAM/gui/AllModuleTab.py`, update only the MOVES (`DbName` /
`MovesPath`) line-edit defaults, leaving NONROAD (`DbNameN` / `NonExePath`)
lines unchanged:
  - `self.lineEditDbName.setText("movesdb20180517")`
    -> `self.lineEditDbName.setText("movesdb20241112")` (occurs at lines ~988 and ~3416)
  - `self.lineEditMovesPath.setText(r"C:\MOVES2014b")`
    -> `self.lineEditMovesPath.setText(r"C:\MOVES5.0")` (line ~842)
  - `self.lineEditMovesPath.setText("C:/MOVES2014b")`
    -> `self.lineEditMovesPath.setText("C:/MOVES5.0")` (line ~3420)

Both files must still import/compile cleanly.

**Acceptance criteria:**
  - [ ] MOVES GUI defaults are movesdb20241112 / MOVES5.0; no MOVES field still
        references movesdb20180517 or MOVES2014b.
  - [ ] NONROAD `dbNameN` / `lineEditDbNameN` defaults are unchanged.
  - [ ] Both GUI files compile.
  - [ ] `bash tools/slice_checks.sh S02` passes.
