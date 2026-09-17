# Requirement Traceability

| Requirement group | Delivery PR | Primary evidence |
| --- | --- | --- |
| FR-01, configuration | Python service bootstrap | Health contract and container smoke tests |
| FR-02–FR-04, FR-09 | Solve request ingestion | Schema, adversarial archive, budget, and diff-rule tests |
| FR-05–FR-06, FR-15 | Model providers and repository tools | Fake-provider, protocol, record, redaction, and usage tests |
| FR-07, FR-10 | Isolated verification | Sandbox controls and seven-toolchain fixtures |
| FR-08, FR-11–FR-12 | Diversification and repair | Candidate lineage, cutoff, repair, and ranking scenarios |
| FR-13–FR-14 | Verified patch workflow | Fresh-snapshot gate and harness-compatible response tests |
| FR-16 | Concurrent service operation | Three-request isolation and shutdown tests |
| Packaging and release | Operational delivery and release PRs | Image smoke, SBOM, vulnerability, and public harness reports |

## Acceptance scenario catalogue

- Valid request with verified diff.
- Valid request with no viable candidate and timely null response.
- Malformed JSON, base64, gzip, tar, and repository root.
- Traversal, links, devices, excessive entries, depth, and expanded bytes.
- Diff with CRLF, binary content, symlink mode, restricted path, oversize,
  empty content, or failed clean apply.
- Missing or failing `run_tests.sh`.
- Derived check absent, failing, timing out, or leaking into the diff.
- Provider unavailable, malformed turn, invalid tool, timeout, and cancellation.
- First candidate repaired, second candidate selected, and earlier viable
  candidate preserved under deadline pressure.
- Container infrastructure failure, resource breach, and output truncation.
- Three concurrent solves with independent success, failure, and timeout.
