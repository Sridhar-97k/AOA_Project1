#ifndef GREEDY_MST_HPP
#define GREEDY_MST_HPP

#include <cstddef>
#include <vector>

namespace cabling {

struct Edge {
    int from;
    int to;
    long long length;
    std::size_t input_order;
};

struct MstResult {
    long long total_length;
    std::vector<Edge> routes;
};

// Throws std::invalid_argument for an invalid or disconnected graph and
// std::overflow_error if the total length exceeds a signed 64-bit integer.
MstResult kruskal(int building_count, std::vector<Edge> routes);

}  // namespace cabling

#endif
