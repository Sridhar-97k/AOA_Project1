#include "../src/mst.hpp"

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <functional>
#include <random>
#include <stdexcept>
#include <unordered_set>
#include <vector>
#include <queue>

namespace {

std::uint64_t route_key(int first, int second) {
    std::uint32_t first_id = static_cast<std::uint32_t>(first);
    std::uint32_t second_id = static_cast<std::uint32_t>(second);
    if (first_id > second_id) {
        std::swap(first_id, second_id);
    }
    return (static_cast<std::uint64_t>(first_id) << 32) | second_id;
}

std::vector<cabling::Edge> make_graph(int vertices, int edge_count,
                                     std::uint64_t seed) {
    std::mt19937_64 random(seed);
    std::uniform_int_distribution<int> vertex(0, vertices - 1);
    std::uniform_int_distribution<int> length(1, 1000000);
    std::unordered_set<std::uint64_t> used;
    used.reserve(static_cast<std::size_t>(edge_count * 2));
    std::vector<cabling::Edge> edges;
    edges.reserve(static_cast<std::size_t>(edge_count));

    // The chain guarantees that every generated graph is connected.
    for (int index = 1; index < vertices; ++index) {
        edges.push_back({index - 1, index, length(random), edges.size()});
        used.insert(route_key(index - 1, index));
    }
    while (static_cast<int>(edges.size()) < edge_count) {
        int first = vertex(random);
        int second = vertex(random);
        if (first == second || !used.insert(route_key(first, second)).second) {
            continue;
        }
        edges.push_back({first, second, length(random), edges.size()});
    }
    return edges;
}

int inner_repetitions(int vertices) {
    if (vertices <= 200) return 100;
    if (vertices <= 800) return 25;
    if (vertices <= 3200) return 8;
    return 3;
}

long long prim_total_length(int vertices,
                            const std::vector<cabling::Edge>& edges) {
    std::vector<std::vector<std::pair<int, int>>> adjacency(vertices);
    for (const cabling::Edge& edge : edges) {
        adjacency[edge.from].push_back({edge.length, edge.to});
        adjacency[edge.to].push_back({edge.length, edge.from});
    }

    using Candidate = std::pair<int, int>;
    std::priority_queue<Candidate, std::vector<Candidate>, std::greater<Candidate>> frontier;
    std::vector<bool> visited(vertices, false);
    frontier.push({0, 0});
    long long total = 0;
    int reached = 0;
    while (!frontier.empty() && reached < vertices) {
        const Candidate current = frontier.top();
        frontier.pop();
        const int length = current.first;
        const int vertex = current.second;
        if (visited[vertex]) {
            continue;
        }
        visited[vertex] = true;
        total += length;
        ++reached;
        for (const std::pair<int, int>& next : adjacency[vertex]) {
            if (!visited[next.second]) {
                frontier.push({next.first, next.second});
            }
        }
    }
    if (reached != vertices) {
        throw std::runtime_error("benchmark graph unexpectedly disconnected");
    }
    return total;
}

}  // namespace

int main(int argc, char** argv) {
    if (argc > 2) {
        std::cerr << "usage: benchmark [output.csv]\n";
        return 1;
    }
    std::ofstream file;
    std::ostream* output = &std::cout;
    if (argc == 2) {
        file.open(argv[1]);
        if (!file) {
            std::cerr << "cannot open benchmark output file\n";
            return 1;
        }
        output = &file;
    }
    const std::vector<int> vertex_counts{100, 200, 400, 800, 1600, 3200, 6400};
    const std::vector<int> density_factors{2, 4, 8, 16};
    constexpr int trials = 7;
    std::uint64_t checksum = 0;

    *output << "algorithm,vertices,edges,density_factor,seed,trial,elapsed_us,total_length\n";
    *output << std::fixed << std::setprecision(3);
    for (int vertices : vertex_counts) {
        for (int factor : density_factors) {
            const int edge_count = factor * vertices;
            const std::uint64_t seed = 20261024ULL +
                static_cast<std::uint64_t>(vertices * 100 + factor);
            const std::vector<cabling::Edge> edges =
                make_graph(vertices, edge_count, seed);
            const int repetitions = inner_repetitions(vertices);

            for (int trial = 0; trial < trials; ++trial) {
                const auto kruskal_start = std::chrono::steady_clock::now();
                long long kruskal_length = 0;
                for (int repeat = 0; repeat < repetitions; ++repeat) {
                    const cabling::MstResult result =
                        cabling::kruskal(vertices, edges);
                    kruskal_length = result.total_length;
                    checksum ^= static_cast<std::uint64_t>(kruskal_length + repeat);
                }
                const auto kruskal_finish = std::chrono::steady_clock::now();
                const double kruskal_us =
                    std::chrono::duration<double, std::micro>(kruskal_finish - kruskal_start).count()
                    / repetitions;
                *output << "Kruskal," << vertices << ',' << edge_count << ',' << factor << ','
                        << seed << ',' << trial << ',' << kruskal_us << ','
                        << kruskal_length << '\n';

                const auto prim_start = std::chrono::steady_clock::now();
                long long prim_length = 0;
                for (int repeat = 0; repeat < repetitions; ++repeat) {
                    prim_length = prim_total_length(vertices, edges);
                    checksum ^= static_cast<std::uint64_t>(prim_length + repeat + 17);
                }
                const auto prim_finish = std::chrono::steady_clock::now();
                const double prim_us =
                    std::chrono::duration<double, std::micro>(prim_finish - prim_start).count()
                    / repetitions;
                if (prim_length != kruskal_length) {
                    throw std::runtime_error("Kruskal and Prim totals disagree");
                }
                *output << "Prim," << vertices << ',' << edge_count << ',' << factor << ','
                        << seed << ',' << trial << ',' << prim_us << ','
                        << prim_length << '\n';
            }
        }
    }
    std::cerr << "Benchmark checksum: " << checksum << '\n';
}
