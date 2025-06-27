import inspect
from contextlib import ExitStack
from dataclasses import dataclass
from typing import overload, Sequence

import logfire_api
from pydantic_graph import (
    Graph,
    End,
    BaseNode,
    GraphRun,
    GraphRunResult,
    exceptions,
    _utils,
)
from pydantic_graph.nodes import StateT, DepsT, RunEndT
from pydantic_graph.persistence import BaseStatePersistence
from pydantic_graph.persistence.in_mem import SimpleStatePersistence

from .nodes import InterruptNode


__all__ = 'InterruptibleGraph', 'GraphResumeResult'


@dataclass(init=False)
class GraphResumeResult(GraphRunResult[StateT, RunEndT]):
    """The result of resuming an interruptible graph.

    This is a subclass of `GraphRunResult` that adds a `interrupt_node`
    attribute. When the graph finishes its run and reaches an `End` node,
    the outcome is the same as a normal `GraphRunResult`.

    When the graph is interrupted by a `InterruptNode`, the outcome is slightly
    different. The `output` attribute is empty and the `interrupt_node` attribute
    is set to the `InterruptNode` that interrupted the execution.

    The returned `InterruptNode` is the next node to be executed when resuming
    the graph. Its `run` method has not been called yet.

    The `interrupt_node` and the `state` can be modified and passed back to
    the `resume` method and will overwrite the values in the persistence
    in that case.

    Attributes:
        state: The state of the graph at the end of the resume attempt.
        interrupt_node: The `InterruptNode` that interrupted the execution or
        ``None`` if the graph has finished its run.
        persistence: The persistence implementation that was used for
        this graph run.
        output: The data returned by the :pyclass:`End` node if the graph
        has finished its run.
        is_interrupted: Whether the graph was interrupted by a `InterruptNode`.
        is_finished: Whether the graph finished its run.
    """
    interrupt_node: InterruptNode[StateT, DepsT, RunEndT] | None

    def __init__(
        self,
        *,
        state: StateT,
        persistence: BaseStatePersistence[StateT, RunEndT],
        output: RunEndT | None = None,
        interrupt_node: InterruptNode[StateT, DepsT, RunEndT] | None = None,
        traceparent: str | None = None,
    ) -> None:
        super().__init__(
            output=output,
            state=state,
            persistence=persistence,
            traceparent=traceparent,
        )
        self.interrupt_node = interrupt_node

    @property
    def is_interrupted(self) -> bool:  # noqa: D401
        """Return ``True`` if the graph execution was interrupted by
        a :class:`InterruptNode`."""

        return self.interrupt_node is not None

    @property
    def is_finished(self) -> bool:  # noqa: D401
        """Return ``True`` if the graph finished during this resume 
        attempt."""

        return self.interrupt_node is None


