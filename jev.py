"""Jev Choice client: protocol, scripted fake, and TypeSafe wrapper."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ChoiceResult:
    choice: str
    confidence: float
    probabilities: dict[str, float]


@dataclass(frozen=True)
class ChooseCall:
    state: Any
    node_id: str
    instructions: str
    criteria: dict[str, str]


class JevClient(Protocol):
    def choose(
        self,
        state: Any,
        *,
        node_id: str,
        instructions: str,
        criteria: dict[str, str],
    ) -> ChoiceResult: ...


class ScriptedJevClient:
    def __init__(self, answers: dict[str, ChoiceResult]) -> None:
        self._answers = answers
        self.calls: list[ChooseCall] = []

    def choose(
        self,
        state: Any,
        *,
        node_id: str,
        instructions: str,
        criteria: dict[str, str],
    ) -> ChoiceResult:
        self.calls.append(
            ChooseCall(
                state=state,
                node_id=node_id,
                instructions=instructions,
                criteria=criteria,
            )
        )
        try:
            return self._answers[node_id]
        except KeyError:
            raise KeyError(node_id) from None


class TypeSafeJevClient:
    def __init__(self, model: str) -> None:
        self._model = model

    def choose(
        self,
        state: Any,
        *,
        node_id: str,
        instructions: str,
        criteria: dict[str, str],
    ) -> ChoiceResult:
        from typesafe_sdk import Choice, TypeSafeClient

        with TypeSafeClient() as client:
            response = client.system_one(
                state=state,
                questions={
                    node_id: Choice(instructions=instructions, criteria=criteria),
                },
                model=self._model,
            )
        answer = response.answers[node_id]
        return ChoiceResult(
            choice=str(answer.choice),
            confidence=float(answer.confidence),
            probabilities={k: float(v) for k, v in dict(answer.probabilities).items()},
        )
