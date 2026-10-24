"""CLI tests with exhaustive and independent Prim-based reference solvers."""

from __future__ import annotations

import itertools
import heapq
import random
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def optimum_by_enumeration(vertices: int, edges: list[tuple[int, int, int]]) -> int:
    best: int | None = None
    for candidate in itertools.combinations(edges, vertices - 1):
        parent = list(range(vertices))

        def find(vertex: int) -> int:
            while parent[vertex] != vertex:
                vertex = parent[vertex]
            return vertex

        for first, second, _ in candidate:
            parent[find(first)] = find(second)
        if len({find(vertex) for vertex in range(vertices)}) == 1:
            cost = sum(weight for _, _, weight in candidate)
            best = cost if best is None else min(best, cost)
    if best is None:
        raise ValueError("test graph is disconnected")
    return best


def optimum_by_prim(vertices: int, edges: list[tuple[int, int, int]]) -> int:
    adjacency: list[list[tuple[int, int]]] = [[] for _ in range(vertices)]
    for first, second, length in edges:
        adjacency[first].append((length, second))
        adjacency[second].append((length, first))
    visited = [False] * vertices
    frontier = [(0, 0)]
    total = 0
    reached = 0
    while frontier and reached < vertices:
        length, vertex = heapq.heappop(frontier)
        if visited[vertex]:
            continue
        visited[vertex] = True
        total += length
        reached += 1
        for next_length, neighbor in adjacency[vertex]:
            if not visited[neighbor]:
                heapq.heappush(frontier, (next_length, neighbor))
    if reached != vertices:
        raise ValueError("test graph is disconnected")
    return total


def selected_tree(output: str, vertices: int) -> tuple[int, list[tuple[int, int, int]]]:
    lines = output.strip().splitlines()
    assert lines and lines[0].startswith("TOTAL_LENGTH ")
    total = int(lines[0].split()[1])
    routes = []
    adjacency: list[list[int]] = [[] for _ in range(vertices)]
    for line in lines[1:]:
        label, first, second, length = line.split()
        assert label == "ROUTE"
        first, second, length = int(first), int(second), int(length)
        routes.append((first, second, length))
        adjacency[first].append(second)
        adjacency[second].append(first)
    assert len(routes) == vertices - 1
    assert sum(length for _, _, length in routes) == total
    seen = {0}
    pending = [0]
    while pending:
        for neighbor in adjacency[pending.pop()]:
            if neighbor not in seen:
                seen.add(neighbor)
                pending.append(neighbor)
    assert len(seen) == vertices
    return total, routes


class MstCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        build_dir = ROOT / "bin"
        build_dir.mkdir(exist_ok=True)
        cls.executable = build_dir / "mst_test.exe"
        build = subprocess.run(
            ["g++", "-std=c++17", "-O2", "-Wall", "-Wextra", "-pedantic",
             str(ROOT / "src/main.cpp"), str(ROOT / "src/mst.cpp"),
             "-o", str(cls.executable)],
            check=False,
            capture_output=True,
            text=True,
        )
        if build.returncode:
            raise RuntimeError(f"test executable build failed:\n{build.stderr}")

    def run_graph(self, vertices: int, edges: list[tuple[int, int, int]]) -> subprocess.CompletedProcess[str]:
        data = f"{vertices} {len(edges)}\n" + "".join(
            f"{first} {second} {length}\n" for first, second, length in edges
        )
        return subprocess.run(
            [str(self.executable)], input=data, text=True, capture_output=True,
            check=False,
        )

    def test_example_graph(self) -> None:
        data = (ROOT / "data/example.txt").read_text(encoding="utf-8")
        result = subprocess.run([str(self.executable)], input=data, text=True,
                                capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [
            "TOTAL_LENGTH 6", "ROUTE 1 2 1", "ROUTE 0 2 2", "ROUTE 1 3 3",
        ])

    def test_one_building_needs_no_cable(self) -> None:
        result = self.run_graph(1, [])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "TOTAL_LENGTH 0")

    def test_random_small_graphs_match_exhaustive_optimum(self) -> None:
        random_generator = random.Random(20261024)
        for vertices in range(2, 7):
            for _ in range(8):
                edges = [(index - 1, index, random_generator.randint(1, 20))
                         for index in range(1, vertices)]
                unused = [(u, v) for u in range(vertices)
                          for v in range(u + 1, vertices)
                          if (u, v) not in {(a, b) for a, b, _ in edges}]
                random_generator.shuffle(unused)
                for first, second in unused[: min(4, len(unused))]:
                    edges.append((first, second, random_generator.randint(1, 20)))
                expected = optimum_by_enumeration(vertices, edges)
                result = self.run_graph(vertices, edges)
                self.assertEqual(result.returncode, 0, result.stderr)
                lines = result.stdout.strip().splitlines()
                self.assertEqual(int(lines[0].split()[1]), expected)
                self.assertEqual(len(lines) - 1, vertices - 1)
                self.assertEqual(sum(int(line.split()[3]) for line in lines[1:]), expected)

    def test_disconnected_graph_fails(self) -> None:
        result = self.run_graph(3, [(0, 1, 2)])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("do not connect", result.stderr)

    def test_invalid_route_fails(self) -> None:
        for edges in [[(0, 2, 1)], [(0, 1, 0)], [(0, 0, 5)]]:
            with self.subTest(edges=edges):
                result = self.run_graph(2, edges)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("invalid", result.stderr)

    def test_parallel_routes_choose_cheapest(self) -> None:
        result = self.run_graph(2, [(0, 1, 9), (0, 1, 3)])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip().splitlines(),
                         ["TOTAL_LENGTH 3", "ROUTE 0 1 3"])

    def test_larger_example_with_billion_meter_values(self) -> None:
        data = (ROOT / "data/larger_example.txt").read_text(encoding="utf-8")
        result = subprocess.run([str(self.executable)], input=data, text=True,
                                capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        total, _ = selected_tree(result.stdout, 12)
        self.assertEqual(total, 11_000_000_066)

    def test_large_sparse_graph_has_known_optimum(self) -> None:
        vertices = 5000
        edges = [(index - 1, index, 1_000_000_000 + index)
                 for index in range(1, vertices)]
        edges += [(index, index + 2, 10_000_000_000 + index)
                  for index in range(vertices - 2)]
        result = self.run_graph(vertices, edges)
        self.assertEqual(result.returncode, 0, result.stderr)
        total, _ = selected_tree(result.stdout, vertices)
        expected = (vertices - 1) * 1_000_000_000 + vertices * (vertices - 1) // 2
        self.assertEqual(total, expected)

    def test_large_random_graph_matches_independent_prim(self) -> None:
        generator = random.Random(20261024)
        vertices = 800
        edges = [(index - 1, index, generator.randint(1, 1_000_000_000_000))
                 for index in range(1, vertices)]
        used = {(first, second) for first, second, _ in edges}
        while len(edges) < 16_000:
            first, second = sorted(generator.sample(range(vertices), 2))
            if (first, second) in used:
                continue
            used.add((first, second))
            edges.append((first, second, generator.randint(1, 1_000_000_000_000)))
        expected = optimum_by_prim(vertices, edges)
        result = self.run_graph(vertices, edges)
        self.assertEqual(result.returncode, 0, result.stderr)
        total, _ = selected_tree(result.stdout, vertices)
        self.assertEqual(total, expected)

    def test_large_equal_weight_graph(self) -> None:
        vertices = 150
        edges = [(first, second, 1) for first in range(vertices)
                 for second in range(first + 1, vertices)]
        result = self.run_graph(vertices, edges)
        self.assertEqual(result.returncode, 0, result.stderr)
        total, _ = selected_tree(result.stdout, vertices)
        self.assertEqual(total, vertices - 1)

    def test_total_length_overflow_is_rejected(self) -> None:
        result = self.run_graph(3, [(0, 1, 9_223_372_036_854_775_807), (1, 2, 1)])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exceeds 64-bit limit", result.stderr)


if __name__ == "__main__":
    unittest.main()
