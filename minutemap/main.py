"""
YearMinuteMap — hierarchical minute-resolution value scheduling.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Literal, Any
import json
import re
from dataclasses import dataclass
from datetime import datetime


NormalTokenKey = Literal["moy", "dow", "dom", "woy", "doy", "h", "m"]
TokenKey = Literal["q"] | NormalTokenKey

TOKEN_SPECIFICITY: dict[str, int] = {
    "q": 10,
    "moy": 20,
    "dow": 30,
    "dom": 40,
    "woy": 50,
    "doy": 60,
    "h": 70,
    "m": 80,
}
TOKEN_ALLOWED_CHILDREN: dict[str, set[str]] = {
    "q": {"dom", "dow", "h", "m"},
    "moy": {"dom", "dow", "h", "m"},
    "woy": {"dow", "h", "m"},
    "doy": {"h", "m"},
    "dom": {"h", "m"},
    "dow": {"h", "m"},
    "h": {"m"},
    "m": set(),
}
MONTH_ALIASES: dict[str, int] = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}
DOW_ALIASES: dict[str, int] = {
    "mon": 1,
    "tue": 2,
    "wed": 3,
    "thu": 4,
    "fri": 5,
    "sat": 6,
    "sun": 7,
}
Q_MONTHS: dict[str, tuple[int, int]] = {
    "q1": (1, 3),
    "q2": (4, 6),
    "q3": (7, 9),
    "q4": (10, 12),
}
TOKEN_RANGES: dict[NormalTokenKey, tuple[int, int]] = {
    "moy": (1, 12),
    "woy": (1, 53),
    "doy": (1, 366),
    "dom": (1, 31),
    "dow": (1, 7),
    "h": (0, 23),
    "m": (0, 59),
}


class Token(ABC):
    kind: str

    @abstractmethod
    def matches(self, v: int) -> bool:
        pass


@dataclass(frozen=True)
class RangeToken(Token):
    """Token dataclass"""

    kind: str
    lo: int
    hi: int
    step: int | None = None

    def matches(self, v: int) -> bool:
        if not self.step:
            return self.lo <= v <= self.hi
        else:
            return self.lo <= v and ((v - self.lo) % self.step) == 0 and v <= self.hi

    def __str__(self):
        return f"{self.kind}{self.lo}-{self.hi}" + (
            f"/{self.step}" if self.step else ""
        )


@dataclass(frozen=True)
class LstToken(Token):
    """Token dataclass"""

    kind: str
    lst: list[int]

    def matches(self, v: int) -> bool:
        return v in self.lst

    def __str__(self):
        return f"{self.kind}{','.join([str(v) for v in self.lst])}"


# Empty tuple == wildcard (matches everything).
ParsedPath = tuple[Token, ...]


class ParseError(ValueError):
    pass


def parse_range(kind: NormalTokenKey, text: str) -> Token:
    lo_bound, hi_bound = TOKEN_RANGES[kind]
    if m := re.fullmatch(r"(\d+)(?:-(\d+))?(\/(\d+))?", text):
        lo = int(m.group(1))
        hi = int(m.group(2)) if m.group(2) else lo
        step = int(m.group(4)) if m.group(4) else None
        if lo > hi:
            raise ParseError(f"Range lo > hi in '{text}' for {kind}")
        if lo < lo_bound or hi > hi_bound:
            raise ParseError(
                f"Range {lo}-{hi} out of bounds [{lo_bound},{hi_bound}] for {kind}"
            )
        if (step is not None) and step <= 0:
            raise ParseError(f"Range step {step} must be gte to 0")
        return RangeToken(kind, lo=lo, hi=hi, step=step)
    elif m := re.fullmatch(
        r"\*\/(\d+)", text
    ):  # The "*" case not handled here - handled by removing the range.
        lo = lo_bound
        hi = hi_bound
        step = int(m.group(1))
        if step <= 0:
            raise ParseError(f"Range step {step} must be gte to 0")
        return RangeToken(kind, lo=lo, hi=hi, step=step)
    elif re.fullmatch(r"(\d+)(,(\d+))+", text):
        lst = [int(i) for i in text.split(",")]
        lo = min(lst)
        hi = max(lst)
        if lo > hi:
            raise ParseError(f"Range lo > hi in '{text}' for {kind}")
        if lo < lo_bound or hi > hi_bound:
            raise ParseError(
                f"Range {lo}-{hi} out of bounds [{lo_bound},{hi_bound}] for {kind}"
            )
        return LstToken(kind, lst)
    else:
        raise ParseError(f"Invalid range '{text}' for {kind}")


def _parse_part(part: str) -> Token:
    """Parse one dot-separated segment into a Token."""
    low = part.lower()

    if low in Q_MONTHS:
        lo, hi = Q_MONTHS[low]
        return RangeToken("q", lo, hi)

    if low in MONTH_ALIASES:
        v = MONTH_ALIASES[low]
        return RangeToken("moy", v, v)

    if low in DOW_ALIASES:
        v = DOW_ALIASES[low]
        return RangeToken("dow", v, v)

    for prefix in TOKEN_RANGES.keys():
        if low.startswith(prefix):
            range_text = low[len(prefix) :]
            if not range_text:
                raise ParseError(f"Missing range after '{prefix}' in '{part}'")
            return parse_range(prefix, range_text)

    raise ParseError(f"Unrecognised token '{part}'")


def parse_spec(spec: str) -> ParsedPath:
    """Parse a spec string into an ordered tuple of Tokens (coarse → fine).
    Returns an empty tuple for a bare wildcard ("*"). A trailing ".*" leaf is
    stripped before parsing ("h19.*" == "h19")."""
    s = spec.strip()

    if s == "*":
        return ()

    parts = s.split(".")

    # Strip a trailing "*" leaf
    if parts[-1] == "*":
        parts = parts[:-1]

    if not parts:
        return ()

    tokens: list[Token] = []
    prev_token = None

    for part in parts:
        tok = _parse_part(part)
        if prev_token:
            allowed = TOKEN_ALLOWED_CHILDREN[prev_token.kind]
            if tok.kind not in allowed:
                raise ParseError(
                    f"'{part}' cannot follow '{prev_token.kind}' in spec '{spec}'"
                )
        tokens.append(tok)
        prev_token = tok

    return tuple(tokens)


def _flatten(
    node: Any, prefix: list[str], out: list[tuple[str, int]], value_cls: type
) -> None:
    """Recursively walk a nested dict, collecting (spec_string, int_value) pairs.
    A "*" key at any level does not contribute a path segment (leaf wildcard)."""
    if isinstance(node, value_cls):
        spec = ".".join(prefix) if prefix else "*"
        out.append((spec, node))
    elif isinstance(node, dict):
        for key, child in node.items():  # pyright: ignore[reportUnknownVariableType]
            if key == "*":
                _flatten(child, prefix, out, value_cls)  # "*" adds nothing to path
            else:
                _flatten(child, prefix + [key], out, value_cls)
    else:
        raise ValueError(
            f"Expected {value_cls.__name__} or dict, got {type(node).__name__} "
            f"at path '{'.'.join(prefix) or '*'}'"
        )


def _specificity(path: ParsedPath) -> tuple[int, int]:
    """(depth, max_rank) - longer paths win; ties broken by finest token rank.
    Empty path (wildcard) scores (0, 0)."""
    if not path:
        return (0, 0)
    return (len(path), max(TOKEN_SPECIFICITY[t.kind] for t in path))


def _matches_path(path: ParsedPath, dt: datetime) -> bool:
    """Return True if every token in the path matches the datetime."""
    if not path:
        return True  # wildcard

    _iso_year, iso_week, iso_dow = dt.isocalendar()
    doy = dt.timetuple().tm_yday

    for tok in path:
        if tok.kind in ("q", "moy"):
            if not tok.matches(dt.month):
                return False
        elif tok.kind == "woy":
            if not tok.matches(iso_week):
                return False
        elif tok.kind == "doy":
            if not tok.matches(doy):
                return False
        elif tok.kind == "dom":
            if not tok.matches(dt.day):
                return False
        elif tok.kind == "dow":
            if not tok.matches(iso_dow):
                return False
        elif tok.kind == "h":
            if not tok.matches(dt.hour):
                return False
        elif tok.kind == "m":
            if not tok.matches(dt.minute):
                return False
    return True


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class YearMinuteMap:
    """
    Parse and stash spec. Provide get_value() to resolve a datetime to an integer
    value using a hierarchical spec. Input may be a flat or nested dict, or a
    JSON string of either.

    Example::

        ymm = YearMinuteMap({
            "*": 8,
            "h5-10": 28,
            "h19": {
                "*": 18,
                "m30-59": 22,
            },
            "q2": {
                "h0-4": 10,
                "h5-10": 30,
            },
        })
        ymm.get_value(datetime(2024, 5, 1, 19, 45))  # -> 22

    Example::

        ymm = YearMinuteMap({"*": 7, "q1": 23, "q1.sun.h5.m30": 99})
        ymm.get_value(datetime(2024, 1, 7, 5, 30))   # -> 99

    """

    def __init__(self, spec: str | dict[str, Any], value_cls: type = int) -> None:
        if isinstance(value_cls, dict):
            raise ValueError("value_cls must not be dict")
        self.value_cls = value_cls
        if isinstance(spec, str):
            try:
                raw: Any = json.loads(spec)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}") from e
        else:
            raw = spec

        if not isinstance(raw, dict):
            raise ValueError("Spec must be a JSON object / dict")

        flat: list[tuple[str, int]] = []
        _flatten(raw, [], flat, value_cls)

        self._entries: list[tuple[ParsedPath, int]] = []
        for spec_str, value in flat:
            try:
                path = parse_spec(spec_str)
            except ParseError as e:
                raise ValueError(f"Invalid spec '{spec_str}': {e}") from e
            self._entries.append((path, value))

        self._entries.sort(key=lambda e: _specificity(e[0]), reverse=True)

    def get_value(self, dt: datetime) -> int | None:
        """Return the value of the most specific matching spec, or None."""
        for path, value in self._entries:
            if _matches_path(path, dt):
                return value
        return None

    def get_matching_spec(self, dt: datetime) -> str | None:
        """Return the canonical spec string that matched, or None."""
        for path, _value in self._entries:
            if _matches_path(path, dt):
                return _path_to_str(path)
        return None

    def __repr__(self) -> str:
        parts = ", ".join(f"{_path_to_str(p)!r}: {v}" for p, v in self._entries)
        return f"YearMinuteMap({{{parts}}})"


def _path_to_str(path: ParsedPath) -> str:
    """Canonical string reconstruction."""
    if not path:
        return "*"
    return ".".join([str(tok) for tok in path])


if __name__ == "__main__":
    """ Demo."""
    my_minute_map: dict[str, Any] = {
        "*": 8,
        "h5-10": 28,
        "h19": {
            "*": 18,
            "m30-59": 22,
        },
        "q2": {
            "h0-4": 10,
            "h5-10": 30,
            "h11-18": 10,
            "h19-23": 20,
        },
        "q3": {
            "h0-4": 12,
            "h5-10": 32,
            "h11-18": 12,
            "h19-23": 20,
            "sun": {
                "h0-4": 14,
                "h5-10": 34,
                "h11-18": 14,
                "h19-23": 23,
            },
        },
    }
    ymm = YearMinuteMap(my_minute_map)
    print(ymm)
    print()
    tests = [
        (datetime(2024, 1, 15, 3, 0), 8, "winter night → *"),
        (datetime(2024, 1, 15, 7, 0), 28, "winter morning h5-10"),
        (datetime(2024, 1, 15, 19, 0), 18, "h19.*"),
        (datetime(2024, 1, 15, 19, 45), 22, "h19.m30-59"),
        (datetime(2024, 5, 1, 2, 0), 10, "q2.h0-4"),
        (datetime(2024, 5, 1, 7, 0), 30, "q2.h5-10"),
        (datetime(2024, 8, 4, 7, 0), 34, "q3.sun.h5-10"),
        (datetime(2024, 8, 5, 7, 0), 32, "q3.mon.h5-10 (no sun override)"),
        (datetime(2024, 8, 4, 20, 0), 23, "q3.sun.h19-23"),
    ]
    for dt, expected, label in tests:
        got = ymm.get_value(dt)
        matched = ymm.get_matching_spec(dt)
        status = "✓" if got == expected else f"✗ (expected {expected})"
        print(
            f"  {status}  {dt.strftime('%Y-%m-%d %H:%M')}  → {got!s:3}  ({matched})  # {label}"
        )
