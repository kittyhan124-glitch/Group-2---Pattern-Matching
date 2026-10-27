# TV4 implementation ledger

Plan: docs/tv4/IMPLEMENTATION_PLAN.md; scope: docs/tv4/SCOPE.md.
Base: 2ca31d9921b34c065af91d030a30c1befa8edb39; isolated existing clone, branch TV4-Tuan.

Task 1 complete: test_overlap_and_pid_contract failed because oracle missing, then passed after implementation. Full unittest discovery: 24 tests passed, including all 15 original test_kmp tests. No student algorithm changed.

Decisions: oracle preserves raw duplicate IDs; Unicode preparation deduplicates centrally and records mapping. Core-contract diagnostics remain separate from canonical-input validation. The missing oracle is a pending TV4 deliverable now provided, not evidence that a student algorithm failed its search task.

Task 2 complete: keyword-profile missing-module assertion RED, then full discovery GREEN at 32 tests before CSV work. Actual student algorithms compared against independent oracle for 10,000 cases each at seeds 11/29/47: zero canonical-search failures. Validator intentionally exits 1 because two raw contract issues and pending AC counters remain visible. Keyword profiling and hand-labelled line-presence fixture supplied; no toxicity labels invented.

Task 3 implementation: CSV-auditor missing-module assertion RED, then full discovery GREEN at 38 tests. A new length-prefix hash compatibility test exposed an 8-byte vs 4-byte serialization mismatch; fixed to TV2's 4-byte format and full discovery GREEN at 39 tests. TV2 common oracle/LineCollector: 1000 cases passed; formulas checked on 660 raw rows and derived pilot CSVs. Audit intentionally reports 80 checksum and 109 other integer export precision differences; machine subcommand on Windows reproduces os.getloadavg AttributeError. Owner source untouched. Documentation and provisional 1000-keyword profile added.

Final independent review of base..935f149: three important reporting/audit defects and one replay-mode finding. Regraded replay-mode loss to important because a TV4 failure must be reproducible in the same counted/normal mode. Added regressions before fixes: missing AC and invalid line hits must still produce reports; invalid raw numeric cells must not abort CSV reporting; timeout source cannot become successful zero measurements; counted shrinking retains execution mode. All reproduced failures then passed. Also pinned empty T4 seed versus TV2's `na` label and blank measured values to prevent false findings or false acceptance. Full discovery after fix pass: 47 passed, 0 failures/errors.

Review boundaries upheld: no official-corpus performance or toxicity claim; unsubmitted work assessed only by visible artifacts; AC instrumentation remains pending; pilot figures are not research conclusions. These were already the scope constraints, not waived requirements. No deferred minor findings remain.

Final verification: fresh 47/47 unit tests; regenerated 30,000 fuzz input reports (seeds 11/29/47) and verified every recorded source hash against delivered files; zero canonical failures, three explicitly open owner issues per seed. Regenerated TV2 audit: 1000 oracle/collector cases passed and only the 80 checksum/109 other integer export cells remain. Original member algorithm files have no diff from origin/main. Full logs and quality_gate.json saved in reports/.

Publication: pushed the implementation to origin/TV4-Tuan, keeping main and tv2-benchmark unchanged. The user requested branch delivery, so no merge or pull request was created. The original configured Git identity was retained. Task 3 complete for supplied inputs; later official-corpus/keyword validation remains a dependency already recorded in the scope and progress assessment.
