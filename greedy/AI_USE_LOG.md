1. **Exact recorded prompt:**
   > connecting buildings with the least amount of cable using MST. this is the topic which we have decided. As you can see this is a greedy type problem.
2. **Exact recorded prompt:**
   > based on the problem statement, how can you define the problem, how woult it satisfy the project requirement? use the report as a reference
3. **Exact recorded prompt:**
   > lets start with the project, i need you to create 2 dirs at the top level, "greedy" and "dividenconquer". You need to populate the greedy dir as a part of your code generation
4. **Exact recorded prompt:**
   > can you add more testcases inside greedy/? have larger values

### Reconstructed greedy-development prompts

5. **Representative prompt — graph abstraction:**
   > Model the campus minimum-cable problem as a weighted undirected graph. Define the vertices, edges, weights, feasible output, and objective precisely.
6. **Representative prompt — algorithm choice:**
   > Explain why a minimum spanning tree is the correct abstraction and compare Kruskal and Prim. Choose the most appropriate greedy algorithm for this report and justify the choice.
7. **Representative prompt — pseudocode:**
   > Write clear pseudocode for Kruskal's algorithm using a disjoint-set data structure, including initialization, sorting, cycle checks, termination, and disconnected-input handling.
8. **Representative prompt — union-find:**
   > Explain path compression and union by rank in the disjoint-set forest, and describe how they affect the running time of Kruskal's algorithm.
9. **Representative prompt — complexity:**
   > Derive the time and space complexity of Kruskal's algorithm in terms of vertices and edges. Explain why sorting gives the final O(E log E) bound.
10. **Representative prompt — correctness proof:**
    > Give a rigorous cut-property or exchange-argument proof that every edge accepted by Kruskal can be part of an MST, and then use it to prove the full algorithm correct.
11. **Representative prompt — domain explanation:**
    > Explain Kruskal's algorithm in campus-networking language while preserving the connection between short cable routes, connected components, cycles, and minimum total cable.
12. **Representative prompt — implementation:**
    > Implement the campus-network MST algorithm in portable C++17 with deterministic tie handling, input validation, disconnected-graph detection, and safe total-length accumulation.
13. **Representative prompt — correctness tests:**
    > Design tests for the MST implementation covering normal graphs, a single vertex, equal weights, parallel routes, disconnected inputs, malformed endpoints, large weights, overflow, and comparison with an independent reference.
14. **Representative prompt — benchmark design:**
    > Design a reproducible timing experiment for Kruskal's algorithm using fixed seeds, connected synthetic graphs, multiple values of V and E, repeated trials, warm-up/repetition handling, and CSV output.
15. **Representative prompt — baseline comparison:**
    > Add an independent Prim implementation as a baseline, verify that Kruskal and Prim produce the same MST total, and record both runtimes without including graph generation in the timed region.
16. **Representative prompt — plotting:**
    > Create publication-quality plots showing runtime versus E log E, normalized runtime, Kruskal versus Prim, and scaling across graph densities. Also generate a concise numerical summary.
17. **Representative prompt — interpretation:**
    > Interpret the benchmark results cautiously: explain how the graphs support the predicted O(E log E) growth, distinguish empirical evidence from a proof, and state the experiment's limitations.
18. **Representative prompt — report review:**
    > Review the greedy report against the assignment rubric for the real-world problem, abstraction, algorithm, complexity analysis, correctness proof, domain explanation, implementation, experiments, graphs, citations, and appendix requirements.

For the final submission appendix, replace reconstructed wording with the exact
original prompts wherever the conversation history is available, and preserve
the corresponding generated answers, code revisions, benchmark outputs, and
figure-generation results.
