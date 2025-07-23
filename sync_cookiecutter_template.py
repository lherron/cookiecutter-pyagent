#!/usr/bin/env python3
"""
sync_cookiecutter_template.py
=============================

Synchronise a rendered Cookiecutter project back into its template.

Features
--------
* Updates **only** files that already exist in the template.
* Prints
    • files present in expanded dir but not in template   (Unmapped ➜ template)  
    • files present in template but not in expanded dir   (Missing  ⬅ template)
* Shows a coloured unified diff (green = added, red = removed) for every text file
  whose contents would change in the template.
* Supports **--diff-only** to preview all changes without modifying any files.
* Never creates extra files or directories in the template.

Example
-------
    python sync_cookiecutter_template.py \
        --template-dir cookiecutter-pyagent \
        --expanded-dir simplecalc \
        --var project_slug=simplecalc \
        --var project_name="Simple Calc" \
        --var module_name=calc \
        --diff-only
"""
from __future__ import annotations

import argparse
import difflib
import os
import sys
from pathlib import Path
from typing import Dict, List

# ─────────────────────────────────────────────────────────────── parameters
TEXT_CHUNK = 16 * 1024  # bytes read to detect binary files

# ────────────────────────────────────── ANSI colours for diffs
RED = "\033[31m"
GREEN = "\033[32m"
RESET = "\033[0m"


# ───────────────────────────────────────────── argument parsing
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--template-dir", required=True, help="Cookiecutter template root")
    p.add_argument("--expanded-dir", required=True, help="Rendered project root")
    p.add_argument(
        "--var",
        action="append",
        required=True,
        metavar="NAME=VALUE",
        help="Cookiecutter variable and its rendered value",
    )
    p.add_argument(
        "--diff-only",
        action="store_true",
        help="Show diffs / notices, but do not write any files",
    )
    return p.parse_args()


# ───────────────────────────────────────────── mappings utilities
def make_maps(specs: List[str]) -> tuple[Dict[str, str], Dict[str, str]]:
    """
    Returns two mappings sorted longest‑first:

        render2tpl : rendered value        ->  {{cookiecutter.name}}
        tpl2render : {{cookiecutter.name}} ->  rendered value
    """
    render2tpl: Dict[str, str] = {}
    tpl2render: Dict[str, str] = {}
    for spec in specs:
        if "=" not in spec:
            sys.exit(f"--var expects NAME=VALUE, got {spec!r}")
        name, value = spec.split("=", 1)
        placeholder = f"{{{{cookiecutter.{name}}}}}"
        render2tpl[value] = placeholder
        tpl2render[placeholder] = value

    # longest first prevents 'calc' from short‑circuiting 'simplecalc'
    render2tpl = dict(sorted(render2tpl.items(), key=lambda t: len(t[0]), reverse=True))
    tpl2render = dict(sorted(tpl2render.items(), key=lambda t: len(t[0]), reverse=True))
    return render2tpl, tpl2render


# ───────────────────────────────────────────── path / text helpers
def is_binary(path: Path) -> bool:
    try:
        with path.open("rb") as fh:
            chunk = fh.read(TEXT_CHUNK)
        return b"\0" in chunk
    except Exception:
        return True


def substitute(text: str, mapping: Dict[str, str]) -> str:
    """Plain, order‑preserving replace on a text buffer."""
    new = text
    for src, dst in mapping.items():
        new = new.replace(src, dst)
    return new


def relpath_substitute(rel: Path, mapping: Dict[str, str]) -> Path:
    """Apply mapping to every path component of a relative path."""
    parts = []
    for part in rel.parts:
        new = part
        for src, dst in mapping.items():
            new = new.replace(src, dst)
        parts.append(new)
    return Path(*parts)


# ───────────────────────────────────────────── diff helper
def print_color_diff(old: str, new: str, rel: Path) -> None:
    """
    Pretty‑print a unified diff with ANSI colours.
    Only content lines beginning with "+" or "-" are colourised;
    diff headers keep default colour.
    """
    diff = difflib.unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile=f"a/{rel}",
        tofile=f"b/{rel}",
        lineterm="",
    )
    for line in diff:
        if line.startswith("+") and not line.startswith("+++"):
            print(f"{GREEN}{line}{RESET}", end="")
        elif line.startswith("-") and not line.startswith("---"):
            print(f"{RED}{line}{RESET}", end="")
        else:
            print(line, end="")


# ───────────────────────────────────────────── main procedure
def main() -> None:
    ns = parse_args()
    tmpl_root = Path(ns.template_dir).resolve()
    exp_root = Path(ns.expanded_dir).resolve()
    diff_only: bool = ns.diff_only

    if not tmpl_root.is_dir():
        sys.exit(f"{tmpl_root} is not a directory")
    if not exp_root.is_dir():
        sys.exit(f"{exp_root} is not a directory")

    render2tpl, tpl2render = make_maps(ns.var)

    unmapped_expanded: List[Path] = []
    missing_in_expanded: List[Path] = []

    # Pass 1 – walk expanded tree, update template counterparts
    for cur_dir, _, files in os.walk(exp_root):
        for fname in files:
            exp_path = Path(cur_dir) / fname
            exp_rel = exp_path.relative_to(exp_root)
            tpl_rel = relpath_substitute(exp_rel, render2tpl)
            tpl_path = tmpl_root / tpl_rel

            if not tpl_path.is_file():
                # Skip files in .venv and .mypy_cache directories
                if '.venv' not in exp_rel.parts and '.mypy_cache' not in exp_rel.parts:
                    unmapped_expanded.append(exp_rel)
                continue

            # Skip README.md files
            if fname == "README.md":
                continue

            # update template file
            if is_binary(exp_path):
                exp_bytes = exp_path.read_bytes()
                if tpl_path.read_bytes() != exp_bytes:
                    if diff_only:
                        print(f"Binary file differs (would update): {tpl_rel}")
                    else:
                        tpl_path.write_bytes(exp_bytes)
            else:
                text = exp_path.read_text(encoding="utf-8")
                new_text = substitute(text, render2tpl)
                old_text = tpl_path.read_text(encoding="utf-8")
                if old_text != new_text:
                    print_color_diff(old_text, new_text, tpl_rel)
                    if not diff_only:
                        tpl_path.write_text(new_text, encoding="utf-8")

    # Pass 2 – detect template files that have no counterpart in expanded tree
    for cur_dir, _, files in os.walk(tmpl_root):
        for fname in files:
            tpl_path = Path(cur_dir) / fname
            tpl_rel = tpl_path.relative_to(tmpl_root)
            exp_rel = relpath_substitute(tpl_rel, tpl2render)
            if not (exp_root / exp_rel).is_file():
                missing_in_expanded.append(tpl_rel)

    # ── report ───────────────────────────────────────────────────
    if unmapped_expanded:
        print("\nFiles present only in expanded dir (not written to template):")
        for p in sorted(unmapped_expanded):
            print(f"  {p}")

    if missing_in_expanded:
        print("\nFiles present only in template dir (no counterpart in expanded):")
        for p in sorted(missing_in_expanded):
            print(f"  {p}")

    if diff_only:
        print("\n(Diff‑only mode — no files were modified.)")
    elif not unmapped_expanded and not missing_in_expanded:
        print("Template and expanded project are fully in sync.")


if __name__ == "__main__":
    main()