class InterruptibleGraph(Graph[StateT, DepsT, RunEndT]):
    """Graph that interrupts its run when a `InterruptNode` is encountered
    and can be resumed from the same point.

    This is a subclass of `Graph` and can be used in the same way but adds
    the `resume` method.

    In `pydantic-graph`, a graph is a collection of nodes that can be run
    in sequence. The nodes define their outgoing edges — e.g. which nodes
    may be run next, and thereby the structure of the graph.

    See `resume` method for an example of running an interruptible graph.
    """
    def __init__(
        self,
        *,
        nodes: Sequence[type[BaseNode[StateT, DepsT, RunEndT]]],
        name: str | None = None,
        state_type: type[StateT] | _utils.Unset = _utils.UNSET,
        run_end_type: type[RunEndT] | _utils.Unset = _utils.UNSET,
        auto_instrument: bool = True,
    ):
        """Create an interruptible graph from a sequence of nodes.

        Interruptible graph is a subclass of `Graph` that will interrupt its
        execution when an `InterruptNode` is encountered and can then
        `resume()` from the same point.

        Args:
            nodes: The nodes which make up the graph, nodes need to be
                unique and all be generic in the same state type.
            name: Optional name for the graph, if not provided the name
                will be inferred from the calling frame on the first call
                to a graph method.
            state_type: The type of the state for the graph, this can
                generally be inferred from `nodes`.
            run_end_type: The type of the result of running the graph, this
                can generally be inferred from `nodes`.
            auto_instrument: Whether to create a span for the graph run and
                the execution of each node's run method.
        """
        super().__init__(
            nodes=nodes,
            name=name,
            state_type=state_type,
            run_end_type=run_end_type,
            auto_instrument=auto_instrument,
        )

    @overload
    async def resume(
        self,
        *,
        persistence: BaseStatePersistence[StateT, RunEndT],
        from_node: BaseNode[StateT, DepsT, RunEndT] | InterruptNode[StateT, DepsT, RunEndT] | None = ...,  # noqa: D401
        state: StateT | None = ...,  # noqa: D401
        deps: DepsT | None = ...,  # noqa: D401
        infer_name: bool = ...,  # noqa: D401
    ) -> GraphResumeResult[StateT, RunEndT]:
        ...

    @overload
    async def resume(
        self,
        *,
        persistence: BaseStatePersistence[StateT, RunEndT] | None = ...,  # noqa: D401
        from_node: BaseNode[StateT, DepsT, RunEndT] | InterruptNode[StateT, DepsT, RunEndT] = ...,  # noqa: D401
        state: StateT | None = ...,  # noqa: D401
        deps: DepsT | None = ...,  # noqa: D401
        infer_name: bool = ...,  # noqa: D401
    ) -> GraphResumeResult[StateT, RunEndT]:
        ...

    async def resume(
        self,
        persistence: BaseStatePersistence[StateT, RunEndT] | None = None,
        from_node: BaseNode[StateT, DepsT, RunEndT] | InterruptNode[StateT, DepsT, RunEndT] | None = None,
        state: StateT | None = None,
        deps: DepsT | None = None,
        infer_name: bool = True,
    ) -> GraphResumeResult[StateT, RunEndT]:
        """Run the graph from the start, the last known state, or from a
        given node until it ends or reaches a `InterruptNode`.

        The `resume` method can be used to both start and continue the
        interruptible graph run.
        
        If `persistence` is used, the :pyfunc:`Graph.initialize` method must
        be called just once before the beginning the graph run to initialize
        the persistence.

        Args:
            persistence: The state persistence interface to use.
            from_node: Node to resume the graph from. Overrides the node
                from the persistence snapshot.
            state: The state of the graph to resume from. Overrides the
                state from the persistence snapshot.
            deps: The dependencies of the graph.
            infer_name: Whether to infer the graph name from the calling
                frame.

        Returns:
            `GraphResumeResult` with the result of the resume attempt.
        """
        if infer_name and self.name is None:
            self._infer_name(inspect.currentframe())

        if persistence is None and from_node is None:
            raise exceptions.GraphRuntimeError('Either `persistence` or `from_node` must be provided.')

        start_node = from_node
        if persistence:
            snapshot = await persistence.load_next()
            if snapshot is None:
                raise exceptions.GraphRuntimeError('Unable to restore snapshot from state persistence.')
            start_node = from_node or snapshot.node
            state = state or snapshot.state
            start_node.set_snapshot_id(snapshot.id)

        # Validate that interruption node has been fully populated.
        if isinstance(start_node, InterruptNode):
            unset_attrs = start_node.unset_attrs
            if unset_attrs:
                raise exceptions.GraphRuntimeError(
                    "Cannot resume graph from InterruptNode "
                    f"{start_node.__class__.__name__} because of unset "
                    f"attributes: {', '.join(unset_attrs)}"
                )

        async with self.iter(
            start_node=start_node,
            persistence=persistence,
            state=state,
            deps=deps,
        ) as graph_run:
            done = False
            while not done:
                next_node = await graph_run.next(graph_run.next_node)
                if isinstance(next_node, InterruptNode):
                    return GraphResumeResult(
                        state=graph_run.state,
                        persistence=persistence,
                        interrupt_node=next_node,
                        traceparent=graph_run._traceparent(required=False),
                    )
                elif isinstance(next_node, End):
                    done = True

        # Graph has reached an end node.
        result = graph_run.result
        assert result is not None, 'Complete graph run should have a result'
        return GraphResumeResult(
            state=result.state,
            persistence=persistence,
            output=result.output,
            traceparent=graph_run._traceparent(required=False),
        )
