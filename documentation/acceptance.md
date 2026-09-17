# Acceptance Model

## Mandatory gates

A deliverable diff must pass, in order:

1. UTF-8, LF, size, binary, symlink, and path validation.
2. `git apply --check` against an untouched copy of the received snapshot.
3. The repository suite through `bash run_tests.sh` in the acceptance image.
4. At least one independently derived task check in the same sandbox.
5. A separate final gate that repeats application and all mandatory checks on a
   new untouched copy.

Any mandatory failure makes the candidate non-viable. Model confidence and
unexecuted reasoning never count as evidence.

## Release gate

The public release target is seven accepted public tasks at concurrency three,
with zero pre-execution rejections, missed deadlines, and null diffs. Live-model
results remain distinct from deterministic continuous-integration fixtures.

## Private boundary

Reviewer-only tasks, reference patches, and acceptance suites are excluded from
development, prompts, tests, and reports.
