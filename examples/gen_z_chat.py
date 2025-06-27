from dataclasses import dataclass, field

from pydantic_ai import Agent, format_as_xml
from pydantic_ai.messages import ModelMessage
from pydantic_graph import Graph, BaseNode, End, GraphRunContext
from pydantic_graph_interrupt import PauseNode, Unset


chatbot = Agent(
    model="gpt-4o-mini",
    system_prompt="You are a Gen-Z chatbot.",
)


@dataclass
class State:
    messages: list[ModelMessage] = field(default_factory=list)


@dataclass
class Greet(BaseNode[State]):
    async def run(
        self,
        ctx: GraphRunContext[State]
    ) -> GetUserReply:
        result = await chatbot.run(
            "Greet the user with a typical Gen-Z greeting.",
            message_history=ctx.state.messages,
        )

        # Greet the user in the terminal
        print(f"> {result.output}")

        ctx.state.messages += result.new_messages()
        return GetUserReply()


@dataclass
class GetUserReply(PauseNode[State]):
    user_input: str = Unset

    async def run(
        self,
        ctx: GraphRunContext[State]
    ) -> Reply:
        ctx.state.messages.append(ModelMessage(role="user", content=self.user_input))
        return Reply(user_input=self.user_input)


@dataclass
class Reply(BaseNode[State]):
    user_input: str

    async def run(
        self,
        ctx: GraphRunContext[State]
    ) -> GetUserReply | End:
        if self.user_input.strip().lower() in ["quit", "exit", "bye"]:
            return End(ctx.state)
        
        result = await chatbot.run(
            "Reply to the user's input in a Gen-Z way.",
            message_history=ctx.state.messages,
        )

        print(f"> {result.output}")

        ctx.state.messages += result.new_messages()
        return GetUserReply()


graph = Graph(nodes=[Greet, GetUserReply, Reply])
