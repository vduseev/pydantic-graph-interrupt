from __future__ import annotations as _annotations

from dataclasses import fields, is_dataclass
from typing import Generic

from pydantic_graph import _utils
from pydantic_graph.nodes import (
    BaseNode,
    StateT,
    DepsT,
    NodeRunEndT,
)


UNSET = _utils.UNSET
"""Represents value that must be set.

Alias for `pydantic_graph._utils.UNSET`.
"""


class InterruptNode(BaseNode, Generic[StateT, DepsT, NodeRunEndT]):
    """Base class for interruption nodes.

    `InterruptNode` is a `BaseNode` that can interrupt the run of an
    `InterruptibleGraph`.

    When the `resume()` function runs the graph and reaches an
    `InterruptNode`, it returns `GraphResumeResult` with the
    `interrupt_node` that was supposed to be run next.

    Resuming the graph after the interruption will execute the interrupt
    node's `run` method to determine the next node to run.

    Attributes of the `InterruptNode` can have a default value of `UNSET`.
    This will enforce a runtime check in `resume()` when the graph continues
    from the interrupted node to make sure that all non-optional attributes
    are set.
    """

    @property
    def unset_attrs(self) -> list[str]:
        """Returns attributes which have `UNSET` as their value."""
        unset_attrs: list[str] = []

        if is_dataclass(self):
            # Dataclass: iterate over the declared fields.
            for f in fields(self):
                if getattr(self, f.name) is UNSET:
                    unset_attrs.append(f.name)
        else:
            # Fallback for non-dataclass: inspect ``__dict__``.
            unset_attrs = [
                name for name, value
                in vars(self).items()
                if value is UNSET
            ]

        return unset_attrs
