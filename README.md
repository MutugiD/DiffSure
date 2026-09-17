# DiffSure

DiffSure is a deadline-aware service that turns a repository snapshot and a
change request into an independently verified unified diff. Candidate code is
never executed on the host: tests and derived checks run in the supplied
networkless, resource-limited multi-toolchain container.

The project is delivered documentation-first. Begin with the
[documentation index](documentation/README.md), then read the
[challenge context](documentation/context.md) and
[problem-to-solution map](documentation/problem-map.md).

## Status

The repository is in its documentation and delivery-foundation phase. The HTTP
service and solver are introduced only after the architecture and product
requirements have been accepted.

## Delivery policy

Work is delivered through one sequential pull request at a time. Pull request
titles and commit subjects begin with `task:` or `feat:`. Each pull request must
be green and free of unresolved blocking review before it is squash-merged to
`main`.

## Development

Python 3.12, `uv`, Git, Docker, and the supplied `acceptance:latest` image are
the intended toolchain. Detailed commands will be added with the application
bootstrap.

## License

DiffSure is available under the [MIT License](LICENSE).
