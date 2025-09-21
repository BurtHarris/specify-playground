#!/usr/bin/env bash
# Apply small, safe automated fixes to make CI/linter output less noisy for the prototype.
# - Convert stray f-strings without placeholders to normal strings
# - Replace `assert False` idioms with `raise AssertionError(...)`
# - Convert `== True` / `== False` patterns to idiomatic asserts (in tests only)

set -euo pipefail

echo "Applying quick automated fixes..."

python - <<'PY'
from pathlib import Path
import re

# 1) Fix simple f-strings without placeholders in interactive_resolver.py
p = Path('interactive_resolver.py')
txt = p.read_text(encoding='utf-8')
txt = re.sub(r'f"([^{}]*)"', r'"\1"', txt)
p.write_text(txt, encoding='utf-8')

# 2) Replace assert(True)/assert(False) placeholders in contract tests with raises
for f in Path('tests/contract').glob('*.py'):
	txt = f.read_text(encoding='utf-8')
	txt = re.sub(r"assert\s*\(\s*True\s*\)\s*,?", 'raise AssertionError("Noted requirement")\n', txt)
	txt = re.sub(r"assert\s*\(\s*False\s*\)\s*,?", 'raise AssertionError("Contract requirement")\n', txt)
	f.write_text(txt, encoding='utf-8')

# 3) Convert simple '== True'/'== False' assertions in integration tests
for f in Path('tests/integration').glob('*.py'):
	txt = f.read_text(encoding='utf-8')
	txt = re.sub(r'assert\s+([\w\.\[\]\'\"\-]+)\s*==\s*True', r'assert \1', txt)
	txt = re.sub(r'assert\s+([\w\.\[\]\'\"\-]+)\s*==\s*False', r'assert not \1', txt)
	f.write_text(txt, encoding='utf-8')

print('Applied quick fixes')
PY

echo "Quick fixes applied (review changes before committing)."

git add interactive_resolver.py tests/contract tests/integration || true

echo "Done."
