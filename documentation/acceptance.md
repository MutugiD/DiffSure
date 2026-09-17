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

## Sandbox controls

Each repository or derived check is sent to a new `acceptance:latest`
container as a gzip tar stream. Candidate content is never imported or
executed by the service process. Containers run with networking disabled, a
read-only root filesystem, UID/GID 65534, writable size-bounded tmpfs mounts,
two CPUs, 1 GiB of memory, a 512-process ceiling, and both inner and outer
timeouts. Output is bounded before it becomes evidence.

The repository suite is exactly `bash run_tests.sh`. Derived check files are
extracted under `/work/checks`, outside `/work/repo`, so they cannot become
part of a candidate diff. The independent test designer receives the task and
repository inventory before candidate generation; it never receives candidate
source or a candidate patch.

Exit and runtime failures remain distinct in evidence: a failed assertion is a
candidate failure, unavailable Docker infrastructure is an infrastructure
failure, and deadline termination is a timeout. Only observed passes count.

Continuous integration builds the public multi-toolchain image and exercises
Python, JavaScript, Bash, Go, C, Rust, and Java probes through the same Docker
runner used by the service.

## Release gate

The public release target is seven accepted public tasks at concurrency three,
with zero pre-execution rejections, missed deadlines, and null diffs. Live-model
results remain distinct from deterministic continuous-integration fixtures.

## Private boundary

Reviewer-only tasks, reference patches, and acceptance suites are excluded from
development, prompts, tests, and reports.
