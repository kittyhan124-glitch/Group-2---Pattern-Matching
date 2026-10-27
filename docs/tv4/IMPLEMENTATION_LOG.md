# TV4 implementation ledger

Plan: docs/tv4/IMPLEMENTATION_PLAN.md; scope: docs/tv4/SCOPE.md.
Base: 2ca31d9921b34c065af91d030a30c1befa8edb39; isolated existing clone, branch TV4-Tuan.

Task 1 complete: test_overlap_and_pid_contract failed because oracle missing, then passed after implementation. Full unittest discovery: 24 tests passed, including all 15 original test_kmp tests. No student algorithm changed.

Decisions: oracle preserves raw duplicate IDs; Unicode preparation deduplicates centrally and records mapping. Core-contract diagnostics remain separate from canonical-input validation. The missing oracle is a pending TV4 deliverable now provided, not evidence that a student algorithm failed its search task.
