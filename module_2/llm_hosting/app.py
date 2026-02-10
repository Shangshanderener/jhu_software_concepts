# -*- coding: utf-8 -*-
"""Flask + tiny local LLM standardizer with incremental JSONL CLI output."""

from __future__ import annotations

import json
import os
import re
import sys
import difflib
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import threading
from typing import Any, Dict, List, Tuple

from flask import Flask, jsonify, request
from huggingface_hub import hf_hub_download
from llama_cpp import Llama  # CPU-only by default if N_GPU_LAYERS=0

app = Flask(__name__)

# ---------------- Model config ----------------
MODEL_REPO = os.getenv(
    "MODEL_REPO",
    "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
)
MODEL_FILE = os.getenv(
    "MODEL_FILE",
    "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
)

N_THREADS = int(os.getenv("N_THREADS", str(os.cpu_count() or 2)))
N_CTX = int(os.getenv("N_CTX", "2048"))
N_GPU_LAYERS = int(os.getenv("N_GPU_LAYERS", "0"))  # 0 → CPU-only

CANON_UNIS_PATH = os.getenv("CANON_UNIS_PATH", "canon_universities.txt")
CANON_PROGS_PATH = os.getenv("CANON_PROGS_PATH", "canon_programs.txt")

# Precompiled, non-greedy JSON object matcher to tolerate chatter around JSON
JSON_OBJ_RE = re.compile(r"\{.*?\}", re.DOTALL)

