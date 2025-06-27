import pytest

from pydantic_graph import SimpleStatePersistence, exceptions

from pydantic_graph_interrupt import InterruptibleGraph

from .fixtures import basic_graph, State, Greet, WaitForName


@pytest.mark.asyncio
async def test_resume_basic(basic_graph: InterruptibleGraph[State]):
    """Basic test."""
    
    persistence = SimpleStatePersistence()
    state = State()
    await basic_graph.initialize(Greet(), persistence=persistence, state=state)

    # First, start the graph from scratch. This will run
    # until it encounters the first interrupt node, which is
    # WaitForName in our case.
    result = await basic_graph.resume(persistence=persistence)

    # TEST: we have arrived at the correct interrupt node
    assert result.is_interrupted
    assert isinstance(result.interrupt_node, WaitForName)
    assert "Hello" in result.state.messages[0]

    # Simulate that we have received a user input from somewhere
    user_name = "Bobby"

    # Add required data to the interrupt node.
    from_node = WaitForName(user_name=user_name)

    # Resume the graph from the interrupt node.
    result = await basic_graph.resume(persistence=persistence, from_node=from_node)

    # TEST: we have arrived at the correct node
    assert result.is_finished
    assert result.state.user_name == user_name
    assert "Goodbye" in result.state.messages[1]


@pytest.mark.asyncio
async def test_resume_with_unset(basic_graph: InterruptibleGraph[State]):
    """Attempting to resume a graph with unset attributes in interrupt node
    must raise an error.
    """

    persistence = SimpleStatePersistence()
    state = State()
    await basic_graph.initialize(Greet(), persistence=persistence, state=state)

    # Run until first interrupt
    result = await basic_graph.resume(persistence=persistence)
    assert isinstance(result.interrupt_node, WaitForName)
    assert result.interrupt_node.unset_attrs == ['user_name']

    # Attempt to resume the graph from the interrupt node with unset attributes
    with pytest.raises(exceptions.GraphRuntimeError):
        await basic_graph.resume(persistence=persistence)
