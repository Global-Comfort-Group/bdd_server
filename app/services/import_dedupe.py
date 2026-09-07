"""
Duplicate detection for the Excel bulk property import.

Two different mechanisms, deliberately:

  * ``flag_duplicates`` — FUZZY, used at PREVIEW time to *advise* the admin.
    Flags a row when its name AND its address both look like an existing
    property (or an earlier row in the same file). Advisory only: the admin
    can always override a flag with the checkbox.

  * ``import_key`` — EXACT, used at CONFIRM time to *enforce*. Whatever the
    client sends, a row whose normalized (name, address) key already exists
    is not inserted a second time.

Enforcement is exact rather than fuzzy on purpose: confirm re-derives its
answer from the database, and a fuzzy answer there could differ from what the
preview showed the user for the same row.

Both reuse ``_normalize_address`` from ``app.services.duplicate`` so import
dedupe agrees with the app's existing duplicate-checker about what an address
is. The composite matcher in that module is deliberately NOT reused: imported
properties share a placeholder lot_area and carry no coordinates, so its area
and GPS terms are constant and would skew every comparison.
"""
from typing import Any, Dict, List, Optional, Sequence, Tuple

import re

from fuzzywuzzy import fuzz

from app.services.duplicate import _normalize_address

# A row is flagged only when BOTH signals fire. Address alone over-flags this
# data set: the BDD sheets carry region/type codes ("..._NCR_CO_001") that
# survive normalization, so unrelated properties in one region share tokens.
_NAME_THRESHOLD = 0.90
_ADDRESS_THRESHOLD = 0.85

# token_sort_ratio cannot reach _NAME_THRESHOLD once two strings differ this
# much in length, so the comparison can be skipped outright.
_LENGTH_GUARD = 0.35


def normalize_name(name: Optional[str]) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    if not name:
        return ""
    text = re.sub(r"[^a-z0-9\s]", " ", name.lower())
    return " ".join(text.split())


def import_key(name: Optional[str], address: Optional[str]) -> str:
    """Exact dedupe key. Two rows collide only if both their normalized name
    and their normalized address match exactly."""
    return f"{normalize_name(name)}||{_normalize_address(address)}"


def _too_different_in_length(a: str, b: str) -> bool:
    longest = max(len(a), len(b))
    if longest == 0:
        return False
    return abs(len(a) - len(b)) / longest > _LENGTH_GUARD


def _similar(a: str, b: str, threshold: float) -> Optional[float]:
    """Return the similarity score when it clears ``threshold``, else None."""
    if not a or not b:
        return None
    if _too_different_in_length(a, b):
        return None
    score = fuzz.token_sort_ratio(a, b) / 100.0
    return score if score >= threshold else None


def discriminators(norm_name: str) -> frozenset:
    """Tokens that DISTINGUISH one property from another with a similar name.

    This portfolio names sibling properties by appending a small identifier:

        Lot A / Lot B / ... / Lot F - Mariveles Bataan
        Jenny's Ave Warehouse 1  vs  Jenny's Ave Warehouse 2
        408 Bulalakaw Porperty   vs  426 Bulalakaw Porperty
        Fourlane Bataan 3,000    vs  Fourlane Bataan 6,000

    Those are different properties, but the distinguishing token is a single
    character in an otherwise identical string — exactly what token_sort_ratio
    treats as noise, so all of the above score 0.86-0.96 and would be flagged
    as duplicates without this guard.

    Returns every digit run found ANYWHERE in the name — "Lot2" hides its
    discriminator inside a token, so splitting on whitespace alone misses it —
    plus every single-letter token. Two names with different discriminator sets
    are never fuzzy-matched, regardless of score.
    """
    numbers = frozenset(re.findall(r"\d+", norm_name))
    letters = frozenset(tok for tok in norm_name.split() if len(tok) == 1)
    return numbers | letters


