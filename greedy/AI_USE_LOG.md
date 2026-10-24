# AI Assistance Log (Starting Record)

The assignment requires an appendix with exact AI tools, prompts, results, and generated intermediate results. This file starts that record; the authors should retain the complete conversation and review it before submission.

## Tool

OpenAI Codex, used to develop the initial greedy-problem implementation and documentation on 2026-10-24.

## User prompts relevant to this code

> connecting buildings with the least amount of cable using MST. this is the topic which we have decided. As you can see this is a greedy type problem.

> based on the problem statement, how can you define the problem, how woult it satisfy the project requirement? use the report as a reference

> lets start with the project, i need you to create 2 dirs at the top level, "greedy" and "dividenconquer". You need to populate the greedy dir as a part of your code generation

> can you add more testcases inside greedy/? have larger values

## Generated results

The generated result is the initial contents of `greedy/src/`, `greedy/tests/`, `greedy/experiments/`, `greedy/data/`, `greedy/README.md`, and `dividenconquer/README.md`. The later prompt added larger graph, weight, and overflow cases to `greedy/tests/test_mst.py` and `greedy/data/larger_example.txt`. Generated CSV and plot files are experiment outputs. Include or archive the exact file versions and any intermediate generated responses in the final report appendix. This record does not itself complete the assignment's disclosure requirement.
