import random
import time

from .cascade import (betweenness, greedy_celf, mean_reach, pick_seeds, sample_worlds,
                      spread_times, top_k)
from .graphs import make_graph

LABELS = {"none": "Do nothing", "random": "Random accounts", "degree": "Most-followed accounts",
          "betweenness": "Bridge accounts", "greedy": "Firebreak optimizer"}


def run(kind, n, seeds_count, seed_mode, p, budget, sims, seed):
    t0 = time.time()
    rng = random.Random(seed)
    adj = make_graph(kind, n, seed)
    seeds = pick_seeds(adj, seeds_count, seed_mode, rng)
    train = sample_worlds(adj, p, sims, seed + 1)   # used to choose the plan
    test = sample_worlds(adj, p, sims, seed + 2)    # held out, used for all scores
    skip = set(seeds)

    degree = [len(a) for a in adj]
    btw = betweenness(adj, 40, rng)
    pool = list(dict.fromkeys(top_k(degree, 50, skip) + top_k(btw, 50, skip)))
    sets = {
        "none": [],
        "random": rng.sample([i for i in range(n) if i not in skip], budget),
        "degree": top_k(degree, budget, skip),
        "betweenness": top_k(btw, budget, skip),
        "greedy": greedy_celf(train, seeds, pool, budget, n),
    }
    base = mean_reach(test, seeds, [], n)
    rows = []
    for key, chosen in sets.items():
        if key == "random":  # average several random draws so luck does not decide
            draws = [chosen] + [rng.sample([i for i in range(n) if i not in skip], budget) for _ in range(6)]
            value = sum(mean_reach(test, seeds, d, n) for d in draws) / len(draws)
        else:
            value = mean_reach(test, seeds, chosen, n)
        rows.append({"key": key, "label": LABELS[key], "inoculated": chosen,
                     "expected_reach": round(value, 1), "reach_pct": round(100 * value / n, 1),
                     "reduction_pct": round(100 * (base - value) / base, 1) if base else 0.0})

    order = sorted(range(len(test)), key=lambda i: mean_reach([test[i]], seeds, [], n))
    world = test[order[int(0.8 * (len(order) - 1))]]  # a typical bad-case run
    g = next(r for r in rows if r["key"] == "greedy")
    best_base = min((r for r in rows if r["key"] not in ("none", "greedy")), key=lambda r: r["reach_pct"])
    none_row = rows[0]
    summary = (f"Left alone, the rumor is expected to reach about {none_row['reach_pct']}% of the {n} accounts. "
               f"Inoculating just {len(g['inoculated'])} accounts chosen by the optimizer cuts that to "
               f"{g['reach_pct']}% ({g['reduction_pct']}% fewer people reached). The best simple rule "
               f"({best_base['label'].lower()}) reaches {best_base['reach_pct']}%, so the optimizer saves a further "
               f"{round(best_base['reach_pct'] - g['reach_pct'], 1)} percentage points. "
               f"Scores come from {sims} held-out simulated worlds.")
    return {
        "graph": {"n": n, "edges": [[u, v] for u in range(n) for v in adj[u] if u < v], "degree": degree},
        "seeds": seeds, "strategies": rows, "summary": summary,
        "cascade": {r["key"]: spread_times(world, seeds, r["inoculated"]) for r in rows},
        "params": {"kind": kind, "n": n, "p": p, "budget": budget, "sims": sims, "seed": seed},
        "seconds": round(time.time() - t0, 2),
    }
