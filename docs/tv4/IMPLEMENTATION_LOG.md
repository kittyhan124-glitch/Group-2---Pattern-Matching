# TV4 implementation ledger

Plan: docs/tv4/IMPLEMENTATION_PLAN.md; scope: docs/tv4/SCOPE.md.
Base: 2ca31d9921b34c065af91d030a30c1befa8edb39; isolated existing clone, branch TV4-Tuan.

Task 1 complete: test_overlap_and_pid_contract failed because oracle missing, then passed after implementation. Full unittest discovery: 24 tests passed, including all 15 original test_kmp tests. No student algorithm changed.

Decisions: oracle preserves raw duplicate IDs; Unicode preparation deduplicates centrally and records mapping. Core-contract diagnostics remain separate from canonical-input validation. The missing oracle is a pending TV4 deliverable now provided, not evidence that a student algorithm failed its search task.

Task 2 complete: keyword-profile missing-module assertion RED, then full discovery GREEN at 32 tests before CSV work. Actual student algorithms compared against independent oracle for 10,000 cases each at seeds 11/29/47: zero canonical-search failures. Validator intentionally exits 1 because two raw contract issues and pending AC counters remain visible. Keyword profiling and hand-labelled line-presence fixture supplied; no toxicity labels invented.

Task 3 implementation: CSV-auditor missing-module assertion RED, then full discovery GREEN at 38 tests. A new length-prefix hash compatibility test exposed an 8-byte vs 4-byte serialization mismatch; fixed to TV2's 4-byte format and full discovery GREEN at 39 tests. TV2 common oracle/LineCollector: 1000 cases passed; formulas checked on 660 raw rows and derived pilot CSVs. Audit intentionally reports 80 checksum and 109 other integer export precision differences; machine subcommand on Windows reproduces os.getloadavg AttributeError. Owner source untouched. Documentation and provisional 1000-keyword profile added.
