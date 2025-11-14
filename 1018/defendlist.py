#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract AI defense techniques (and subTechniques) from your tactic JS files and export to CSV.
Prints per-file counts for easy debugging.

Usage:
  python defendlist.py
"""

import os, re, csv
from typing import List, Tuple

# Your file list (in the relative paths you provided earlier)
FILES = [
    "../aidefense-framework/tactics/deceive.js",
    "../aidefense-framework/tactics/detect.js",
    "../aidefense-framework/tactics/evict.js",
    "../aidefense-framework/tactics/harden.js",
    "../aidefense-framework/tactics/isolate.js",
    "../aidefense-framework/tactics/model.js",
    "../aidefense-framework/tactics/restore.js",
]

OUT_PATH = "AI_Defense_Techniques.csv"

def read_text(p: str) -> str:
    with open(p, "r", encoding="utf-8") as f:
        return f.read()

def collapse_ws(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()

def find_array_blocks(text: str, key: str) -> List[Tuple[int, int]]:
    """
    Locate the [ ... ] block for key: [ ... ].
    Supports "key": [ ... ] or 'key': [ ... ] or key: [ ... ].
    Returns the tuple (start_after_bracket, end_bracket_index) list.
    """
    out = []
    pat = rf'(["\']?){re.escape(key)}\1\s*:\s*\['
    for m in re.finditer(pat, text):
        start = m.end()  # position right after '['
        i = start
        depth = 1
        in_single = in_double = in_back = False
        esc = False
        while i < len(text):
            ch = text[i]
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == "'" and not in_double and not in_back:
                in_single = not in_single
            elif ch == '"' and not in_single and not in_back:
                in_double = not in_double
            elif ch == "`" and not in_single and not in_double:
                in_back = not in_back
            elif not in_single and not in_double and not in_back:
                if ch == "[":
                    depth += 1
                elif ch == "]":
                    depth -= 1
                    if depth == 0:
                        out.append((start, i))
                        break
            i += 1
    return out

def extract_top_level_objs(array_text: str) -> List[str]:
    """Extract only top-level { ... } objects from a JS array (ignore nested child objects)."""
    objs = []
    i, L = 0, len(array_text)
    while i < L:
        ch = array_text[i]
        if ch.isspace() or ch == ",":
            i += 1
            continue
        if ch == "{":
            start = i
            depth = 0
            in_single = in_double = in_back = False
            esc = False
            while i < L:
                c = array_text[i]
                if esc:
                    esc = False
                elif c == "\\":
                    esc = True
                elif c == "'" and not in_double and not in_back:
                    in_single = not in_single
                elif c == '"' and not in_single and not in_back:
                    in_double = not in_double
                elif c == "`" and not in_single and not in_double:
                    in_back = not in_back
                elif not in_single and not in_double and not in_back:
                    if c == "{":
                        depth += 1
                    elif c == "}":
                        depth -= 1
                        if depth == 0:
                            end = i
                            objs.append(array_text[start:end+1])
                            i = end + 1
                            break
                i += 1
        else:
            i += 1
    return objs

def extract_str(obj_text: str, field: str) -> str:
    """Extract a string field (supports ", ', ` as value delimiters)."""
    pats = [
        rf'{re.escape(field)}\s*:\s*"((?:[^"\\]|\\.)*)"',
        rf"{re.escape(field)}\s*:\s*'((?:[^'\\]|\\.)*)'",
        rf'{re.escape(field)}\s*:\s*`((?:[^`\\]|\\.)*)`',
        rf'["\']{re.escape(field)}["\']\s*:\s*"((?:[^"\\]|\\.)*)"',
        rf'["\']{re.escape(field)}["\']\s*:\s*\'((?:[^\'\\]|\\.)*)\'',
        rf'["\']{re.escape(field)}["\']\s*:\s*`((?:[^`\\]|\\.)*)`',
    ]
    for p in pats:
        m = re.search(p, obj_text, flags=re.DOTALL)
        if m:
            raw = (m.group(1)
                   .replace(r'\"', '"')
                   .replace(r"\'", "'")
                   .replace(r"\n", "\n")
                   .replace(r"\t", "\t")
                   .replace(r"\\", "\\"))
            return collapse_ws(raw)

    # Rare: bare token without quotes
    m2 = re.search(rf'{re.escape(field)}\s*:\s*([A-Za-z0-9_.-]+)', obj_text)
    if not m2:
        m2 = re.search(rf'["\']{re.escape(field)}["\']\s*:\s*([A-Za-z0-9_.-]+)', obj_text)
    return collapse_ws(m2.group(1)) if m2 else ""

def get_tactic_name(text: str) -> str:
    # Get the first name field defined as name: "...".
    m = re.search(r'(["\']?)name\1\s*:\s*(?P<q>["\'`])(?P<v>.*?)(?P=q)', text, flags=re.DOTALL)
    return collapse_ws(m.group("v")) if m else ""

def parse_one(text: str, include_sub=True):
    tactic = get_tactic_name(text)
    techniques, subs = [], []

    # Find "techniques" array blocks
    tech_blocks = find_array_blocks(text, "techniques")
    for (s, e) in tech_blocks:
        arr = text[s:e]
        for obj in extract_top_level_objs(arr):
            tid = extract_str(obj, "id")
            tname = extract_str(obj, "name")
            desc = extract_str(obj, "description")
            techniques.append({"id": tid, "name": tname, "description": desc})

            if include_sub:
                for (ss, ee) in find_array_blocks(obj, "subTechniques"):
                    sub_arr = obj[ss:ee]
                    for sobj in extract_top_level_objs(sub_arr):
                        sid = extract_str(sobj, "id")
                        sname = extract_str(sobj, "name")
                        sdesc = extract_str(sobj, "description")
                        subs.append({
                            "parent_id": tid, "id": sid, "name": sname, "description": sdesc
                        })

    return tactic, techniques, subs

def fallback_scan(text: str):
    """
    Fallback method: scan for any { ... } block containing id/name/description.
    May catch extra objects, but ensures non-zero results.
    Only detects top-level sized blocks (limit to avoid huge memory).
    """
    results = []
    for m in re.finditer(r"\{[^{}]{20,5000}\}", text, flags=re.DOTALL):
        block = m.group(0)
        tid = extract_str(block, "id")
        tname = extract_str(block, "name")
        desc = extract_str(block, "description")
        if tname and (tid or desc):
            results.append({"id": tid, "name": tname, "description": desc})
    return results

def main():
    rows = []
    total_tech, total_sub = 0, 0

    for path in FILES:
        if not os.path.exists(path):
            print(f"[WARN] not found: {path}")
            continue

        text = read_text(path)
        tactic, techs, subs = parse_one(text, include_sub=True)

        # If no techniques were extracted at all, trigger fallback
        if not techs:
            fb = fallback_scan(text)
            if fb:
                print(f"[INFO] fallback used for {os.path.basename(path)} -> {len(fb)} items")
                techs = fb

        print(f"[OK] {os.path.basename(path)} | tactic='{tactic or '?'}' | techniques={len(techs)} | subTechniques={len(subs)}")

        total_tech += len(techs)
        total_sub  += len(subs)

        for t in techs:
            rows.append({
                "Source File": os.path.basename(path),
                "Tactic": tactic,
                "Level": "Technique",
                "Parent Technique ID": "",
                "Technique ID": t.get("id",""),
                "Technique Name": t.get("name",""),
                "Description": t.get("description",""),
            })
        for st in subs:
            rows.append({
                "Source File": os.path.basename(path),
                "Tactic": tactic,
                "Level": "SubTechnique",
                "Parent Technique ID": st.get("parent_id",""),
                "Technique ID": st.get("id",""),
                "Technique Name": st.get("name",""),
                "Description": st.get("description",""),
            })

    # Export CSV
    with open(OUT_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "Source File","Tactic","Level","Parent Technique ID",
            "Technique ID","Technique Name","Description"
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDone. Wrote {len(rows)} rows -> {os.path.abspath(OUT_PATH)}")
    print(f"  Techniques: {total_tech} | SubTechniques: {total_sub}")

if __name__ == "__main__":
    main()