# ---------------- Canonical lists + abbrev maps ----------------
def _read_lines(path: str) -> List[str]:
    """Read non-empty, stripped lines from a file (UTF-8)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [ln.strip() for ln in f if ln.strip()]
    except FileNotFoundError:
        return []


CANON_UNIS = _read_lines(CANON_UNIS_PATH)
CANON_PROGS = _read_lines(CANON_PROGS_PATH)

ABBREV_UNI: Dict[str, str] = {
    r"(?i)^mcg(\.|ill)?$": "McGill University",
    r"(?i)^(ubc|u\.?b\.?c\.?)$": "University of British Columbia",
    r"(?i)^uoft$": "University of Toronto",
}

COMMON_UNI_FIXES: Dict[str, str] = {
    "McGiill University": "McGill University",
    "Mcgill University": "McGill University",
    # Normalize 'Of' → 'of'
    "University Of British Columbia": "University of British Columbia",
}

COMMON_PROG_FIXES: Dict[str, str] = {
    "Mathematic": "Mathematics",
    "Info Studies": "Information Studies",
}

# ---------------- Few-shot prompt ----------------
SYSTEM_PROMPT = (
    "You are a data cleaning assistant. Standardize degree program and university "
    "names.\n\n"
    "Rules:\n"
    "- Input provides a single string under key `program` that may contain both "
    "program and university.\n"
    "- Split into (program name, university name).\n"
    "- Trim extra spaces and commas.\n"
    '- Expand obvious abbreviations (e.g., "McG" -> "McGill University", '
    '"UBC" -> "University of British Columbia").\n'
    "- Use Title Case for program; use official capitalization for university "
    "names (e.g., \"University of X\").\n"
    '- Ensure correct spelling (e.g., "McGill", not "McGiill").\n'
    '- If university cannot be inferred, return "Unknown".\n\n'
    "Return JSON ONLY with keys:\n"
    "  standardized_program, standardized_university\n"
)

FEW_SHOTS: List[Tuple[Dict[str, str], Dict[str, str]]] = [
    (
        {"program": "Information Studies, McGill University"},
        {
            "standardized_program": "Information Studies",
            "standardized_university": "McGill University",
        },
    ),
    (
        {"program": "Information, McG"},
        {
            "standardized_program": "Information Studies",
            "standardized_university": "McGill University",
        },
    ),
    (
        {"program": "Mathematics, University Of British Columbia"},
        {
            "standardized_program": "Mathematics",
            "standardized_university": "University of British Columbia",
        },
    ),
]

_LLM: Llama | None = None
_LLM_LOCK = threading.Lock()


def _load_llm() -> Llama:
    """Download (or reuse) the GGUF file and initialize llama.cpp (thread-safe)."""
    global _LLM
    if _LLM is not None:
        return _LLM

    with _LLM_LOCK:
        # Double-check after acquiring lock
        if _LLM is not None:
            return _LLM

        model_path = hf_hub_download(
            repo_id=MODEL_REPO,
            filename=MODEL_FILE,
            local_dir="models",
            local_dir_use_symlinks=False,
            force_filename=MODEL_FILE,
        )

        _LLM = Llama(
            model_path=model_path,
            n_ctx=N_CTX,
            n_threads=N_THREADS,
            n_gpu_layers=N_GPU_LAYERS,
            verbose=False,
        )
    return _LLM


# Precompiled pattern for university-keyword detection
_UNI_KW_RE = re.compile(
    r"(?i)\b(university|college|institute|school|polytechnic|academy|conservatory|seminary)"
    r"|(\b(?:MIT|UCLA|USC|NYU|CUNY|SUNY|UCSF|UCSD|UCI|UCR|UCD|UCSB|UCSC|UCB|UBC|EPFL|ETH|Caltech|Emory|Purdue|Rutgers|Drexel|Brandeis|Tufts|Vanderbilt|Georgetown|Stanford|Harvard|Yale|Princeton|Columbia|Cornell|Dartmouth|Brown|Rice|Duke|Oxford|Cambridge)\b)"
)


def _smart_split(text: str) -> Tuple[str, str]:
    """
    Split a combined 'program, university' string by scanning from the RIGHT
    to find the university portion. Handles multi-comma program names like
    'Criminology, Law and Society, Temple University' correctly.
    """
    s = re.sub(r"\s+", " ", (text or "")).strip().strip(",")

    # Split on commas and scan from the right
    parts = [p.strip() for p in s.split(",") if p.strip()]
    if len(parts) <= 1:
        # No comma — try the whole thing as program
        return s, ""

    # Scan from right: try building the university from 1, 2, ... rightmost parts
    for i in range(len(parts) - 1, 0, -1):
        candidate_uni = ", ".join(parts[i:])
        # Check against canon list first (exact then fuzzy with high cutoff)
        if candidate_uni in CANON_UNIS:
            return ", ".join(parts[:i]), candidate_uni
        canon_match = _best_match(candidate_uni, CANON_UNIS, cutoff=0.88)
        if canon_match:
            return ", ".join(parts[:i]), canon_match
        # Check for university keywords
        if _UNI_KW_RE.search(candidate_uni):
            return ", ".join(parts[:i]), candidate_uni

    # Fallback: first part = program, rest = university
    return parts[0], ", ".join(parts[1:])


def _split_fallback(text: str) -> Tuple[str, str]:
    """Rules-based parser using right-scan splitting."""
    prog, uni = _smart_split(text)

    # High-signal abbreviation expansions
    if re.fullmatch(r"(?i)mcg(ill)?(\.)?", uni or ""):
        uni = "McGill University"
    if re.fullmatch(
        r"(?i)(ubc|u\.?b\.?c\.?|university of british columbia)",
        uni or "",
    ):
        uni = "University of British Columbia"

    # Title-case program; normalize 'Of' → 'of' for universities
    prog = prog.title()
    if uni:
        uni = re.sub(r"\bOf\b", "of", uni.title())
    else:
        uni = "Unknown"
    return prog, uni


def _best_match(name: str, candidates: List[str], cutoff: float = 0.80) -> str | None:
    """Fuzzy match via difflib (lightweight, Replit-friendly)."""
    if not name or not candidates:
        return None
    matches = difflib.get_close_matches(name, candidates, n=1, cutoff=cutoff)
    return matches[0] if matches else None


def _post_normalize_program(prog: str) -> str:
    """Apply common fixes, title case, then canonical/fuzzy mapping."""
    p = (prog or "").strip()
    p = COMMON_PROG_FIXES.get(p, p)
    # Strip trailing parenthetical abbreviations like "(OLPD)"
    p = re.sub(r"\s*\([A-Z]{2,}\)\s*$", "", p)
    # Strip leading "Department of" / "Dept. of"
    p = re.sub(r"^(department|dept\.?)\s+of\s+", "", p, flags=re.IGNORECASE)
    p = p.strip().strip(",").strip()
    p = p.title()
    # Normalize common small words
    for word in ["And", "Of", "In", "For", "The", "With", "To"]:
        p = re.sub(rf"\b{word}\b", word.lower(), p)
    # Capitalize first letter
    if p:
        p = p[0].upper() + p[1:]
    if p in CANON_PROGS:
        return p
    match = _best_match(p, CANON_PROGS, cutoff=0.78)
    return match or p


def _post_normalize_university(uni: str) -> str:
    """Expand abbreviations, apply common fixes, capitalization, and canonical map."""
    u = (uni or "").strip()

    # Abbreviations
    for pat, full in ABBREV_UNI.items():
        if re.fullmatch(pat, u):
            u = full
            break

    # Common spelling fixes
    u = COMMON_UNI_FIXES.get(u, u)

    # Strip trailing parenthetical abbreviations like "(MIT)"
    u = re.sub(r"\s*\([A-Z]{2,}\)\s*$", "", u).strip()

    # Normalize capitalization: title case, then fix 'Of' → 'of'
    if u:
        u = u.title()
        for word in ["Of", "And", "In", "For", "The", "At", "De", "Du", "Des"]:
            u = re.sub(rf"\b{word}\b", word.lower(), u)
        # Capitalize first letter
        u = u[0].upper() + u[1:]

    # Canonical or fuzzy map
    if u in CANON_UNIS:
        return u
    match = _best_match(u, CANON_UNIS, cutoff=0.80)
    return match or u or "Unknown"

# Cache for LLM results to avoid redundant calls
_LLM_CACHE: Dict[str, Tuple[str, str]] = {}

# Parallel processing config
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))


def _try_rule_based_parse(program_text: str) -> Tuple[str, str] | None:
    """
    Attempt to parse program/university using rules only.
    Uses right-scan splitting to correctly handle multi-comma program names.
    Returns (program, university) if confident, else None to trigger LLM.
    """
    if not program_text or not program_text.strip():
        return ("Unknown", "Unknown")

    # Use smart right-scan splitting
    prog_raw, uni_raw = _smart_split(program_text)

    if not uni_raw:
        # Can't reliably split - need LLM
        return None

    # Normalize program
    prog = _post_normalize_program(prog_raw)

    # Normalize university
    uni = _post_normalize_university(uni_raw)

    # If university normalized successfully (not "Unknown" and found in canon or fuzzy matched)
    # and program looks valid, we can skip LLM
    if uni != "Unknown" and prog:
        return (prog, uni)

    # If we got a good fuzzy match for university, trust it
    if uni and uni in CANON_UNIS:
        return (prog, uni)

    # Otherwise, might need LLM for ambiguous cases
    return None


@lru_cache(maxsize=10000)
def _call_llm_cached(program_text: str) -> Tuple[str, str]:
    """Cached wrapper for LLM calls. Returns (program, university) tuple."""
    llm = _load_llm()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for x_in, x_out in FEW_SHOTS:
        messages.append(
            {"role": "user", "content": json.dumps(x_in, ensure_ascii=False)}
        )
        messages.append(
            {
                "role": "assistant",
                "content": json.dumps(x_out, ensure_ascii=False),
            }
        )
    messages.append(
        {
            "role": "user",
            "content": json.dumps({"program": program_text}, ensure_ascii=False),
        }
    )

    out = llm.create_chat_completion(
        messages=messages,
        temperature=0.0,
        max_tokens=128,
        top_p=1.0,
    )

    text = (out["choices"][0]["message"]["content"] or "").strip()
    try:
        match = JSON_OBJ_RE.search(text)
        obj = json.loads(match.group(0) if match else text)
        std_prog = str(obj.get("standardized_program", "")).strip()
        std_uni = str(obj.get("standardized_university", "")).strip()
    except Exception:
        std_prog, std_uni = _split_fallback(program_text)

    std_prog = _post_normalize_program(std_prog)
    std_uni = _post_normalize_university(std_uni)
    return (std_prog, std_uni)


def _call_llm(program_text: str) -> Dict[str, str]:
    """Query the tiny LLM and return standardized fields (with caching)."""
    std_prog, std_uni = _call_llm_cached(program_text)
    return {
        "standardized_program": std_prog,
        "standardized_university": std_uni,
    }


def _standardize_fast(program_text: str) -> Dict[str, str]:
    """
    Fast standardization: try rules first, fall back to cached LLM.
    This is the main entry point for processing.
    """
    # Try rule-based parsing first (instant)
    result = _try_rule_based_parse(program_text)
    if result is not None:
        return {
            "standardized_program": result[0],
            "standardized_university": result[1],
        }

    # Fall back to cached LLM call
    return _call_llm(program_text)


def _normalize_input(payload: Any) -> List[Dict[str, Any]]:
    """Accept either a list of rows or {'rows': [...]}."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("rows"), list):
        return payload["rows"]
    return []


