"""Hand-written issue query language → Django Q (whitelisted only)."""

from __future__ import annotations

import re

from django.db.models import Q
from rest_framework.exceptions import ValidationError

FIELD_MAP = {
    "project": "project__key",
    "status": "workflow_status__key",
    "type": "issue_type__key",
    "assignee": "assignee__email",
    "priority": "priority",
    "label": "labels",
    "sprint": "sprint__name",
    "text": "title",
}

OPS = {"=", "!=", "~"}


TOKEN_RE = re.compile(
    r"""
    \s*
    (
        ORDER\s+BY|AND|OR|ASC|DESC|currentUser\(\)
        |[A-Za-z_][A-Za-z0-9_]*
        |!=|=|~
        |,(?=\s*[A-Za-z_])
        |"[^"]*"|'[^']*'
        |\(|\)
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


def tokenize(query: str) -> list[str]:
    tokens = []
    pos = 0
    q = query.strip()
    while pos < len(q):
        m = TOKEN_RE.match(q, pos)
        if not m:
            raise ValidationError(
                {
                    "detail": f"Unexpected token near: {q[pos:pos+20]!r}",
                    "code": "invalid_query",
                }
            )
        tok = m.group(1)
        tokens.append(tok)
        pos = m.end()
    return tokens


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] in "\"'" and value[-1] == value[0]:
        return value[1:-1]
    return value


def parse_query(query: str, *, current_user_email: str | None = None) -> tuple[Q, list[str]]:
    """Return (Q object, order_by fields). Rejects unknown fields and injection."""
    if not query or not query.strip():
        return Q(), []

    # Hard reject raw SQL fingerprints / injection attempts
    lowered = query.lower()
    if (
        "--" in lowered
        or ";" in lowered
        or " or 1=1" in lowered
        or "1=1" in lowered.replace(" ", "")
    ):
        raise ValidationError(
            {
                "detail": "Query contains disallowed syntax.",
                "code": "invalid_query",
            }
        )

    tokens = tokenize(query)
    order_by: list[str] = []
    if "ORDER" in " ".join(tokens).upper():
        # Split ORDER BY clause
        upper = [t.upper() if t.upper() in {"AND", "OR", "ORDER", "BY"} or t.upper().startswith("ORDER") else t for t in tokens]
        # Find ORDER BY index
        idx = None
        for i, t in enumerate(tokens):
            if t.upper().replace(" ", "") == "ORDERBY" or (
                t.upper() == "ORDER" and i + 1 < len(tokens) and tokens[i + 1].upper() == "BY"
            ):
                idx = i
                break
            if t.upper().startswith("ORDER") and "BY" in t.upper():
                idx = i
                break
        if idx is not None:
            # handle "ORDER BY" as two tokens
            if tokens[idx].upper() == "ORDER":
                rest = tokens[idx + 2 :]
            else:
                rest = tokens[idx + 1 :]
            tokens = tokens[:idx]
            i = 0
            while i < len(rest):
                field = rest[i]
                direction = ""
                if i + 1 < len(rest) and rest[i + 1].upper() in {"ASC", "DESC"}:
                    direction = rest[i + 1].upper()
                    i += 1
                mapped = FIELD_MAP.get(field.lower())
                if not mapped:
                    raise ValidationError(
                        {"detail": f"Unknown ORDER BY field: {field}", "code": "invalid_query"}
                    )
                order_by.append(("-" if direction == "DESC" else "") + mapped)
                i += 1
                if i < len(rest) and rest[i] == ",":
                    i += 1

    def parse_expr(ts: list[str]) -> Q:
        if not ts:
            return Q()
        # Split on OR (lowest precedence)
        parts = []
        buf = []
        depth = 0
        for t in ts:
            if t == "(":
                depth += 1
            elif t == ")":
                depth -= 1
            if t.upper() == "OR" and depth == 0:
                parts.append(buf)
                buf = []
            else:
                buf.append(t)
        parts.append(buf)
        q_acc = parse_and(parts[0])
        for p in parts[1:]:
            q_acc |= parse_and(p)
        return q_acc

    def parse_and(ts: list[str]) -> Q:
        parts = []
        buf = []
        depth = 0
        for t in ts:
            if t == "(":
                depth += 1
            elif t == ")":
                depth -= 1
            if t.upper() == "AND" and depth == 0:
                parts.append(buf)
                buf = []
            else:
                buf.append(t)
        parts.append(buf)
        q_acc = parse_clause(parts[0])
        for p in parts[1:]:
            q_acc &= parse_clause(p)
        return q_acc

    def parse_clause(ts: list[str]) -> Q:
        ts = [t for t in ts if t]
        if not ts:
            return Q()
        if ts[0] == "(" and ts[-1] == ")":
            return parse_expr(ts[1:-1])
        if len(ts) < 3:
            raise ValidationError(
                {"detail": f"Incomplete clause: {' '.join(ts)}", "code": "invalid_query"}
            )
        field, op, *rest = ts
        value = " ".join(rest)
        field_l = field.lower()
        if field_l not in FIELD_MAP:
            raise ValidationError(
                {"detail": f"Unknown field: {field}", "code": "invalid_query"}
            )
        if op not in OPS:
            raise ValidationError(
                {"detail": f"Unsupported operator: {op}", "code": "invalid_query"}
            )
        raw = _unquote(value)
        if raw.lower() == "currentuser()":
            raw = current_user_email or ""
        orm_field = FIELD_MAP[field_l]
        if field_l == "label":
            if op == "=":
                return Q(labels__contains=[raw])
            if op == "!=":
                return ~Q(labels__contains=[raw])
            raise ValidationError({"detail": "label only supports = and !=", "code": "invalid_query"})
        if field_l == "text" or op == "~":
            return Q(**{f"{orm_field}__icontains": raw})
        if op == "=":
            return Q(**{f"{orm_field}__iexact": raw})
        if op == "!=":
            return ~Q(**{f"{orm_field}__iexact": raw})
        raise ValidationError({"detail": "Unsupported clause", "code": "invalid_query"})

    return parse_expr(tokens), order_by
