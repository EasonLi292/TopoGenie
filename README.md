# TopoGenie

TopoGenie is a minimal, MCTS-driven analog topology generator built around an Euler-trail formulation. It is organized as a small Python package:

- `topogenie.vocab` – token vocabulary and adjacency utilities
- `topogenie.euler_mcts` – EulerState representation and a simple PUCT search
- `topogenie.netlist_io` – heuristic/optional PySpice reward bridge

An example script demonstrating a short search lives in `examples/run_demo.py`:

```bash
python -m examples.run_demo
```

The script prints the sequence of actions chosen by MCTS along with a heuristic reward. If PySpice is installed, simple circuit simulation is attempted; otherwise a topology-based heuristic is used.
