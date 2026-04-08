#!/usr/bin/env python3
"""
refined_cognitive_load.py

Cognitive-load analyzer for toy C and Forth snippets.

- Uses libclang (clang.cindex) for C parsing and tokenization.
- Uses heuristic tokenizer/analysis for Forth.
- Batch mode: analyze a directory of examples (c/ and forth/).
- Sensitivity helper: sweep weights and record result stability.

Usage examples:
  python refined_cognitive_load.py --batch examples/ --weights weights.json --out results.csv
  python refined_cognitive_load.py --sensitivity --batch examples/ --out-dir plots/ --weights weights.json
"""

import os
import sys
import json
import argparse
import re
import math
import csv
from collections import defaultdict
from clang import cindex

# If libclang is not found automatically, uncomment and set path:
# cindex.Config.set_library_file("/path/to/libclang.so")  # linux
# cindex.Config.set_library_file("/path/to/libclang.dylib")  # macOS
# cindex.Config.set_library_file(r"C:\path\to\libclang.dll")  # Windows

# Default weights
DEFAULT_WEIGHTS = {
    "wT": 0.2,
    "wB": 1.0,
    "wS": 0.9,
    "wR": 0.8,
    "wN": 0.5,
    "wC": 0.7,
    "wE": 0.4
}

# Forth stack-control and op words
FORTH_STACK_WORDS = {">r", "r>", "dup", "drop", "swap", "rot", "over", "nip", "tuck"}
FORTH_CONTROL_WORDS = {"if","else","then","begin","again","until","while","repeat","do","loop","?do"}

# ---------- C analysis (libclang) ----------
_CALL_KINDS = {cindex.CursorKind.CALL_EXPR, cindex.CursorKind.CXX_OPERATOR_CALL_EXPR}
_FUNC_DECL_KINDS = {cindex.CursorKind.FUNCTION_DECL, cindex.CursorKind.CXX_METHOD}
_CONTROL_KINDS = {
    cindex.CursorKind.IF_STMT,
    cindex.CursorKind.FOR_STMT,
    cindex.CursorKind.WHILE_STMT,
    cindex.CursorKind.DO_STMT,
    cindex.CursorKind.SWITCH_STMT,
}
_COMPOUND_KINDS = {cindex.CursorKind.COMPOUND_STMT}

def analyze_c_with_clang(filename, clang_args=None):
    if clang_args is None:
        clang_args = ['-std=c11']
    index = cindex.Index.create()
    tu = index.parse(filename, args=clang_args, options=cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)

    tokens = [t.spelling for t in tu.get_tokens(extent=tu.cursor.extent)]

    bindings = set()
    calls = 0
    control_count = 0
    max_compound_depth = 0

    def walk(node, depth=0):
        nonlocal calls, control_count, max_compound_depth
        if node.kind in _FUNC_DECL_KINDS:
            if node.spelling:
                bindings.add(node.spelling)
            for c in node.get_children():
                if c.kind == cindex.CursorKind.PARM_DECL and c.spelling:
                    bindings.add(c.spelling)
        if node.kind in _CALL_KINDS:
            calls += 1
        if node.kind in _CONTROL_KINDS:
            control_count += 1
        if node.kind in _COMPOUND_KINDS:
            max_compound_depth = max(max_compound_depth, depth + 1)
            child_depth = depth + 1
        else:
            child_depth = depth
        for child in node.get_children():
            walk(child, child_depth)

    walk(tu.cursor, depth=0)

    T = len(tokens)
    B = len(bindings)
    S = 0
    R = calls
    N = max_compound_depth
    C = control_count + calls
    arithmetic_ops = {"+", "-", "*", "/", "%"}
    E = sum(1 for tok in tokens if tok in arithmetic_ops or tok == ",")

    return {
        "T": T, "B": B, "S": S, "R": R, "N": N, "C": C, "E": E,
        "tokens": tokens, "bindings": sorted(bindings)
    }

