"""Synthetic social-network generators (pure Python, undirected)."""
import random


def _finish(n, edges):
    adj = [set() for _ in range(n)]
    for u, v in edges:
        if u != v:
            adj[u].add(v)
            adj[v].add(u)
    return [sorted(a) for a in adj]


def scale_free(n, rng, m=3):
    """Barabasi-Albert: a few huge 'influencer' hubs, many small accounts."""
    targets, repeated, edges = set(range(m)), [], []
    for new in range(m, n):
        for t in targets:
            edges.append((new, t))
        repeated.extend(targets)
        repeated.extend([new] * m)
        targets = set()
        while len(targets) < m:
            targets.add(rng.choice(repeated))
    return _finish(n, edges)


def small_world(n, rng, k=6, beta=0.08):
    """Watts-Strogatz: tight friend groups with a few long-range links."""
    edges = []
    for i in range(n):
        for j in range(1, k // 2 + 1):
            v = (i + j) % n
            if rng.random() < beta:
                v = rng.randrange(n)
            edges.append((i, v))
    return _finish(n, edges)


def communities(n, rng, blocks=4, mean_in=6.0, mean_out=0.8):
    """Stochastic block model: dense echo chambers, few bridges between them."""
    size = n / blocks
    group = [min(int(i / size), blocks - 1) for i in range(n)]
    p_in, p_out = min(1.0, mean_in / size), min(1.0, mean_out / (n - size))
    edges = [(u, v) for u in range(n) for v in range(u + 1, n)
             if rng.random() < (p_in if group[u] == group[v] else p_out)]
    return _finish(n, edges)


KINDS = {"scale_free": scale_free, "small_world": small_world, "communities": communities}


def make_graph(kind, n, seed):
    return KINDS[kind](n, random.Random(seed))
