# Minimum-Cable Campus Network (Greedy Problem)

## Problem and scope

A campus wants every building to be able to reach every other building through a new cable network while installing the least total cable. A planning survey supplies permitted interbuilding routes and the length of cable required for each route. This is motivated by real campus outside-plant backbone cabling and approved pathways; see [Yale's IT infrastructure design guidelines](https://facilities.yale.edu/sites/default/files/files/Design%20Standards/IT%20Infrastructure%20Design%20Guidelines%20and%20Performance%20Standards_Rev1_5.pdf), section 1.16. The university guidelines motivate the domain problem, not the algorithm.

The model assumes each route's cable length is independent, every building can pass traffic onward, all required buildings must be connected, and backup links are outside the objective. It does not claim that a physical campus should omit redundancy, use straight-line routes, or ignore permits and existing ducts.

## Graph abstraction and greedy solution

Let `V` be buildings and `E` be feasible undirected routes. Each route `e` has a positive length `w(e)` in meters. The input graph must be connected. Find a subset `T` that connects all buildings and minimizes `sum(w(e) for e in T)`. Since a positive-cost cycle can be removed without disconnecting buildings, an optimum is a minimum spanning tree (MST).

Kruskal's algorithm sorts routes by length and accepts a route only when it joins two currently disconnected groups of buildings. A disjoint-set structure detects cycles. Ties are broken deterministically by endpoints and input order.

**Correctness sketch.** Before each selection, some MST contains every route already selected. Let `e` be the next accepted route and let `C` be one component it joins. `e` is a minimum-weight route crossing the cut from `C` to the other buildings. If that MST lacks `e`, adding it creates a cycle containing another route `f` crossing the cut. Since `w(e) <= w(f)`, replacing `f` with `e` keeps a spanning tree of no greater cost. Repeating this argument yields an MST containing all selected routes.

Sorting costs `O(E log E)`; disjoint-set operations add `O(E alpha(V))`, so total time is `O(E log E)` and working space is `O(E + V)`. For a complete candidate graph, `E = Theta(V^2)` and the bound becomes `O(V^2 log V)`.

## Build and run

From the repository root in PowerShell, with `g++` and Python available:

```powershell
New-Item -ItemType Directory -Force greedy/bin | Out-Null
g++ -std=c++17 -O2 -Wall -Wextra -pedantic greedy/src/main.cpp greedy/src/mst.cpp -o greedy/bin/mst.exe
Get-Content greedy/data/example.txt | ./greedy/bin/mst.exe
```

Input begins with `building_count route_count`, then one `from to length` line per route. Buildings are numbered `0` through `building_count - 1`; lengths are positive integer meters. Parallel routes are allowed. The example's minimum total is `6` meters. The program reports an error if the route graph is disconnected or malformed. For a larger numeric stress fixture, run `Get-Content greedy/data/larger_example.txt | ./greedy/bin/mst.exe`; its expected total is `11000000066`.

## Tests and runtime experiment

```powershell
python -m unittest discover -s greedy/tests -v
g++ -std=c++17 -O2 -Wall -Wextra -pedantic greedy/experiments/benchmark.cpp greedy/src/mst.cpp -o greedy/bin/benchmark.exe
./greedy/bin/benchmark.exe greedy/experiments/results.csv
python -m pip install matplotlib numpy
python greedy/experiments/plot_results.py greedy/experiments/results.csv greedy/figures
```

The 11 tests compare small random graphs against exhaustive enumeration and a seeded 800-building, 16,000-route graph against an independent Prim implementation. Other cases include a 5,000-building sparse graph with a known optimum, a 150-building equal-weight graph, billion-meter synthetic weights, 64-bit overflow, malformed routes, disconnected routes, parallel routes, and a single building. The large lengths stress integer handling; they are not proposed cable routes for a real campus.

The benchmark uses fixed seeds and connected synthetic graphs, with `V` from 100 to 6400 and `E` equal to `2V`, `4V`, `8V`, or `16V`. It runs seven trials per graph family, repeats short runs within each trial, and times both Kruskal and an independent Prim implementation on the same graph. The CSV records 392 observations, including algorithm, graph size, seed, trial, runtime, and MST total. The plotting script writes four PDF and PNG figures plus `summary.txt`: an $E\log E$ fit, normalized runtime, a Kruskal-versus-Prim baseline, and scaling by route density. This experiment supports the asymptotic analysis; it is not a proof of optimality or a claim about real installation times.

## Report

The standalone IEEE-style report is `greedy_report.tex`. From the repository
root, compile it with `latexmk -pdf greedy/greedy_report.tex`.
