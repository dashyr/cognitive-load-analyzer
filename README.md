# cognitive-load-analyzer

A small toolkit to estimate "mental juggling" (cognitive load) of small code snippets in C and Forth.
It uses libclang (clang.cindex) for accurate C parsing and a heuristic Forth tokenizer for Forth snippets.
Produces raw counts (tokens, bindings, stack slots, temporaries, nesting, control points, sequencing)
and computes a tunable cognitive-load scalar from configurable weights.

---

## Repo layout

- `refined_cognitive_load.py` — main analyzer script (libclang + Forth analyzer, batch runner, CSV output, sensitivity helper)
- `examples/c/` — canonical C examples
- `examples/forth/` — canonical Forth examples
- `weights.json` — default weights (edit to experiment)
- `requirements.txt` — Python dependencies

---

## Requirements

- Python 3.8+
- libclang / clang installed (see installation notes below)
- Python packages: see `requirements.txt`

---

## Installing libclang

- Debian/Ubuntu:
  - `sudo apt-get update && sudo apt-get install -y clang libclang-dev`
- macOS (Homebrew):
  - `brew install llvm`
  - Note: Homebrew installs LLVM into `/usr/local/opt/llvm` or `/opt/homebrew/opt/llvm`. You may need to point `libclang.dylib` in the script (see below).
- Windows:
  - Install LLVM (official installer) or Visual Studio LLVM tools; note the path to `libclang.dll`.

If the script fails to find libclang automatically, set the path at the top of `refined_cognitive_load.py`:

```python
from clang import cindex
cindex.Config.set_library_file("/full/path/to/libclang.so")   # Linux
# cindex.Config.set_library_file("/full/path/to/libclang.dylib")  # macOS
# cindex.Config.set_library_file(r"C:\path\to\libclang.dll")  # Windows
