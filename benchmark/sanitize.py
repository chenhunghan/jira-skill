#!/usr/bin/env python3
"""Sanitize a raw Jira capture into a size-preserving, committable fixture.

Design goals:
  - Deterministic (seeded) so re-runs produce identical fixtures.
  - Size-preserving for free text so byte and approximate-token counts stay
    faithful to the real payload.
  - Stable cross-reference: same real accountId / displayName / issue key
    maps to the same synthetic value throughout the fixture.

Modes (auto-detected by file extension):
  .json  - walks the structure; replaces free-text fields, user objects,
           URLs, UUIDs, emails, and issue keys.
  other  - text mode; regex-only replacement for URLs, UUIDs, emails,
           issue keys, plus blocklist substitution.

Usage:
  python3 sanitize.py <input> <output> [--blocklist <path>]
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path

LOREM = (
    "lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod "
    "tempor incididunt ut labore et dolore magna aliqua enim ad minim veniam "
    "quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo "
    "consequat duis aute irure dolor in reprehenderit voluptate velit esse "
    "cillum dolore eu fugiat nulla pariatur excepteur sint occaecat cupidatat "
    "non proident sunt in culpa qui officia deserunt mollit anim id est laborum"
)
LOREM_WORDS = LOREM.split()

URL_RE = re.compile(r"https?://[^\s<>\"'\\)\]]+")
UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
EMAIL_RE = re.compile(r"\b[\w.+%-]+@[\w.-]+\.[A-Za-z]{2,}\b")
ISSUE_KEY_RE = re.compile(r"\b[A-Z][A-Z0-9_]{1,15}-\d+\b")
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

FREE_TEXT_KEYS = {"summary", "description", "body", "environment"}
USER_CONTAINER_KEYS = {
    "assignee",
    "reporter",
    "creator",
    "author",
    "user",
    "updateAuthor",
}
# Numeric identifiers that leak tenant-specific ordering. Values (string
# or int) are remapped to stable monotonic synthetics.
NUMERIC_ID_KEYS = {"id", "avatarId"}
KEEP_NAME_PARENTS = {
    "status",
    "issuetype",
    "priority",
    "resolution",
    "statusCategory",
}

# Parents where a `name` value is free text that should be lorem-replaced.
SCRUB_NAME_PARENTS = {
    "project",
    "projectCategory",
    "component",
    "components",
    "label",
    "labels",
    "version",
    "fixVersions",
}


class Sanitizer:
    def __init__(self, blocklist: list[str], seed: int = 42):
        self.rng = random.Random(seed)
        self.blocklist = [t for t in blocklist if t]
        self.account_map: dict[str, str] = {}
        self.user_map: dict[str, str] = {}
        self.email_map: dict[str, str] = {}
        self.uuid_map: dict[str, str] = {}
        self.prefix_map: dict[str, str] = {}
        self.numeric_id_map: dict[str, str] = {}

    def lorem(self, n: int) -> str:
        if n <= 0:
            return ""
        parts: list[str] = []
        total = 0
        while total < n:
            w = self.rng.choice(LOREM_WORDS)
            add = (1 if parts else 0) + len(w)
            if total + add > n:
                break
            parts.append(w)
            total += add
        s = " ".join(parts)
        if len(s) < n:
            s += " " + self.rng.choice(LOREM_WORDS)
        return s[:n]

    def _pad(self, s: str, n: int) -> str:
        if len(s) == n:
            return s
        if len(s) < n:
            return s + " " + self.lorem(max(0, n - len(s) - 1))
        return s[:n]

    def account_id(self, real: str) -> str:
        if real not in self.account_map:
            idx = len(self.account_map) + 1
            self.account_map[real] = self._pad(f"acc-{idx}", len(real))
        return self.account_map[real]

    def display_name(self, real: str) -> str:
        if real not in self.user_map:
            idx = len(self.user_map) + 1
            self.user_map[real] = self._pad(f"User {idx}", max(6, len(real)))
        return self.user_map[real]

    def email(self, real: str) -> str:
        if real not in self.email_map:
            idx = len(self.email_map) + 1
            self.email_map[real] = self._pad(f"user{idx}@example.com", len(real))
        return self.email_map[real]

    def numeric_id(self, real: str) -> str:
        if real not in self.numeric_id_map:
            self.numeric_id_map[real] = str(1000 + len(self.numeric_id_map))
        return self.numeric_id_map[real]

    def cloud_uuid(self, real: str) -> str:
        if real not in self.uuid_map:
            n = len(self.uuid_map)
            self.uuid_map[real] = (
                f"{n:08x}-0000-0000-0000-{n:012x}"
            )
        return self.uuid_map[real]

    def _issue_key_sub(self, m: re.Match) -> str:
        whole = m.group(0)
        prefix, _, num = whole.partition("-")
        if prefix not in self.prefix_map:
            idx = len(self.prefix_map)
            self.prefix_map[prefix] = "BENCH" if idx == 0 else f"BENCH{idx + 1}"
        new = f"{self.prefix_map[prefix]}-{num}"
        return self._pad(new, len(whole))

    def _url_sub(self, m: re.Match) -> str:
        orig = m.group(0)
        return self._pad("https://example.atlassian.net/x", len(orig))

    def _blocklist_sub(self, s: str) -> str:
        for term in self.blocklist:
            pat = re.compile(re.escape(term), re.IGNORECASE)
            s = pat.sub(lambda m, t=term: self.lorem(len(m.group(0))), s)
        return s

    def scrub_string(self, s: str) -> str:
        s = ISSUE_KEY_RE.sub(self._issue_key_sub, s)
        s = URL_RE.sub(self._url_sub, s)
        s = EMAIL_RE.sub(lambda m: self.email(m.group(0)), s)
        s = UUID_RE.sub(lambda m: self.cloud_uuid(m.group(0)), s)
        s = self._blocklist_sub(s)
        return s

    def _user_object(self, node: dict) -> dict:
        out: dict = {}
        for k, v in node.items():
            if isinstance(v, str) and k == "accountId":
                out[k] = self.account_id(v)
            elif isinstance(v, str) and k in {"displayName", "key"}:
                out[k] = self.display_name(v)
            elif isinstance(v, str) and k == "name":
                out[k] = self.display_name(v)
            elif isinstance(v, str) and k == "emailAddress":
                out[k] = self.email(v)
            elif k == "timeZone" and isinstance(v, str):
                out[k] = self._pad("UTC", len(v))
            elif isinstance(v, str) and k == "self":
                out[k] = self._pad(
                    "https://example.atlassian.net/rest/api/3/user?accountId=acc",
                    len(v),
                )
            elif k == "avatarUrls" and isinstance(v, dict):
                out[k] = {
                    sz: self._pad("https://example.atlassian.net/avatar.png", len(url))
                    if isinstance(url, str)
                    else url
                    for sz, url in v.items()
                }
            else:
                out[k] = self.walk(v, k, "user")
        return out

    def walk(self, node, key: str | None = None, parent_key: str | None = None):
        if isinstance(node, dict):
            if node.get("type") == "text" and isinstance(node.get("text"), str):
                rebuilt = {
                    k: self.walk(v, k, "text") for k, v in node.items() if k != "text"
                }
                rebuilt["text"] = self.lorem(len(node["text"]))
                return rebuilt
            if key in USER_CONTAINER_KEYS or parent_key in USER_CONTAINER_KEYS:
                return self._user_object(node)
            return {k: self.walk(v, k, key) for k, v in node.items()}
        if isinstance(node, list):
            return [self.walk(v, key, parent_key) for v in node]
        if isinstance(node, str):
            if key in NUMERIC_ID_KEYS and node.isdigit():
                return self.numeric_id(node)
            if key in FREE_TEXT_KEYS and parent_key != "text":
                return self.lorem(len(node))
            if key and key.startswith("customfield_"):
                return self.lorem(len(node))
            if key == "name" and parent_key in KEEP_NAME_PARENTS:
                return node
            if key == "name" and parent_key in SCRUB_NAME_PARENTS:
                return self.lorem(len(node))
            return self.scrub_string(node)
        if isinstance(node, int) and not isinstance(node, bool):
            if key in NUMERIC_ID_KEYS:
                return int(self.numeric_id(str(node)))
        return node


def load_blocklist(path: Path | None) -> list[str]:
    if not path or not path.exists():
        return []
    return [
        line.strip()
        for line in path.read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def sanitize_json(raw: str, s: Sanitizer) -> str:
    data = json.loads(raw)
    out = s.walk(data)
    return json.dumps(out, ensure_ascii=False, separators=(",", ":"))


ACLI_LABEL_RE = re.compile(r"^([A-Za-z][A-Za-z ]*?):\s?(.*)$")
ACLI_KEEP_VALUE_LABELS = {"Type", "Status", "Key"}
ACLI_LOREM_VALUE_LABELS = {"Summary"}
ACLI_DESCRIPTION_LABEL = "Description"


def _sanitize_acli_view(raw: str, s: Sanitizer) -> str:
    """Structured handler for `acli jira workitem view` output.

    Layout is a sequence of `Label: value` lines ending with a
    `Description:` label whose body extends to EOF. We lorem-replace
    the Summary value and the entire Description body; Key goes through
    the standard issue-key remap; Assignee goes through email scrubbing;
    Type and Status values are preserved (they are workflow-generic).
    """
    lines = raw.splitlines()
    out: list[str] = []
    in_description = False

    for line in lines:
        if in_description:
            out.append(s.lorem(len(line)))
            continue

        m = ACLI_LABEL_RE.match(line)
        if not m:
            out.append(s.scrub_string(line))
            continue

        label, value = m.group(1), m.group(2)
        prefix_len = len(line) - len(value)
        prefix = line[:prefix_len]

        if label == ACLI_DESCRIPTION_LABEL:
            out.append(prefix + s.lorem(len(value)))
            in_description = True
        elif label in ACLI_LOREM_VALUE_LABELS:
            out.append(prefix + s.lorem(len(value)))
        elif label in ACLI_KEEP_VALUE_LABELS:
            out.append(prefix + s.scrub_string(value))
        else:
            out.append(prefix + s.scrub_string(value))

    trailing = "\n" if raw.endswith("\n") else ""
    return "\n".join(out) + trailing


TABLE_LOREM_COLUMNS = {"summary", "description"}


def _sanitize_acli_table(raw: str, s: Sanitizer) -> str | None:
    """Handle acli table output with box-drawing separators.

    Columns whose header matches `summary` or `description` have their
    cell contents lorem-replaced (preserving padding). Other cells go
    through string-level scrubbing so URLs, keys, emails, and blocklist
    terms are cleaned.
    """
    sep = "│" if "│" in raw else ("|" if "|" in raw else None)
    if sep is None:
        return None

    lines = raw.splitlines()
    header_line = None
    for line in lines:
        if line.startswith(sep):
            cells = line.split(sep)
            if any(
                cell.strip() and any(c.isalpha() for c in cell) for cell in cells[1:-1]
            ):
                header_line = line
                break
    if header_line is None:
        return None

    sep_positions = [i for i, c in enumerate(header_line) if c == sep]
    if len(sep_positions) < 2:
        return None

    cells: list[tuple[int, int, str]] = []
    for i in range(len(sep_positions) - 1):
        start = sep_positions[i] + 1
        end = sep_positions[i + 1]
        name = header_line[start:end].strip()
        cells.append((start, end, name))

    lorem_cols = [
        i for i, (_, _, name) in enumerate(cells)
        if name.lower() in TABLE_LOREM_COLUMNS
    ]

    out_lines: list[str] = []
    last_end = cells[-1][1]
    for line in lines:
        if (
            line.startswith(sep)
            and len(line) >= last_end
            and line is not header_line
            and any(c.isalnum() for c in line)
            and lorem_cols
        ):
            chars = list(line)
            for col_idx in lorem_cols:
                start, end, _ = cells[col_idx]
                cell = line[start:end]
                stripped = cell.strip()
                if not stripped:
                    continue
                lead = len(cell) - len(cell.lstrip())
                trail = len(cell) - len(cell.rstrip())
                content_len = end - start - lead - trail
                if content_len <= 0:
                    continue
                replacement = s.lorem(content_len)
                for j, ch in enumerate(replacement):
                    chars[start + lead + j] = ch
            out_lines.append(s.scrub_string("".join(chars)))
        else:
            out_lines.append(s.scrub_string(line))

    trailing = "\n" if raw.endswith("\n") else ""
    return "\n".join(out_lines) + trailing


def sanitize_text(raw: str, s: Sanitizer) -> str:
    raw = ANSI_RE.sub("", raw)
    if re.match(r"^Key:\s", raw):
        return _sanitize_acli_view(raw, s)
    if raw.lstrip().startswith(("┌", "╭", "│", "+")):
        result = _sanitize_acli_table(raw, s)
        if result is not None:
            return result
    return s.scrub_string(raw)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--blocklist", default=None, type=Path)
    args = ap.parse_args()

    inp = Path(args.input)
    outp = Path(args.output)
    raw = inp.read_text()
    blocklist = load_blocklist(args.blocklist)
    s = Sanitizer(blocklist)

    if inp.suffix == ".json":
        result = sanitize_json(raw, s)
    else:
        result = sanitize_text(raw, s)

    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(result)
    print(
        f"sanitized {inp} -> {outp} "
        f"(raw={len(raw)}c, fixture={len(result)}c)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
