from __future__ import annotations as _annotations

from abc import abstractmethod
from typing import Any, Generic

from pydantic_graph import exceptions
from pydantic_graph.nodes import (
    BaseNode,
    End,
    NodeDef,
    StateT,
    DepsT,
    NodeRunEndT,
    GraphRunContext,
)


class BaseInterrupt(BaseNode, Generic[StateT, DepsT, NodeRunEndT]):
    """Base class for interruption nodes.

    Interrupt nodes should never have their run method called. They exist
    to allow us to stop the graph run traversal and transition to the next
    node manually.
    """

    @abstractmethod
    async def run(
        self, ctx: GraphRunContext[StateT, DepsT]
    ) -> BaseNode[StateT, DepsT, NodeRunEndT] | End[NodeRunEndT]:
        """Define the next node to transition to after the interruption.
        
        Treat this method as a type definition that has no business logic.

        The implementation of this method should never be called and must
        raise a NotImplementedError.

        The return type of this method is used to determine the next node
        to transition to after the interruption.

        Args:
            ctx: The graph context.

        Returns:
            Type hints which node to transition to after the interruption.
            Doesn't actually return anything. Always raises an error.

        Raises:
            NotImplementedError: This method should never be called.
        """
        ...

    @classmethod
    def get_node_def(cls, local_ns: dict[str, Any] | None) -> NodeDef[StateT, DepsT, NodeRunEndT]:
        """Custom node definition for interruption nodes.
        
        Interruption nodes can only transition to one base node.
        """
        node_def = super().get_node_def(local_ns)
        if len(node_def.next_node_edges) > 1:
            raise exceptions.GraphSetupError(
                f"Interruption node {cls} has more than one return type hint: {node_def.next_node_edges.keys()}"
            )
        return node_def
