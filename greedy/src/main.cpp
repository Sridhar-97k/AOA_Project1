#include "mst.hpp"

#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

int main() {
    try {
        int building_count = 0;
        int route_count = 0;
        if (!(std::cin >> building_count >> route_count) || building_count <= 0 ||
            route_count < 0) {
            throw std::invalid_argument("expected positive building count and nonnegative route count");
        }

        std::vector<cabling::Edge> routes;
        routes.reserve(static_cast<std::size_t>(route_count));
        for (int index = 0; index < route_count; ++index) {
            cabling::Edge route{};
            if (!(std::cin >> route.from >> route.to >> route.length)) {
                throw std::invalid_argument("missing or malformed route");
            }
            route.input_order = static_cast<std::size_t>(index);
            routes.push_back(route);
        }
        std::string extra;
        if (std::cin >> extra) {
            throw std::invalid_argument("unexpected data after the route list");
        }

        const cabling::MstResult result = cabling::kruskal(building_count, routes);
        std::cout << "TOTAL_LENGTH " << result.total_length << '\n';
        for (const cabling::Edge& route : result.routes) {
            std::cout << "ROUTE " << route.from << ' ' << route.to << ' '
                      << route.length << '\n';
        }
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "error: " << error.what() << '\n';
        return 1;
    }
}
