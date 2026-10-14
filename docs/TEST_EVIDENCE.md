# Test evidence

## Run on 14 October 2026

Command from project root:

```powershell
python -m pytest -v --tb=short -p no:cacheprovider
```

Actual result: **110 collected; 28 failed; 82 setup errors**. The 28 pure availability tests reached unimplemented availability methods. The 82 database-dependent tests stopped in `seed.reset_db()` with `NotImplementedError`, before their test bodies ran. This is an initial contract-test run, not a passing implementation or completed acceptance demo.

The complete captured output follows below. No failures are skipped or marked as expected passes.

## Business-rule test mapping

| Rule | Implemented test examples |
|---|---|
| BR1 | `test_happy_path_and_audit` |
| BR2 | `test_seeded_availability`, `test_free_copies_order_and_deterministic_selection` |
| BR3 | `test_inclusive_overlap`, `test_clean_code_capacity`, `test_database_trigger_blocks_direct_overlap`, `test_database_trigger_blocks_copy_reassignment` |
| BR4 | `test_clean_code_capacity`, `test_design_patterns_capacity` |
| BR5 | `test_out_of_service_copy_never_free`, `test_damaged_design_patterns_copy_excluded`, `test_all_out_of_service_explanation` |
| BR6 | `test_happy_path_and_audit`, `test_cannot_issue_before_review` |
| BR7 | `test_reject_releases_last_copy`, `test_rejection_requires_reason`, `test_terminal_requests_cannot_reopen` |
| BR8 | `test_cancel_releases_copy`, `test_cannot_cancel_issued` |
| BR9 | `test_happy_path_and_audit`, `test_damaged_return_moves_future_reservation` |
| BR10 | `test_no_partial_fulfillment_or_alternative_title` |

Additional tests cover authorization, duplicate requests, inclusive issue boundaries, overdue copies, 30/31-day periods, unknown IDs, and rollback when audit insertion fails. Refused operations compare persisted requests, copies, and events before and after the attempt.

## Manual acceptance checks

All are **NOT RUN**. Update only after actually performing each scenario in Streamlit.

| Scenario | Result |
|---|---|
| Valid/invalid login and role-gated pages | NOT RUN |
| Catalog date selection and availability counts | NOT RUN |
| Asha requests Database System Concepts 05–12 Aug; approve; advance to 05 Aug; issue; return | NOT RUN |
| My Requests ownership, status, notes, and audit history | NOT RUN |
| Two Clean Code bookings for 02–03 Aug; third distinct member refused | NOT RUN |
| Design Patterns allocates DP-1, never damaged DP-2 | NOT RUN |
| Reject last available commitment; another member books released dates | NOT RUN |
| Cancel reservation; another member books released dates | NOT RUN |
| Damaged return moves future reservation or closes it with reason | NOT RUN |
| Past start, reversed dates, and 31-day period show clear errors without inserts | NOT RUN |
| Business-date override and demo-data reset | NOT RUN |

## Remaining validation

Re-run after P2/P3/P4 implementations land. Investigate each failure against the contracts. Confirm the suite passes on integrated main, then run the manual demo. Broader checklist cases still needing dedicated tests include approval-time stale-copy handling, availability exclusion of the current request, and next-free-date explanations. The bonus dashboard has not been implemented.

## Captured pytest output

