"""Independent clean-copy delivery gate."""

from __future__ import annotations

from dataclasses import dataclass

from diffsure.archive import RepositoryWorkspace
from diffsure.budget import SolveBudget
from diffsure.config import Settings
from diffsure.git import apply_diff, static_diff_error
from diffsure.verification import CheckSpec, Evidence
from diffsure.verifier import CandidateVerifier


@dataclass(frozen=True, slots=True)
class DeliveryResult:
    passed: bool
    reason: str
    evidence: Evidence | None = None


class DeliveryGate:
    def __init__(
        self, settings: Settings, verifier: CandidateVerifier, budget: SolveBudget
    ) -> None:
        self.settings = settings
        self.verifier = verifier
        self.budget = budget

    def verify(
        self,
        encoded_repository: str,
        diff: bytes,
        derived_checks: tuple[CheckSpec, ...],
    ) -> DeliveryResult:
        static_error = static_diff_error(diff)
        if static_error is not None:
            return DeliveryResult(False, static_error)
        remaining = self.budget.remaining(self.budget.usable_cutoff)
        if remaining <= 0:
            return DeliveryResult(False, "delivery reserve reached")
        with RepositoryWorkspace(encoded_repository, self.settings) as clean:
            error = apply_diff(clean, diff, remaining)
            if error is not None:
                return DeliveryResult(False, error)
            evidence = self.verifier.verify(
                "delivery", clean, derived_checks, self.budget.usable_cutoff
            )
        if not evidence.viable:
            return DeliveryResult(False, "clean-copy verification failed", evidence)
        return DeliveryResult(True, "clean-copy verification passed", evidence)
