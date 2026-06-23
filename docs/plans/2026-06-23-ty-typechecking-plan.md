# Ty Typechecking and Deprecation Fixes Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Resolve all 364 type checking diagnostics by ignoring dynamic Django-specific warnings and fixing actual deprecations and imports in the codebase.

**Architecture:** We will adjust the type checker rules in `pyproject.toml` to ignore unresolved attributes and argument mismatches (since `ty` does not support Django stubs natively). We will then fix the codebase deprecations by migrating from `os.system` to `subprocess.run` inside `app/utils/database.py` and adding an explicit submodule import in `app/BillOfQuantities/exporters/detailed_report_exporter.py`.

**Tech Stack:** Python 3.13, Django 5.x, ty (Type Checker), subprocess

---

### Task 1: Update type checking configuration in `pyproject.toml`

**Files:**
- Modify: `pyproject.toml:34-44`

**Step 1: Check existing warnings**

Verify that running `ty` normally reports 364 diagnostics:
Run: `.venv\Scripts\python.exe -m ty check . --python .venv\Scripts\python.exe`
Expected: Outputs "Found 364 diagnostics" and exits.

**Step 2: Update configuration in pyproject.toml**

Update the rules under `[tool.ty.rules]` to ignore the following warnings:
- `unresolved-attribute = "ignore"`
- `invalid-argument-type = "ignore"`
- `unused-type-ignore-comment = "ignore"`
- `unused-ignore-comment = "ignore"`

Target replacement block:
```toml
[tool.ty.rules]
# ty cannot resolve Django's runtime-generated attributes (reverse FKs,
# _id fields, CBV mixins, form field types). django-stubs covers these
# for mypy/pyright but ty doesn't fully support them yet.
# Revisit when ty adds Django support.
unresolved-attribute = "ignore"
invalid-argument-type = "ignore"
unused-type-ignore-comment = "ignore"
unused-ignore-comment = "ignore"
```

**Step 3: Run the check to verify the warning count is reduced**

Run: `.venv\Scripts\python.exe -m ty check . --python .venv\Scripts\python.exe`
Expected: Outputs "Found 4 diagnostics" (the 3 os.system deprecations and the 1 openpyxl import warning).

**Step 4: Commit**

Run:
```bash
git add pyproject.toml
git commit -m "config: update ty configuration to ignore django dynamic attributes and unused type ignores"
```

---

### Task 2: Replace soft-deprecated `os.system` with `subprocess.run` in `app/utils/database.py`

**Files:**
- Modify: `app/utils/database.py:1-44`

**Step 1: Run local checks to verify database.py warnings**

Confirm warnings exist for `app/utils/database.py`:
Run: `.venv\Scripts\python.exe -m ty check . --python .venv\Scripts\python.exe`
Expected: Look for `warning[deprecated]: The function system is deprecated` pointing to lines 28, 38, 42.

**Step 2: Replace os.system with subprocess.run**

Import `sys` and `subprocess`, then replace `os.system` in `app/utils/database.py`:

```python
import glob
import os
import subprocess
import sys

from django.conf import settings

# ...

def clear_migration_table():
    apps = get_apps()
    for app in apps:
        subprocess.run([sys.executable, "manage.py", "migrate", "--fake", app, "zero"], check=True)

# ...

def make_migrations():
    subprocess.run([sys.executable, "manage.py", "makemigrations"], check=True)


def fake_initial():
    subprocess.run([sys.executable, "manage.py", "migrate", "--fake-initial"], check=True)
```

**Step 3: Verify the warnings in database.py are resolved**

Run: `.venv\Scripts\python.exe -m ty check . --python .venv\Scripts\python.exe`
Expected: Warnings for `app/utils/database.py` are gone. Only 1 diagnostic remains (about `openpyxl.utils`).

**Step 4: Commit**

Run:
```bash
git add app/utils/database.py
git commit -m "refactor: replace deprecated os.system with subprocess.run in migration tools"
```

---

### Task 3: Fix submodule import warning in `app/BillOfQuantities/exporters/detailed_report_exporter.py`

**Files:**
- Modify: `app/BillOfQuantities/exporters/detailed_report_exporter.py`

**Step 1: Verify warning exists**

Run: `.venv\Scripts\python.exe -m ty check . --python .venv\Scripts\python.exe`
Expected: Look for `warning[possibly-missing-submodule]: Submodule utils might not have been imported` at line 386.

**Step 2: Import get_column_letter explicitly**

Add the import at the top of the file:
```python
from openpyxl.utils import get_column_letter
```
And replace:
```python
col_letter = openpyxl.utils.get_column_letter(col_idx)
```
with:
```python
col_letter = get_column_letter(col_idx)
```

**Step 3: Run the check to verify 0 diagnostics**

Run: `.venv\Scripts\python.exe -m ty check . --python .venv\Scripts\python.exe`
Expected: Outputs "Found 0 diagnostics" or passes successfully with no error.

**Step 4: Commit**

Run:
```bash
git add app/BillOfQuantities/exporters/detailed_report_exporter.py
git commit -m "fix: explicitly import get_column_letter to satisfy type checker"
```