@app.get("/")
def health() -> Any:
    """Simple liveness check."""
    return jsonify({"ok": True})


@app.post("/standardize")
def standardize() -> Any:
    """Standardize rows from an HTTP request and return JSON."""
    payload = request.get_json(force=True, silent=True)
    rows = _normalize_input(payload)

    out: List[Dict[str, Any]] = []
    for row in rows:
        program_text = (row or {}).get("program") or ""
        result = _standardize_fast(program_text)
        row["llm-generated-program"] = result["standardized_program"]
        row["llm-generated-university"] = result["standardized_university"]
        out.append(row)

    return jsonify({"rows": out})


def _process_single_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single row with fast standardization."""
    program_text = (row or {}).get("program") or ""
    result = _standardize_fast(program_text)
    row["llm-generated-program"] = result["standardized_program"]
    row["llm-generated-university"] = result["standardized_university"]
    return row


def _cli_process_file(
    in_path: str,
    out_path: str | None,
    append: bool,
    to_stdout: bool,
    parallel: bool = True,
) -> None:
    """Process a JSON file with optional parallel processing."""
    with open(in_path, "r", encoding="utf-8") as f:
        rows = _normalize_input(json.load(f))

    total = len(rows)
    print(f"Processing {total} rows...", file=sys.stderr)

    # First pass: separate into rule-parseable vs LLM-needed
    rule_parsed: List[Tuple[int, Dict[str, Any]]] = []
    llm_needed: List[Tuple[int, Dict[str, Any]]] = []

    for idx, row in enumerate(rows):
        program_text = (row or {}).get("program") or ""
        result = _try_rule_based_parse(program_text)
        if result is not None:
            row["llm-generated-program"] = result[0]
            row["llm-generated-university"] = result[1]
            rule_parsed.append((idx, row))
        else:
            llm_needed.append((idx, row))

    print(
        f"  Rule-parsed: {len(rule_parsed)} | LLM-needed: {len(llm_needed)}",
        file=sys.stderr,
    )

    # Process LLM-needed rows sequentially (LLM isn't thread-safe)
    # Pre-load the model once before processing
    processed_llm: List[Tuple[int, Dict[str, Any]]] = []
    if llm_needed:
        print("  Loading LLM model...", file=sys.stderr)
        _load_llm()  # Pre-load to avoid issues
        print("  Processing LLM rows...", file=sys.stderr)
        for idx, row in llm_needed:
            processed_llm.append((idx, _process_single_row(row)))

    # Merge and sort by original index
    all_processed = sorted(rule_parsed + processed_llm, key=lambda x: x[0])

    # Write output as JSON array
    sink = sys.stdout if to_stdout else None
    if not to_stdout:
        out_path = out_path or in_path.replace(".json", "_llm.json")
        mode = "a" if append else "w"
        sink = open(out_path, mode, encoding="utf-8")

    assert sink is not None

    try:
        # Extract just the rows (without indices) and write as JSON array
        rows_out = [row for _, row in all_processed]
        json.dump(rows_out, sink, ensure_ascii=False, indent=2)
        sink.write("\n")
        sink.flush()
        print(f"Done! Processed {total} rows.", file=sys.stderr)
    finally:
        if sink is not sys.stdout:
            sink.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Standardize program/university with a tiny local LLM.",
    )
    parser.add_argument(
        "--file",
        help="Path to JSON input (list of rows or {'rows': [...]})",
        default=None,
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Run the HTTP server instead of CLI.",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output path for JSON Lines (ndjson). "
        "Defaults to <input>.jsonl when --file is set.",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to the output file instead of overwriting.",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Write JSON Lines to stdout instead of a file.",
    )
    args = parser.parse_args()

    if args.serve or args.file is None:
        port = int(os.getenv("PORT", "8000"))
        app.run(host="0.0.0.0", port=port, debug=False)
    else:
        _cli_process_file(
            in_path=args.file,
            out_path=args.out,
            append=bool(args.append),
            to_stdout=bool(args.stdout),
        )
