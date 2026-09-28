import random

from fastapi.testclient import TestClient

from app.cascade import greedy_celf, mean_reach, sample_worlds, spread_times
from app.experiment import run
from app.graphs import make_graph
from app.main import app

client = TestClient(app)


def test_graphs_have_expected_size_and_no_self_loops():
    for kind in ("scale_free", "small_world", "communities"):
        adj = make_graph(kind, 120, 1)
        assert len(adj) == 120
        assert all(i not in a for i, a in enumerate(adj))
        assert sum(map(len, adj)) / 120 > 2  # not nearly empty


def test_blocking_a_node_never_increases_reach():
    adj = make_graph("scale_free", 100, 3)
    worlds = sample_worlds(adj, 0.3, 40, 5)
    base = mean_reach(worlds, [0], [], 100)
    hub = max(range(1, 100), key=lambda i: len(adj[i]))
    assert mean_reach(worlds, [0], [hub], 100) <= base


def test_greedy_beats_doing_nothing_on_training_worlds():
    adj = make_graph("communities", 120, 2)
    worlds = sample_worlds(adj, 0.25, 40, 9)
    plan = greedy_celf(worlds, [0], list(range(1, 120)), 5, 120)
    assert 0 < len(plan) <= 5 and 0 not in plan
    assert mean_reach(worlds, [0], plan, 120) < mean_reach(worlds, [0], [], 120)


def test_spread_times_respect_blocking():
    live = [[1], [0, 2], [1, 3], [2]]  # a path 0-1-2-3
    assert spread_times(live, [0], []) == [0, 1, 2, 3]
    assert spread_times(live, [0], [2]) == [0, 1, -1, -1]


def test_experiment_is_deterministic_and_optimizer_wins_held_out():
    a, b = run("scale_free", 120, 2, "random", 0.25, 6, 60, 11), run("scale_free", 120, 2, "random", 0.25, 6, 60, 11)
    assert a["strategies"] == b["strategies"]
    reach = {s["key"]: s["reach_pct"] for s in a["strategies"]}
    assert reach["greedy"] <= min(reach["random"], reach["none"])
    assert set(a["seeds"]).isdisjoint(a["strategies"][4]["inoculated"])


def test_api_and_validation():
    r = client.post("/api/simulate", json={"n": 80, "sims": 30, "budget": 4})
    assert r.status_code == 200
    body = r.json()
    assert len(body["strategies"]) == 5 and body["graph"]["n"] == 80
    assert len(body["cascade"]["none"]) == 80 and "Left alone" in body["summary"]
    assert client.post("/api/simulate", json={"n": 5000}).status_code == 422
    assert client.post("/api/simulate", json={"network": "bogus"}).status_code == 422