def _match_score(
    name_a: str, addr_a: str, name_b: str, addr_b: str
) -> Optional[float]:
    """Both name and address must clear their thresholds. Returns the lower of
    the two scores (the weaker signal) so the caller can rank matches."""
    # A difference in lot number / letter means different properties, however
    # similar the rest of the text is.
    if discriminators(name_a) != discriminators(name_b):
        return None
    name_score = _similar(name_a, name_b, _NAME_THRESHOLD)
    if name_score is None:
        return None
    addr_score = _similar(addr_a, addr_b, _ADDRESS_THRESHOLD)
    if addr_score is None:
        return None
    return min(name_score, addr_score)


def flag_duplicates(
    rows: List[Dict[str, Any]],
    existing: Sequence[Tuple[int, Optional[str], Optional[str], str]],
) -> List[Dict[str, Any]]:
    """Annotate each parsed row in place with duplicate information.

    ``existing`` is a sequence of ``(id, name, address, source)`` where source
    describes where the match lives — "database" for a real property,
    "import queue" for a staging row awaiting review. A lead imported last
    month and not yet promoted is still a duplicate for this month's file, so
    both are passed in together and the label says which was hit.

    Adds three keys to every row:
      ``duplicate_kind``  — "existing" | "in_file" | None
      ``duplicate_of``    — human-readable description of what it matched
      ``duplicate_score`` — similarity of the weaker of the two signals

    An exact key match short-circuits the fuzzy pass, so re-importing the same
    file is fast and always flags every repeat.
    """
    existing_norm = [
        (pid, normalize_name(name), _normalize_address(address), name, source)
        for pid, name, address, source in existing
    ]
    existing_by_key = {
        import_key(name, address): (pid, name, source)
        for pid, name, address, source in existing
    }

    # Rows already accepted in this pass, for in-file duplicate detection.
    seen_by_key: Dict[str, Dict[str, Any]] = {}
    seen_norm: List[Tuple[str, str, Dict[str, Any]]] = []

    for row in rows:
        name, address = row.get("name"), row.get("address")
        norm_name, norm_addr = normalize_name(name), _normalize_address(address)
        row["duplicate_kind"] = None
        row["duplicate_of"] = None
        row["duplicate_score"] = None

        # Rows with nothing to compare are left unflagged; bulk_import skips
        # them anyway for missing name/address.
        if not norm_name and not norm_addr:
            continue

        # 1. Exact match against an existing property.
        key = import_key(name, address)
        hit = existing_by_key.get(key)
        if hit:
            row["duplicate_kind"] = "existing"
            row["duplicate_of"] = f"Already in {hit[2]}: {hit[1]}"
            row["duplicate_score"] = 1.0
            continue

        # 2. Exact match against an earlier row in this file.
        earlier = seen_by_key.get(key)
        if earlier:
            row["duplicate_kind"] = "in_file"
            row["duplicate_of"] = (
                f"Same as row {earlier['row_number']} on {earlier['sheet_name']}"
            )
            row["duplicate_score"] = 1.0
            continue

        # 3. Fuzzy match against existing properties.
        best: Optional[Tuple[float, str, str]] = None
        for _pid, ex_name, ex_addr, ex_label, ex_source in existing_norm:
            score = _match_score(norm_name, norm_addr, ex_name, ex_addr)
            if score is not None and (best is None or score > best[0]):
                best = (score, "existing", f"Likely already in {ex_source}: {ex_label}")

        # 4. Fuzzy match against earlier rows in this file.
        for prev_name, prev_addr, prev_row in seen_norm:
            score = _match_score(norm_name, norm_addr, prev_name, prev_addr)
            if score is not None and (best is None or score > best[0]):
                best = (
                    score,
                    "in_file",
                    f"Likely same as row {prev_row['row_number']} "
                    f"on {prev_row['sheet_name']}",
                )

        if best:
            row["duplicate_score"], row["duplicate_kind"], row["duplicate_of"] = best
        else:
            # Only unflagged rows become comparison targets, so a run of three
            # copies flags copies 2 and 3 against the first rather than chaining.
            seen_by_key[key] = row
            seen_norm.append((norm_name, norm_addr, row))

    return rows
