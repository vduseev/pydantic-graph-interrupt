from dataclasses import dataclass, field

import pytest_asyncio
from pydantic_graph import BaseNode, End, GraphRunContext

from pydantic_graph_interrupt import InterruptibleGraph, InterruptNode, UNSET


@dataclass
class State:
    user_name: str | None = None
    messages: list[str] = field(default_factory=list)


@dataclass
class Greet(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State]) -> "WaitForName":
        ctx.state.messages.append("Hello, what is your name?")
        return WaitForName()


@dataclass
class WaitForName(InterruptNode[State]):
    user_name: str = UNSET

    async def run(self, ctx: GraphRunContext[State]) -> "Goodbye":
        ctx.state.user_name = self.user_name
        return Goodbye(user_name=self.user_name)


@dataclass
class Goodbye(BaseNode[State]):
    user_name: str

    async def run(self, ctx: GraphRunContext[State]) -> End:
        ctx.state.messages.append(f"Goodbye, {self.user_name}!")
        return End(ctx.state)


@pytest_asyncio.fixture
async def basic_graph() -> InterruptibleGraph[State]:
    return InterruptibleGraph(nodes=[Greet, WaitForName, Goodbye])
