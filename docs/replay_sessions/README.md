# Recorded Replay Sessions

Four complete pipeline runs recorded with `tools/replay_driver.py` against a
live model. Each session folder contains every prompt (`call_NNN_prompt.txt`),
every model response (`call_NNN_response.txt`), the generated counterfactual
checker and its verdict (`*_eval_code.py`, `*_eval_result.txt`), the full
control-flow trace (`*_ormind_trace.json`), and the post-hoc blind grading log
(`*_test_log.txt`). Together they make one Algorithm 1 execution auditable
call by call.

| Session | Dataset / problem | What it demonstrates |
|---|---|---|
| `prob_123` | LPWP `prob_123` (the Appendix A pharmacy problem) | Happy path: the model formulates correctly on the first pass, the counterfactual checker reports no violation, no revision happens (5 LLM calls). |
| `prob_123_cf` | LPWP `prob_123` | **Reproduction of the Appendix A case study**: the initial program returns `(150.0, 50, 0)`, the System 2 Reasoner's checker flags the 70%-sleeping-pills constraint, the Supervisor revises, and the corrected program returns `(735.0, 50, 117)` — the exact trajectory printed in the paper. |
| `prob_0` | LPWP `prob_0` | **The Appendix B failure mode (syntax repair) on a live model**: the first program fails at execution, the System 2 Reasoner diagnoses the error, the Supervisor's backward pass repairs it, and the rerun passes (7 LLM calls, `repairs: ["execution_error"]`). Appendix B prints this mode on ComplexOR `steel3`; this recording reproduces the mechanism, not that specific problem. |
| `Knapsack` | ComplexOR `Knapsack` | The ComplexOR path: scaffolded `solve(data)` interface, dict-output handling, counterfactual checker over `optimized_vars` + instance data, clean verdict, graded ACCEPT. |

## How to verify the no-label-leakage invariant yourself

The reference optimum never appears in any prompt. Two prompts do contain
numbers equal to it — both are benign and worth checking explicitly:

- `prob_0/call_006_prompt.txt` contains `obj: 3000.0`: that is the
  **program's own computed solution**, which the counterfactual checker
  legitimately receives as input.
- `prob_123/call_004_prompt.txt` contains `3000` from "3000 mg of morphine"
  in the problem text, plus the computed `obj: 735.0`.

`tests/test_offline_pipeline.py::scenario_no_label_leakage` asserts the same
invariant mechanically for a wrong-but-feasible solution.

## Token-count caveat

The replay transport has no API usage object, so `prompt_tokens` /
`completion_tokens` in these traces are `len(text) // 4` **estimates**
(`tools/replay_driver.py`). Do not compare them with Table 4 of the paper;
the experiment runner records real API token usage for that purpose.

## Reproducing a session

```bash
python tools/replay_driver.py --dataset LPWP --problem prob_123 --session temp/replay/prob_123
# exit code 3 -> write temp/replay/prob_123/call_000_response.txt, rerun, repeat
```

Responses can come from any completion source (another model, a chat UI, a
human). Completed calls replay deterministically from disk.
