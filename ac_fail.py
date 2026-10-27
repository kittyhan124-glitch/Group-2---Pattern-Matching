"""ac_fail.py
----------
Bản tương thích ngược (Backward compatibility).
Trỏ trực tiếp đến mô-đun chính: aho_corasick.py
"""

from aho_corasick import (
    AhoCorasickFail,
    AhoCorasick,
    MatchResult,
    KeywordItem,
    State,
    build,
    scan
)

__all__ = [
    "AhoCorasickFail",
    "AhoCorasick",
    "MatchResult",
    "KeywordItem",
    "State",
    "build",
    "scan"
]