# ---------- Forth analysis (heuristic) ----------
IDENT_NUM_RE = re.compile(r"^-?\d+$")

def tokenize_forth(code):
    code = re.sub(r"\\.*?$", "", code, flags=re.M)
    code = re.sub(r"\(.*?\)", "", code, flags=re.S)
    parts = re.split(r"\s+", code.strip())
    return [p for p in parts if p]

def analyze_forth(code):
    tokens = tokenize_forth(code)
    T = len(tokens)
    bindings = set()
    i = 0
    while i < len(tokens):
        tok = tokens[i].lower()
        if tok == ":" and i+1 < len(tokens):
            bindings.add(tokens[i+1])
            i += 2
            continue
        i += 1
    B = len(bindings)

    # S: detect usage patterns of numbers followed by a binding (heuristic)
    S = 0
    for j, tok in enumerate(tokens):
        if tok in bindings:
            k = j-1
            count_nums = 0
            while k >= 0 and IDENT_NUM_RE.match(tokens[k]) and count_nums < 16:
                count_nums += 1
                k -= 1
            S = max(S, count_nums)

    R = sum(1 for tok in tokens if tok.lower() in {">r", "r>"})
    N = 1 if ":" in tokens else 0
    ctrl_count = sum(1 for tok in tokens if tok.lower() in FORTH_CONTROL_WORDS)
    calls = sum(1 for tok in tokens if not IDENT_NUM_RE.match(tok) and tok not in {":",";"} )
    C = ctrl_count + calls
    seq_ops = sum(1 for tok in tokens if tok.lower() in FORTH_STACK_WORDS or re.match(r"^[+\-*/]$", tok) or tok.lower() in {">r","r>"})
    E = seq_ops

    return {
        "T": T, "B": B, "S": S, "R": R, "N": N, "C": C, "E": E,
        "tokens": tokens, "bindings": sorted(bindings)
    }

# ---------- Compute load ----------
def compute_load(counts, weights):
    L = (
        weights["wT"] * counts["T"]
        + weights["wB"] * counts["B"]
        + weights["wS"] * counts["S"]
        + weights["wR"] * counts["R"]
        + weights["wN"] * counts["N"]
        + weights["wC"] * counts["C"]
        + weights["wE"] * counts["E"]
    )
    return L

# ---------- Helpers: file / batch processing ----------
def analyze_file(path, lang=None, clang_args=None, weights=None):
    if weights is None:
        weights = DEFAULT_WEIGHTS
    ext = os.path.splitext(path)[1].lower()
    if lang is None:
        if ext in {".c", ".h"}:
            lang = "c"
        elif ext in {".forth", ".fs", ".fth", ".4th"} or path.endswith(".forth"):
            lang = "forth"
        else:
            # try to infer from directory name
            if "/c/" in path or "\\c\\" in path:
                lang = "c"
            elif "/forth/" in path or "\\forth\\" in path:
                lang = "forth"
            else:
                raise ValueError("Cannot infer language for: " + path)
    if lang == "c":
        counts = analyze_c_with_clang(path, clang_args=clang_args)
    elif lang == "forth":
        with open(path, "r", encoding="utf-8") as f:
            code = f.read()
        counts = analyze_forth(code)
    else:
        raise ValueError("Unsupported language: " + str(lang))
    load = compute_load(counts, weights)
    return counts, load

def batch_analyze(dirpath, clang_args=None, weights=None, out_csv=None):
    rows = []
    for root, dirs, files in os.walk(dirpath):
        for fn in files:
            if fn.startswith('.'):
                continue
            path = os.path.join(root, fn)
            try:
                counts, load = analyze_file(path, clang_args=clang_args, weights=weights)
                rows.append({
                    "path": path,
                    "lang": "c" if "/c/" in path or "\\c\\" in path else "forth",
                    **counts,
                    "L": load
                })
            except Exception as e:
                print(f"Warning: failed to analyze {path}: {e}", file=sys.stderr)
    if out_csv:
        keys = ["path","lang","T","B","S","R","N","C","E","L"]
        with open(out_csv, "w", newline="", encoding="utf-8") as wf:
            w = csv.DictWriter(wf, fieldnames=keys)
            w.writeheader()
            for r in rows:
                out = {k: r.get(k, "") for k in keys}
                w.writerow(out)
    return rows

