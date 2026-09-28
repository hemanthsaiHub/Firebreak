"""Independent-cascade rumor spreading + inoculation strategies.

Key idea: sample many 'live-edge worlds' once (each edge is live with
probability p). Every strategy is then evaluated on identical worlds, which
removes Monte-Carlo noise from comparisons. Plans are optimised on TRAIN worlds
and scored on separate held-out TEST worlds, so results are not overfitted.
"""
import heapq
import random


def sample_worlds(adj, p, sims, seed):
    rng = random.Random(seed)
    n = len(adj)
    edges = [(u, v) for u in range(n) for v in adj[u] if u < v]
    worlds = []
    for _ in range(sims):
        live = [[] for _ in range(n)]
        for u, v in edges:
            if rng.random() < p:
                live[u].append(v)
                live[v].append(u)
        worlds.append(live)
    return worlds


def reach(live, seeds, blocked):
    seen = bytearray(len(live))
    stack = []
    for s in seeds:
        seen[s] = 1
        stack.append(s)
    count = len(stack)
    while stack:
        u = stack.pop()
        for v in live[u]:
            if not seen[v] and not blocked[v]:
                seen[v] = 1
                count += 1
                stack.append(v)
    return count


def mean_reach(worlds, seeds, blocked_nodes, n):
    blocked = bytearray(n)
    for b in blocked_nodes:
        blocked[b] = 1
    return sum(reach(w, seeds, blocked) for w in worlds) / len(worlds)


def spread_times(live, seeds, blocked_nodes):
    """Step at which each account hears the rumor (-1 = never)."""
    n = len(live)
    blocked = bytearray(n)
    for b in blocked_nodes:
        blocked[b] = 1
    times = [-1] * n
    frontier = list(seeds)
    for s in frontier:
        times[s] = 0
    step = 0
    while frontier:
        step += 1
        nxt = []
        for u in frontier:
            for v in live[u]:
                if times[v] < 0 and not blocked[v]:
                    times[v] = step
                    nxt.append(v)
        frontier = nxt
    return times


def betweenness(adj, samples, rng):
    """Approximate betweenness centrality (Brandes, sampled sources)."""
    n = len(adj)
    score = [0.0] * n
    for s in rng.sample(range(n), min(samples, n)):
        dist, sigma, preds, order = [-1] * n, [0] * n, [[] for _ in range(n)], []
        dist[s], sigma[s] = 0, 1
        queue = [s]
        for u in queue:
            order.append(u)
            for v in adj[u]:
                if dist[v] < 0:
                    dist[v] = dist[u] + 1
                    queue.append(v)
                if dist[v] == dist[u] + 1:
                    sigma[v] += sigma[u]
                    preds[v].append(u)
        delta = [0.0] * n
        for w in reversed(order):
            for u in preds[w]:
                delta[u] += sigma[u] / sigma[w] * (1 + delta[w])
            if w != s:
                score[w] += delta[w]
    return score


def top_k(scores, k, exclude):
    return [i for i in sorted(range(len(scores)), key=lambda i: -scores[i]) if i not in exclude][:k]


def greedy_celf(worlds, seeds, candidates, k, n):
    """Lazy-greedy (CELF) choice of accounts whose inoculation cuts reach most."""
    chosen, cur = [], mean_reach(worlds, seeds, [], n)
    heap = [(-(cur - mean_reach(worlds, seeds, [c], n)), c, 0) for c in candidates]
    heapq.heapify(heap)
    while heap and len(chosen) < k:
        neg, c, stamp = heapq.heappop(heap)
        if stamp == len(chosen):
            if -neg <= 1e-9:
                break
            chosen.append(c)
            cur -= -neg
        else:
            gain = cur - mean_reach(worlds, seeds, chosen + [c], n)
            heapq.heappush(heap, (-gain, c, len(chosen)))
    return chosen


def pick_seeds(adj, count, mode, rng):
    n = len(adj)
    if mode == "influencer":
        return sorted(range(n), key=lambda i: -len(adj[i]))[:count]
    return rng.sample(range(n), count)