```text
============================= test session starts =============================
platform win32 -- Python 3.13.15, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\Hackathon141026\Documents\lib-microsoft
configfile: pyproject.toml
testpaths: tests
plugins: anyio-4.15.1
collected 110 items

tests\test_availability.py FFFFFFFFFFFFFFFFFFFFFFFFFFFFEEEEEEEEEEEEEE    [ 38%]
tests\test_edge_cases.py EEEEEEEEEEEEEEEEEEEEEEEEEE                      [ 61%]
tests\test_lifecycle.py EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE       [100%]

=================================== ERRORS ====================================
____ ERROR at setup of test_seeded_availability[Clean Code-2-3-1-counts0] _____
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
____ ERROR at setup of test_seeded_availability[Clean Code-5-6-1-counts1] _____
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
_ ERROR at setup of test_seeded_availability[Introduction to Algorithms-5-7-1-counts2] _
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
__ ERROR at setup of test_seeded_availability[Design Patterns-5-7-1-counts3] __
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
_ ERROR at setup of test_seeded_availability[Artificial Intelligence: A Modern Approach-6-6-1-counts4] _
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
___ ERROR at setup of test_seeded_availability[Clean Code-10-11-10-counts5] ___
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
_______ ERROR at setup of test_out_of_service_copy_never_free[DAMAGED] ________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
_____ ERROR at setup of test_out_of_service_copy_never_free[UNDER_REPAIR] _____
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
_________ ERROR at setup of test_out_of_service_copy_never_free[LOST] _________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
____ ERROR at setup of test_out_of_service_copy_never_free[REFERENCE_ONLY] ____
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
______ ERROR at setup of test_out_of_service_copy_never_free[RESTRICTED] ______
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
____ ERROR at setup of test_free_copies_order_and_deterministic_selection _____
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
________ ERROR at setup of test_damaged_design_patterns_copy_excluded _________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
_ ERROR at setup of test_catalog_contains_all_seeded_titles_with_consistent_counts _
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
_________________ ERROR at setup of test_clean_code_capacity __________________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
_______________ ERROR at setup of test_design_patterns_capacity _______________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
__________ ERROR at setup of test_duplicate_active_request[pending] ___________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
__________ ERROR at setup of test_duplicate_active_request[reserved] __________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
___________ ERROR at setup of test_duplicate_active_request[issued] ___________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
____________ ERROR at setup of test_nonoverlapping_request_allowed ____________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
_____ ERROR at setup of test_terminal_request_allows_new_booking[reject] ______
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
_____ ERROR at setup of test_terminal_request_allows_new_booking[cancel] ______
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
_____ ERROR at setup of test_terminal_request_allows_new_booking[return] ______
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
___ ERROR at setup of test_database_trigger_blocks_direct_overlap[PENDING] ____
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
___ ERROR at setup of test_database_trigger_blocks_direct_overlap[RESERVED] ___
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
____ ERROR at setup of test_database_trigger_blocks_direct_overlap[ISSUED] ____
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
______ ERROR at setup of test_database_trigger_blocks_copy_reassignment _______
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
_______ ERROR at setup of test_damaged_return_moves_future_reservation ________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
_ ERROR at setup of test_unavailable_copy_closes_request_without_replacement[False-REJECTED] _
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
_ ERROR at setup of test_unavailable_copy_closes_request_without_replacement[True-CANCELLED] _
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
________ ERROR at setup of test_inventory_change_preserves_issued_loan ________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
_____________ ERROR at setup of test_repair_restores_availability _____________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
___________ ERROR at setup of test_overdue_copy_remains_unavailable ___________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
_ ERROR at setup of test_invalid_submission_has_no_side_effects[start0-end0-START_IN_PAST] _
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
_ ERROR at setup of test_invalid_submission_has_no_side_effects[start1-end1-INVALID_DATES] _
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
_ ERROR at setup of test_invalid_submission_has_no_side_effects[start2-end2-PERIOD_TOO_LONG] _
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
____________ ERROR at setup of test_thirty_day_submission_allowed _____________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
_____ ERROR at setup of test_no_partial_fulfillment_or_alternative_title ______
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
____________ ERROR at setup of test_all_out_of_service_explanation ____________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
________ ERROR at setup of test_submit_rolls_back_if_audit_write_fails ________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
_________________ ERROR at setup of test_happy_path_and_audit _________________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
______________ ERROR at setup of test_reject_releases_last_copy _______________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
_____________ ERROR at setup of test_rejection_requires_reason[] ______________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
____________ ERROR at setup of test_rejection_requires_reason[   ] ____________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
___________ ERROR at setup of test_rejection_requires_reason[\t\n] ____________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
__________ ERROR at setup of test_cancel_releases_copy[owner-False] ___________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
___________ ERROR at setup of test_cancel_releases_copy[owner-True] ___________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
________ ERROR at setup of test_cancel_releases_copy[librarian-False] _________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
_________ ERROR at setup of test_cancel_releases_copy[librarian-True] _________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
_________________ ERROR at setup of test_cannot_cancel_issued _________________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
______________ ERROR at setup of test_cannot_issue_before_review ______________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
______________ ERROR at setup of test_other_member_cannot_cancel ______________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
___ ERROR at setup of test_member_cannot_perform_librarian_action[approve] ____
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
____ ERROR at setup of test_member_cannot_perform_librarian_action[reject] ____
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
____ ERROR at setup of test_member_cannot_perform_librarian_action[issue] _____
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
____ ERROR at setup of test_member_cannot_perform_librarian_action[return] ____
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
__ ERROR at setup of test_member_cannot_perform_librarian_action[inventory] ___
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
________ ERROR at setup of test_librarian_cannot_submit_member_request ________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
_____________ ERROR at setup of test_issue_outside_dates[today0] ______________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
_____________ ERROR at setup of test_issue_outside_dates[today1] ______________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
_________ ERROR at setup of test_issue_on_inclusive_boundary[today0] __________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
_________ ERROR at setup of test_issue_on_inclusive_boundary[today1] __________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
___ ERROR at setup of test_terminal_requests_cannot_reopen[approve-reject] ____
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
___ ERROR at setup of test_terminal_requests_cannot_reopen[approve-cancel] ____
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
___ ERROR at setup of test_terminal_requests_cannot_reopen[approve-return] ____
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
____ ERROR at setup of test_terminal_requests_cannot_reopen[reject-reject] ____
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
____ ERROR at setup of test_terminal_requests_cannot_reopen[reject-cancel] ____
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
____ ERROR at setup of test_terminal_requests_cannot_reopen[reject-return] ____
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
____ ERROR at setup of test_terminal_requests_cannot_reopen[cancel-reject] ____
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
____ ERROR at setup of test_terminal_requests_cannot_reopen[cancel-cancel] ____
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
____ ERROR at setup of test_terminal_requests_cannot_reopen[cancel-return] ____
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
____ ERROR at setup of test_terminal_requests_cannot_reopen[issue-reject] _____
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
____ ERROR at setup of test_terminal_requests_cannot_reopen[issue-cancel] _____
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
____ ERROR at setup of test_terminal_requests_cannot_reopen[issue-return] _____
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
____ ERROR at setup of test_terminal_requests_cannot_reopen[return-reject] ____
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
____ ERROR at setup of test_terminal_requests_cannot_reopen[return-cancel] ____
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
____ ERROR at setup of test_terminal_requests_cannot_reopen[return-return] ____
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
_______________ ERROR at setup of test_unknown_request[approve] _______________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
_______________ ERROR at setup of test_unknown_request[reject] ________________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
_______________ ERROR at setup of test_unknown_request[cancel] ________________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
________________ ERROR at setup of test_unknown_request[issue] ________________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
_______________ ERROR at setup of test_unknown_request[return] ________________
tests\conftest.py:19: in fresh_db
    seed.reset_db()
src\lms\persistence\seed.py:47: in reset_db
    raise NotImplementedError
E   NotImplementedError
================================== FAILURES ===================================
__________ TestPureAvailability.test_inclusive_overlap[1-5-3-7-True] __________
tests\test_availability.py:36: in test_inclusive_overlap
    assert av.overlaps(*(D(2026, 8, n) for n in (s1, e1, s2, e2))) is expected
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src\lms\services\availability.py:29: in overlaps
    raise NotImplementedError
E   NotImplementedError
_________ TestPureAvailability.test_inclusive_overlap[1-10-3-5-True] __________
tests\test_availability.py:36: in test_inclusive_overlap
    assert av.overlaps(*(D(2026, 8, n) for n in (s1, e1, s2, e2))) is expected
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src\lms\services\availability.py:29: in overlaps
    raise NotImplementedError
E   NotImplementedError
_________ TestPureAvailability.test_inclusive_overlap[3-5-1-10-True] __________
tests\test_availability.py:36: in test_inclusive_overlap
    assert av.overlaps(*(D(2026, 8, n) for n in (s1, e1, s2, e2))) is expected
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src\lms\services\availability.py:29: in overlaps
    raise NotImplementedError
E   NotImplementedError
__________ TestPureAvailability.test_inclusive_overlap[2-4-2-4-True] __________
tests\test_availability.py:36: in test_inclusive_overlap
    assert av.overlaps(*(D(2026, 8, n) for n in (s1, e1, s2, e2))) is expected
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src\lms\services\availability.py:29: in overlaps
    raise NotImplementedError
E   NotImplementedError
__________ TestPureAvailability.test_inclusive_overlap[1-3-3-5-True] __________
tests\test_availability.py:36: in test_inclusive_overlap
    assert av.overlaps(*(D(2026, 8, n) for n in (s1, e1, s2, e2))) is expected
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src\lms\services\availability.py:29: in overlaps
    raise NotImplementedError
E   NotImplementedError
_________ TestPureAvailability.test_inclusive_overlap[1-3-4-6-False] __________
tests\test_availability.py:36: in test_inclusive_overlap
    assert av.overlaps(*(D(2026, 8, n) for n in (s1, e1, s2, e2))) is expected
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src\lms\services\availability.py:29: in overlaps
    raise NotImplementedError
E   NotImplementedError
_________ TestPureAvailability.test_inclusive_overlap[4-6-1-3-False] __________
tests\test_availability.py:36: in test_inclusive_overlap
    assert av.overlaps(*(D(2026, 8, n) for n in (s1, e1, s2, e2))) is expected
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src\lms\services\availability.py:29: in overlaps
    raise NotImplementedError
E   NotImplementedError
__________ TestPureAvailability.test_inclusive_overlap[3-3-3-3-True] __________
tests\test_availability.py:36: in test_inclusive_overlap
    assert av.overlaps(*(D(2026, 8, n) for n in (s1, e1, s2, e2))) is expected
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src\lms\services\availability.py:29: in overlaps
    raise NotImplementedError
E   NotImplementedError
_ TestPureAvailability.test_invalid_period[None-end0-INVALID_DATES-Please choose both a start and a return date.] _
tests\test_availability.py:51: in test_invalid_period
    av.validate_period(start, end, TODAY)
src\lms\services\availability.py:45: in validate_period
    raise NotImplementedError
E   NotImplementedError
_ TestPureAvailability.test_invalid_period[start1-None-INVALID_DATES-Please choose both a start and a return date.] _
tests\test_availability.py:51: in test_invalid_period
    av.validate_period(start, end, TODAY)
src\lms\services\availability.py:45: in validate_period
    raise NotImplementedError
E   NotImplementedError
_ TestPureAvailability.test_invalid_period[None-None-INVALID_DATES-Please choose both a start and a return date.] _
tests\test_availability.py:51: in test_invalid_period
    av.validate_period(start, end, TODAY)
src\lms\services\availability.py:45: in validate_period
    raise NotImplementedError
E   NotImplementedError
_ TestPureAvailability.test_invalid_period[start3-end3-INVALID_DATES-Return date must be on or after the start date.] _
tests\test_availability.py:51: in test_invalid_period
    av.validate_period(start, end, TODAY)
src\lms\services\availability.py:45: in validate_period
    raise NotImplementedError
E   NotImplementedError
_ TestPureAvailability.test_invalid_period[start4-end4-START_IN_PAST-Start date cannot be in the past (today is 01 Aug 2026).] _
tests\test_availability.py:51: in test_invalid_period
    av.validate_period(start, end, TODAY)
src\lms\services\availability.py:45: in validate_period
    raise NotImplementedError
E   NotImplementedError
_ TestPureAvailability.test_invalid_period[start5-end5-PERIOD_TOO_LONG-Borrowing period is 31 days; maximum is 30.] _
tests\test_availability.py:51: in test_invalid_period
    av.validate_period(start, end, TODAY)
src\lms\services\availability.py:45: in validate_period
    raise NotImplementedError
E   NotImplementedError
_____________ TestPureAvailability.test_valid_period[start0-end0] _____________
tests\test_availability.py:61: in test_valid_period
    assert av.validate_period(start, end, TODAY) is None
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src\lms\services\availability.py:45: in validate_period
    raise NotImplementedError
E   NotImplementedError
_____________ TestPureAvailability.test_valid_period[start1-end1] _____________
tests\test_availability.py:61: in test_valid_period
    assert av.validate_period(start, end, TODAY) is None
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src\lms\services\availability.py:45: in validate_period
    raise NotImplementedError
E   NotImplementedError
_____________ TestPureAvailability.test_valid_period[start2-end2] _____________
tests\test_availability.py:61: in test_valid_period
    assert av.validate_period(start, end, TODAY) is None
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src\lms\services\availability.py:45: in validate_period
    raise NotImplementedError
E   NotImplementedError
_ TestPureAvailability.test_validation_error_precedence[None-end0-INVALID_DATES] _
tests\test_availability.py:70: in test_validation_error_precedence
    av.validate_period(start, end, TODAY)
src\lms\services\availability.py:45: in validate_period
    raise NotImplementedError
E   NotImplementedError
_ TestPureAvailability.test_validation_error_precedence[start1-end1-INVALID_DATES] _
tests\test_availability.py:70: in test_validation_error_precedence
    av.validate_period(start, end, TODAY)
src\lms\services\availability.py:45: in validate_period
    raise NotImplementedError
E   NotImplementedError
_ TestPureAvailability.test_validation_error_precedence[start2-end2-START_IN_PAST] _
tests\test_availability.py:70: in test_validation_error_precedence
    av.validate_period(start, end, TODAY)
src\lms\services\availability.py:45: in validate_period
    raise NotImplementedError
E   NotImplementedError
______ TestPureAvailability.test_effective_end[ISSUED-today0-expected0] _______
tests\test_availability.py:86: in test_effective_end
    assert av.effective_end(request, today) == expected
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src\lms\services\availability.py:34: in effective_end
    raise NotImplementedError
E   NotImplementedError
______ TestPureAvailability.test_effective_end[ISSUED-today1-expected1] _______
tests\test_availability.py:86: in test_effective_end
    assert av.effective_end(request, today) == expected
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src\lms\services\availability.py:34: in effective_end
    raise NotImplementedError
E   NotImplementedError
______ TestPureAvailability.test_effective_end[ISSUED-today2-expected2] _______
tests\test_availability.py:86: in test_effective_end
    assert av.effective_end(request, today) == expected
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src\lms\services\availability.py:34: in effective_end
    raise NotImplementedError
E   NotImplementedError
______ TestPureAvailability.test_effective_end[PENDING-today3-expected3] ______
tests\test_availability.py:86: in test_effective_end
    assert av.effective_end(request, today) == expected
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src\lms\services\availability.py:34: in effective_end
    raise NotImplementedError
E   NotImplementedError
_____ TestPureAvailability.test_effective_end[RESERVED-today4-expected4] ______
tests\test_availability.py:86: in test_effective_end
    assert av.effective_end(request, today) == expected
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src\lms\services\availability.py:34: in effective_end
    raise NotImplementedError
E   NotImplementedError
_____ TestPureAvailability.test_effective_end[RETURNED-today5-expected5] ______
tests\test_availability.py:86: in test_effective_end
    assert av.effective_end(request, today) == expected
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src\lms\services\availability.py:34: in effective_end
    raise NotImplementedError
E   NotImplementedError
_____ TestPureAvailability.test_effective_end[REJECTED-today6-expected6] ______
tests\test_availability.py:86: in test_effective_end
    assert av.effective_end(request, today) == expected
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src\lms\services\availability.py:34: in effective_end
    raise NotImplementedError
E   NotImplementedError
_____ TestPureAvailability.test_effective_end[CANCELLED-today7-expected7] _____
tests\test_availability.py:86: in test_effective_end
    assert av.effective_end(request, today) == expected
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src\lms\services\availability.py:34: in effective_end
    raise NotImplementedError
E   NotImplementedError
=========================== short test summary info ===========================
FAILED tests/test_availability.py::TestPureAvailability::test_inclusive_overlap[1-5-3-7-True]
FAILED tests/test_availability.py::TestPureAvailability::test_inclusive_overlap[1-10-3-5-True]
FAILED tests/test_availability.py::TestPureAvailability::test_inclusive_overlap[3-5-1-10-True]
FAILED tests/test_availability.py::TestPureAvailability::test_inclusive_overlap[2-4-2-4-True]
FAILED tests/test_availability.py::TestPureAvailability::test_inclusive_overlap[1-3-3-5-True]
FAILED tests/test_availability.py::TestPureAvailability::test_inclusive_overlap[1-3-4-6-False]
FAILED tests/test_availability.py::TestPureAvailability::test_inclusive_overlap[4-6-1-3-False]
FAILED tests/test_availability.py::TestPureAvailability::test_inclusive_overlap[3-3-3-3-True]
FAILED tests/test_availability.py::TestPureAvailability::test_invalid_period[None-end0-INVALID_DATES-Please choose both a start and a return date.]
FAILED tests/test_availability.py::TestPureAvailability::test_invalid_period[start1-None-INVALID_DATES-Please choose both a start and a return date.]
FAILED tests/test_availability.py::TestPureAvailability::test_invalid_period[None-None-INVALID_DATES-Please choose both a start and a return date.]
FAILED tests/test_availability.py::TestPureAvailability::test_invalid_period[start3-end3-INVALID_DATES-Return date must be on or after the start date.]
FAILED tests/test_availability.py::TestPureAvailability::test_invalid_period[start4-end4-START_IN_PAST-Start date cannot be in the past (today is 01 Aug 2026).]
FAILED tests/test_availability.py::TestPureAvailability::test_invalid_period[start5-end5-PERIOD_TOO_LONG-Borrowing period is 31 days; maximum is 30.]
FAILED tests/test_availability.py::TestPureAvailability::test_valid_period[start0-end0]
FAILED tests/test_availability.py::TestPureAvailability::test_valid_period[start1-end1]
FAILED tests/test_availability.py::TestPureAvailability::test_valid_period[start2-end2]
FAILED tests/test_availability.py::TestPureAvailability::test_validation_error_precedence[None-end0-INVALID_DATES]
FAILED tests/test_availability.py::TestPureAvailability::test_validation_error_precedence[start1-end1-INVALID_DATES]
FAILED tests/test_availability.py::TestPureAvailability::test_validation_error_precedence[start2-end2-START_IN_PAST]
FAILED tests/test_availability.py::TestPureAvailability::test_effective_end[ISSUED-today0-expected0]
FAILED tests/test_availability.py::TestPureAvailability::test_effective_end[ISSUED-today1-expected1]
FAILED tests/test_availability.py::TestPureAvailability::test_effective_end[ISSUED-today2-expected2]
FAILED tests/test_availability.py::TestPureAvailability::test_effective_end[PENDING-today3-expected3]
FAILED tests/test_availability.py::TestPureAvailability::test_effective_end[RESERVED-today4-expected4]
FAILED tests/test_availability.py::TestPureAvailability::test_effective_end[RETURNED-today5-expected5]
FAILED tests/test_availability.py::TestPureAvailability::test_effective_end[REJECTED-today6-expected6]
FAILED tests/test_availability.py::TestPureAvailability::test_effective_end[CANCELLED-today7-expected7]
ERROR tests/test_availability.py::test_seeded_availability[Clean Code-2-3-1-counts0]
ERROR tests/test_availability.py::test_seeded_availability[Clean Code-5-6-1-counts1]
ERROR tests/test_availability.py::test_seeded_availability[Introduction to Algorithms-5-7-1-counts2]
ERROR tests/test_availability.py::test_seeded_availability[Design Patterns-5-7-1-counts3]
ERROR tests/test_availability.py::test_seeded_availability[Artificial Intelligence: A Modern Approach-6-6-1-counts4]
ERROR tests/test_availability.py::test_seeded_availability[Clean Code-10-11-10-counts5]
ERROR tests/test_availability.py::test_out_of_service_copy_never_free[DAMAGED]
ERROR tests/test_availability.py::test_out_of_service_copy_never_free[UNDER_REPAIR]
ERROR tests/test_availability.py::test_out_of_service_copy_never_free[LOST]
ERROR tests/test_availability.py::test_out_of_service_copy_never_free[REFERENCE_ONLY]
ERROR tests/test_availability.py::test_out_of_service_copy_never_free[RESTRICTED]
ERROR tests/test_availability.py::test_free_copies_order_and_deterministic_selection
ERROR tests/test_availability.py::test_damaged_design_patterns_copy_excluded
ERROR tests/test_availability.py::test_catalog_contains_all_seeded_titles_with_consistent_counts
ERROR tests/test_edge_cases.py::test_clean_code_capacity - NotImplementedError
ERROR tests/test_edge_cases.py::test_design_patterns_capacity - NotImplemente...
ERROR tests/test_edge_cases.py::test_duplicate_active_request[pending] - NotI...
ERROR tests/test_edge_cases.py::test_duplicate_active_request[reserved] - Not...
ERROR tests/test_edge_cases.py::test_duplicate_active_request[issued] - NotIm...
ERROR tests/test_edge_cases.py::test_nonoverlapping_request_allowed - NotImpl...
ERROR tests/test_edge_cases.py::test_terminal_request_allows_new_booking[reject]
ERROR tests/test_edge_cases.py::test_terminal_request_allows_new_booking[cancel]
ERROR tests/test_edge_cases.py::test_terminal_request_allows_new_booking[return]
ERROR tests/test_edge_cases.py::test_database_trigger_blocks_direct_overlap[PENDING]
ERROR tests/test_edge_cases.py::test_database_trigger_blocks_direct_overlap[RESERVED]
ERROR tests/test_edge_cases.py::test_database_trigger_blocks_direct_overlap[ISSUED]
ERROR tests/test_edge_cases.py::test_database_trigger_blocks_copy_reassignment
ERROR tests/test_edge_cases.py::test_damaged_return_moves_future_reservation
ERROR tests/test_edge_cases.py::test_unavailable_copy_closes_request_without_replacement[False-REJECTED]
ERROR tests/test_edge_cases.py::test_unavailable_copy_closes_request_without_replacement[True-CANCELLED]
ERROR tests/test_edge_cases.py::test_inventory_change_preserves_issued_loan
ERROR tests/test_edge_cases.py::test_repair_restores_availability - NotImplem...
ERROR tests/test_edge_cases.py::test_overdue_copy_remains_unavailable - NotIm...
ERROR tests/test_edge_cases.py::test_invalid_submission_has_no_side_effects[start0-end0-START_IN_PAST]
ERROR tests/test_edge_cases.py::test_invalid_submission_has_no_side_effects[start1-end1-INVALID_DATES]
ERROR tests/test_edge_cases.py::test_invalid_submission_has_no_side_effects[start2-end2-PERIOD_TOO_LONG]
ERROR tests/test_edge_cases.py::test_thirty_day_submission_allowed - NotImple...
ERROR tests/test_edge_cases.py::test_no_partial_fulfillment_or_alternative_title
ERROR tests/test_edge_cases.py::test_all_out_of_service_explanation - NotImpl...
ERROR tests/test_edge_cases.py::test_submit_rolls_back_if_audit_write_fails
ERROR tests/test_lifecycle.py::test_happy_path_and_audit - NotImplementedError
ERROR tests/test_lifecycle.py::test_reject_releases_last_copy - NotImplemente...
ERROR tests/test_lifecycle.py::test_rejection_requires_reason[] - NotImplemen...
ERROR tests/test_lifecycle.py::test_rejection_requires_reason[   ] - NotImple...
ERROR tests/test_lifecycle.py::test_rejection_requires_reason[\t\n] - NotImpl...
ERROR tests/test_lifecycle.py::test_cancel_releases_copy[owner-False] - NotIm...
ERROR tests/test_lifecycle.py::test_cancel_releases_copy[owner-True] - NotImp...
ERROR tests/test_lifecycle.py::test_cancel_releases_copy[librarian-False] - N...
ERROR tests/test_lifecycle.py::test_cancel_releases_copy[librarian-True] - No...
ERROR tests/test_lifecycle.py::test_cannot_cancel_issued - NotImplementedError
ERROR tests/test_lifecycle.py::test_cannot_issue_before_review - NotImplement...
ERROR tests/test_lifecycle.py::test_other_member_cannot_cancel - NotImplement...
ERROR tests/test_lifecycle.py::test_member_cannot_perform_librarian_action[approve]
ERROR tests/test_lifecycle.py::test_member_cannot_perform_librarian_action[reject]
ERROR tests/test_lifecycle.py::test_member_cannot_perform_librarian_action[issue]
ERROR tests/test_lifecycle.py::test_member_cannot_perform_librarian_action[return]
ERROR tests/test_lifecycle.py::test_member_cannot_perform_librarian_action[inventory]
ERROR tests/test_lifecycle.py::test_librarian_cannot_submit_member_request - ...
ERROR tests/test_lifecycle.py::test_issue_outside_dates[today0] - NotImplemen...
ERROR tests/test_lifecycle.py::test_issue_outside_dates[today1] - NotImplemen...
ERROR tests/test_lifecycle.py::test_issue_on_inclusive_boundary[today0] - Not...
ERROR tests/test_lifecycle.py::test_issue_on_inclusive_boundary[today1] - Not...
ERROR tests/test_lifecycle.py::test_terminal_requests_cannot_reopen[approve-reject]
ERROR tests/test_lifecycle.py::test_terminal_requests_cannot_reopen[approve-cancel]
ERROR tests/test_lifecycle.py::test_terminal_requests_cannot_reopen[approve-return]
ERROR tests/test_lifecycle.py::test_terminal_requests_cannot_reopen[reject-reject]
ERROR tests/test_lifecycle.py::test_terminal_requests_cannot_reopen[reject-cancel]
ERROR tests/test_lifecycle.py::test_terminal_requests_cannot_reopen[reject-return]
ERROR tests/test_lifecycle.py::test_terminal_requests_cannot_reopen[cancel-reject]
ERROR tests/test_lifecycle.py::test_terminal_requests_cannot_reopen[cancel-cancel]
ERROR tests/test_lifecycle.py::test_terminal_requests_cannot_reopen[cancel-return]
ERROR tests/test_lifecycle.py::test_terminal_requests_cannot_reopen[issue-reject]
ERROR tests/test_lifecycle.py::test_terminal_requests_cannot_reopen[issue-cancel]
ERROR tests/test_lifecycle.py::test_terminal_requests_cannot_reopen[issue-return]
ERROR tests/test_lifecycle.py::test_terminal_requests_cannot_reopen[return-reject]
ERROR tests/test_lifecycle.py::test_terminal_requests_cannot_reopen[return-cancel]
ERROR tests/test_lifecycle.py::test_terminal_requests_cannot_reopen[return-return]
ERROR tests/test_lifecycle.py::test_unknown_request[approve] - NotImplemented...
ERROR tests/test_lifecycle.py::test_unknown_request[reject] - NotImplementedE...
ERROR tests/test_lifecycle.py::test_unknown_request[cancel] - NotImplementedE...
ERROR tests/test_lifecycle.py::test_unknown_request[issue] - NotImplementedError
ERROR tests/test_lifecycle.py::test_unknown_request[return] - NotImplementedE...
======================== 28 failed, 82 errors in 0.54s ========================
```
