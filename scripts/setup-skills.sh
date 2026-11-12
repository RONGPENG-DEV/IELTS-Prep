#!/usr/bin/env bash
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-skills.txt
practice_dir="${HOME}/.english-practice"
mkdir -p "$practice_dir/history" "$practice_dir/quiz_history"
if [[ ! -e "$practice_dir/template.html" ]]; then
  cp vendor/english-practice-skill/template.html "$practice_dir/template.html"
fi
python3 vendor/english-skill/shadowing-practice/scripts/validate_skill.py --format json
.venv/bin/python -c 'import jsonschema, edge_tts; print("Skills dependencies OK")'
