# Problem-to-Solution Map

| Problem | Product response | Required evidence |
| --- | --- | --- |
| Hidden acceptance tests | Derive checks independently from the task and repository tests | Check source, command, and observed outcome |
| Binary scoring | Deliver only after a clean-copy gate passes | Static, apply, repository, and derived-check results |
| Multiple languages | Use the supplied multi-toolchain image and root test wrapper | Per-toolchain container fixtures |
| Hostile repository content | Treat files as data and expose only bounded tools | Tool transcript and path-policy tests |
| Hostile generated code | Execute only in a disposable networkless container | Sandbox controls and resource measurements |
| Malformed archives | Validate size, type, paths, and extracted shape | Adversarial archive test corpus |
| Model errors | Normalize tool calls, validate output, and fail closed | Protocol errors and null-diff responses |
| Candidate overfitting | Design checks before candidate source is visible | Test-design provenance |
| Weak first attempt | Generate a second lineage or repair when budget permits | Candidate lineage and evidence ranking |
| Deadline pressure | Use monotonic cutoffs and a protected response reserve | Phase timing ledger |
| Diff rejection | Mirror every public pre-execution rule | Exact static and clean-apply checks |
| Service concurrency | Isolate workspaces, budgets, and provider capacity | Three-request integration run |
| Cost uncertainty | Record tokens, provider, model, and estimated cost | Per-request usage report |
