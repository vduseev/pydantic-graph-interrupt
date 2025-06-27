# pedantic-graph-interrupt

Run interruptible Pydantic Graphs that can be paused and resumed.

## Table of Contents

* [Use cases](#use-cases)
* [Installation](#installation)
* [Concepts](#concepts)
* [Usage](#usage)
  * [Define graph with pause nodes](#define-graph-with-pause-nodes)
  * [Initialize persistence once](#initialize-persistence-once)

## Use cases

* LLM AI chatbots implemented using [pydantic-ai] that need to obtain user
  input outside of the graph.
* Document processing workflows where an external approval or human
  involvement is required.
* Graphs that can run for a very long time, so their execution must be
  broken into smaller continuous chunks. Most often each chunk is executed
  in a background worker, when the graph is ready to resume its run.

## Installation

```bash
pip install pydantic-graph-interrupt
```

## Concepts

* `InterruptNode` is a special node type that interrupts the graph execution.
* `resume()` is an alternative to `graph.run()`. It can be used to both start
  the graph run from scratch or resume it after an interruption.

## Usage

### Define graph with interrupt nodes

```python

```

### Initialize persistence once

When you just start, you have to initialize the persistence once. This
defines the starting node of the graph and sets correct types inside
the persistence.

```python
from pathlib import Path

from pydantic_graph import End
from pydantic_graph.persistence.file import FileStatePersistence

async def start():
    persistence = FileStatePersistence(Path("offline_state.json"))


    # Start the graph from scratch
    await resume(graph, Start(), persistence=persistence)
```

[State Persistence]: https://ai.pydantic.dev/graph/#state-persistence
[pydantic-ai]: https://ai.pydantic.dev/