# ---------- Sensitivity analysis ----------
def sensitivity_sweep(batch_dir, weight_ranges, clang_args=None, base_weights=None, out_dir=None):
    import numpy as np
    import matplotlib.pyplot as plt
    import pandas as pd

    if base_weights is None:
        base_weights = DEFAULT_WEIGHTS

    # produce combinations (cartesian product) for a small grid
    keys = list(weight_ranges.keys())
    grid = []
    def rec(idx, cur):
        if idx >= len(keys):
            grid.append(cur.copy()); return
        k = keys[idx]
        for v in weight_ranges[k]:
            cur[k] = v
            rec(idx+1, cur)
    rec(0, {})

    base_results = batch_analyze(batch_dir, clang_args=clang_args, weights=base_weights)
    base_map = {r["path"]: r["L"] for r in base_results}

    records = []
    for wset in grid:
        # merge with base weights
        ws = base_weights.copy()
        ws.update(wset)
        rows = batch_analyze(batch_dir, clang_args=clang_args, weights=ws)
        for r in rows:
            records.append({**wset, "path": r["path"], "L": r["L"]})

    df = pd.DataFrame(records)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        csvp = os.path.join(out_dir, "sensitivity.csv")
        df.to_csv(csvp, index=False)
        # Plot example: L difference from base for each example across one varied weight
        # Here create a basic plot per example vs one weight if only one key varied.
        for key in keys:
            plt.figure(figsize=(8,4))
            for path, grp in df.groupby("path"):
                plt.plot(grp[key], grp["L"], marker='o', label=os.path.basename(path))
            plt.xlabel(key)
            plt.ylabel("L")
            plt.legend()
            plt.tight_layout()
            plt.savefig(os.path.join(out_dir, f"sensitivity_{key}.png"))
            plt.close()
    return df

# ---------- CLI ----------
def load_weights(path):
    if path is None:
        return DEFAULT_WEIGHTS.copy()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    w = DEFAULT_WEIGHTS.copy()
    w.update(data)
    return w

def main():
    p = argparse.ArgumentParser(description="Cognitive-load analyzer (C + Forth)")
    p.add_argument("--batch", help="Directory to recursively analyze (examples/)", default=None)
    p.add_argument("--out", help="CSV output for batch", default="results.csv")
    p.add_argument("--weights", help="weights JSON file", default=None)
    p.add_argument("--clang-args", nargs="*", help="extra args to pass to clang parser", default=[])
    p.add_argument("--sensitivity", action="store_true", help="run sensitivity helper")
    p.add_argument("--out-dir", help="output dir for graphs/csv from sensitivity", default="plots")
    args = p.parse_args()

    weights = load_weights(args.weights)

    if args.batch:
        rows = batch_analyze(args.batch, clang_args=args.clang_args, weights=weights, out_csv=args.out)
        print(f"Wrote {args.out} ({len(rows)} entries)")
        for r in rows:
            print(f"{r['path']}: L={r['L']:.3f}")
        if args.sensitivity:
            # small example sweep: vary wS and wB moderately for demonstration
            weight_ranges = {
                "wS": [weights["wS"] * v for v in (0.5, 1.0, 1.5)],
                "wB": [weights["wB"] * v for v in (0.5, 1.0, 1.5)]
            }
            df = sensitivity_sweep(args.batch, weight_ranges, clang_args=args.clang_args, base_weights=weights, out_dir=args.out_dir)
            print(f"Sensitivity CSV written to {args.out_dir}/sensitivity.csv")
    else:
        p.print_help()

if __name__ == "__main__":
    main()
