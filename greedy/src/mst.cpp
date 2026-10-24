#include "mst.hpp"

#include <algorithm>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <utility>
#include <vector>

namespace cabling {
namespace {

class DisjointSet {
public:
    explicit DisjointSet(int size) : parent_(size), rank_(size, 0) {
        std::iota(parent_.begin(), parent_.end(), 0);
    }

    int find(int vertex) {
        if (parent_[vertex] != vertex) {
            parent_[vertex] = find(parent_[vertex]);
        }
        return parent_[vertex];
    }

    bool unite(int first, int second) {
        first = find(first);
        second = find(second);
        if (first == second) {
            return false;
        }
        if (rank_[first] < rank_[second]) {
            std::swap(first, second);
        }
        parent_[second] = first;
        if (rank_[first] == rank_[second]) {
            ++rank_[first];
        }
        return true;
    }

private:
    std::vector<int> parent_;
    std::vector<int> rank_;
};

bool shorter_first(const Edge& first, const Edge& second) {
    if (first.length != second.length) {
        return first.length < second.length;
    }
    const auto first_ends = std::minmax(first.from, first.to);
    const auto second_ends = std::minmax(second.from, second.to);
    if (first_ends != second_ends) {
        return first_ends < second_ends;
    }
    return first.input_order < second.input_order;
}

}  // namespace

MstResult kruskal(int building_count, std::vector<Edge> routes) {
    if (building_count <= 0) {
        throw std::invalid_argument("building count must be positive");
    }
    for (const Edge& route : routes) {
        if (route.from < 0 || route.to < 0 || route.from >= building_count ||
            route.to >= building_count || route.from == route.to ||
            route.length <= 0) {
            throw std::invalid_argument("route has invalid endpoints or length");
        }
    }

    std::sort(routes.begin(), routes.end(), shorter_first);
    DisjointSet components(building_count);
    MstResult result{0, {}};
    result.routes.reserve(static_cast<std::size_t>(building_count - 1));
    if (building_count == 1) {
        return result;
    }

    for (const Edge& route : routes) {
        if (!components.unite(route.from, route.to)) {
            continue;
        }
        if (result.total_length >
            std::numeric_limits<long long>::max() - route.length) {
            throw std::overflow_error("total cable length exceeds 64-bit limit");
        }
        result.total_length += route.length;
        result.routes.push_back(route);
        if (result.routes.size() == static_cast<std::size_t>(building_count - 1)) {
            return result;
        }
    }

    throw std::invalid_argument("permitted routes do not connect all buildings");
}

}  // namespace cabling
