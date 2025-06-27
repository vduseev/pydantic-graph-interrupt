from dataclasses import dataclass, field
from pydantic_graph import BaseNode, GraphRunContext
from pydantic_graph_interrupt import InterruptibleGraph, PauseNode, Unset

@dataclass
class Approval:
    approver_name: str
    is_approved: bool
    comment: str | None = None

@dataclass
class State:
    case_id: str
    approvals: dict[str, Approval] = field(default_factory=dict)

@dataclass
class Start(BaseNode[State]):
    async def run(self, ctx: GraphRunContext) -> NewApproval:
        # Simulate email to approvers
        for approval in ctx.state.approvals:
            print(f'Hello {approval.name}. Your approval is required for case {ctx.state.case_id}')
        return NewApproval()

@dataclass
class NewApproval(PauseNode[State]):
    approver: str = Unset
    is_approved: bool = Unset

@dataclass
class NotifyRequestor(BaseNode[State]):
    async def run(self, ctx: GraphRunContext) -> End[None]:
        return End(None)

async def start_run():
    # Initialize the persistence
    persistence = FileStatePersistence('graph_state.json')
    state = MyState(approver='john.doe@example.com', case_id='123')
    await my_graph.initialize(Start(), persistence=persistence, state=state)

    # Run the graph until the first interruption
    result = await my_graph.resume(persistence=persistence)

    # We have encountered a node that needs data from outside of the
    # graph.
    if isinstance(result.pause_node, GetApproval):
        email_service.request_approval()

async def resume_after_first_interruption():
    # Simply resume from the last known state but add some new data
    # to the node that has interrupted the run
    persistence = FileStatePersistence('graph_state.json')
    node = GetData(external_data='some data')
    await my_graph.resume(persistence=persistence, from_node=node)

async def resume_after_second_interruption():
    # Again resume from the last known state but this time override
    # the state
    persistence = FileStatePersistence('graph_state.json')
    state 
    await my_graph.resume(persistence=persistence)
