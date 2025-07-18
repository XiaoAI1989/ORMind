# ORMind

[![ACL 2025](https://img.shields.io/badge/ACL-2025-red)](https://aclanthology.org/2025.acl-industry.10/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Official codebase for **ORMind: A Cognitive-Inspired End-to-End Reasoning Framework for Operations Research** (ACL 2025 Industry Track).

[Read the paper](https://aclanthology.org/2025.acl-industry.10/)

## What This Repo Implements

The default pipeline (`--mode paper`) is a faithful implementation of the
paper's Algorithm 1 with the prompt templates published verbatim in
Appendix C:

| Paper component (Section 3.3) | Code |
|---|---|
| Semantic Encoder | `agent_team/semantic_encoder.py` |
| Formalization Thinking | `agent_team/formalization_thinking.py` |
| Executive Compiler | `agent_team/executive_compiler.py` |
| Metacognitive Supervisor (forward/backward) | `agent_team/supervisor.py` |
| System 2 Reasoner (counterfactual + syntax analysis) | `agent_team/reasoner.py` |
| Memory pool P (Section 3.2) | `utils/comment_pool.py` |
| Algorithm 1 control flow | `agent_team/ormind_pipeline.py` |

Control flow per problem: encode -> formalize -> compile -> supervisor
formats the final program -> run on problem inputs -> if execution fails,
the System 2 Reasoner diagnoses the error and the Supervisor revises
(`--max_repair_rounds`, default 1 as in Algorithm 1) -> on clean
execution, the System 2 Reasoner generates a counterfactual checker from
the problem description; if it reports a discrepancy, the Supervisor
revises once more.

Two additional modes exist:

- `--mode standard`: single-prompt baseline (the "w/o All modules" row of
  Table 2).
- `--mode extended`: post-publication research extensions (adaptive
  search, dual-view formalization, online preference verifier, experience
  memory). **Not used for any number reported in the paper**; see
  "Extended mode" below.

## Evaluation Protocol and Data Hygiene

The harness is built so that benchmark numbers are auditable:

1. The solving pipeline receives the problem text, the interface code
   example, and **raw test inputs only**. Reference outputs never reach
   any pipeline, prompt, or stored artifact (`solve_problem` in
   `main.py` takes `test_inputs` with the labels already stripped).
2. Repair is triggered exclusively by execution errors and by the
   counterfactual check against the problem description — never by
   comparing to reference outputs.
3. Grading happens exactly once per problem, after the pipeline has
   finished (`test_generated_code` in `utils/test_generated_code.py`).
4. `tests/test_offline_pipeline.py` contains a regression test
   (`scenario_no_label_leakage`) asserting that the ground-truth optimum
   does not appear in any prompt.

Metric operationalization (numeric tolerance: `rel_tol=1e-3`,
`abs_tol=0.2` on the objective value):

| Paper metric | Definition in this harness |
|---|---|
| SR | graded `ACCEPT`: objective matches the reference optimum |
| MFFR | graded `MODEL_FAILURE`: program ran but the model was invalid (solver status not `Optimal`, or no objective produced) |
| IEFR | graded `COMPILE_ERROR` or `RUNTIME_ERROR` |
| (residual) | graded `WRONG_ANSWER`: feasible model, wrong optimum |

### Known protocol caveats

These properties are part of the published protocol (shared with the
upstream Chain-of-Experts release). They are disclosed here so that
third-party reviewers do not have to rediscover them; none of them was
changed for the published numbers.

1. **Infeasible references cap ComplexOR SR at 26/37.** 11 of the 37
   ComplexOR problems ship the string `"Infeasible"` as their reference
   output. The published grader counts a solver status that is not
   `Optimal` as MODEL_FAILURE, so a program that *correctly* detects
   infeasibility can never be graded ACCEPT. `--accept_infeasible`
   grades an exact status match as ACCEPT instead; numbers produced with
   this flag are not comparable to the paper's tables.
2. **LPWP inputs can encode the optimum (echo-args caveat).** Per the
   upstream data format, the `data.json` "input" values of many LPWP
   problems are the optimal decision values themselves (the function
   arguments name the decision variables). Input values never appear in
   any prompt, but a generated program that ignores the solver and
   computes its return value directly from its arguments would be graded
   correct on such problems. The runner therefore logs `Solver Used:
   True/False` per problem and warns about any ACCEPTed program that
   never references the solver, so runs can be audited for this shortcut.
   All systems evaluated under this protocol face the same caveat.
3. **Tolerance width.** The published tolerance accepts an objective
   within 0.1% relative error (e.g. 2997.5 vs a true optimum of 3000).
   `--rel_tol` / `--abs_tol` expose stricter checks; the defaults are the
   published values.

## Setup

```bash
git clone https://github.com/XiaoAI1989/ORMind.git
cd ORMind
pip install -r requirements.txt
```

Create `env.local` in the project root (loaded automatically):

```env
# Paper configuration (Section 5.2): GPT-3.5-turbo, temperature 0.
# These are also the built-in defaults — with no env.local at all, the
# runner targets gpt-3.5-turbo on the OpenAI API; only the key is needed.
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
ORMIND_MODEL=gpt-3.5-turbo

# Or any OpenAI-compatible endpoint, e.g. OpenRouter:
# OPENROUTER_API_KEY=your_key_here
# OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
# ORMIND_MODEL=deepseek/deepseek-chat-v3.1

# Strictly opt-in: retry a failed call once on a second model. OFF unless
# set. When it fires, the runner prints a warning and the per-problem
# logs record completions per model ("Models Used"), so a mixed-model run
# is always visible. Do not enable when reproducing paper numbers.
# ORMIND_FALLBACK_MODEL=gpt-4o-mini
```

## Reproducing the Paper

**Table 1 (main results).** ORMind rows:

```bash
python run_exp.py                 # LPWP (the NL4Opt LP word problems)
python run_exp_ComplexOR.py      # ComplexOR
```

Baseline rows are not produced by this repository: OptiMUS numbers are
cited from its original paper, and the prompting baselines
(CoT/ReAct/Reflexion/CoE, ...) come from their respective public
implementations.

**Table 2 (ablations).** Every row maps to a flag:

```bash
python run_exp.py                                   # ORMind (Full)
python run_exp.py --with_conductor                  # w/ Conductor
python run_exp.py --with_terminology_interpreter    # w/ Terminology Interpreter
python run_exp.py --with_code_reviewer              # w/ Code Reviewer
python run_exp.py --without_semantic_encoder        # w/o Semantic Encoder
python run_exp.py --without_formalization           # w/o Formalization Thinking
python run_exp.py --without_counterfactual          # w/o Counterfactual Analysis
python run_exp.py --without_syntax_analysis         # w/o Syntax Error Analysis
python run_exp.py --mode standard                   # w/o All modules
```

(Use `run_exp_ComplexOR.py` with the same flags for the ComplexOR
column.)

**Table 3 (model robustness).** `python run_exp.py --model gpt-4`.

**Figure 3 (temperature analysis).** `python run_exp.py --temperature 0.5`.

**Table 4 (prompt-length statistics).** Each `*_test_log.txt` records
`Prompt Tokens: N` for the full problem run; aggregate with:

```bash
python data_process/count_token.py --folder <run_dir>   # mean and std
```

SR/MFFR/IEFR can be recomputed from any run directory with
`python data_process/correct_rate.py --folder <run_dir>`.

Useful options:

```bash
python run_exp.py --problem prob_12              # single problem
python run_exp_ComplexOR.py --problem steel3
python run_exp.py --max_repair_rounds 2          # allow a second error repair
```

Grading options that deviate from the published protocol (all defaults =
published behaviour; see "Known protocol caveats"):

```bash
python run_exp_ComplexOR.py --accept_infeasible  # status match on "Infeasible" counts as ACCEPT
python run_exp.py --rel_tol 1e-4                 # stricter objective tolerance
```

## Datasets

- `LPWP`: the NL4Opt competition LP word problems. This release contains
  288 problems, while the paper reports 289 test samples; the discrepancy
  is one problem.
- `ComplexOR`: 37 industrial optimization problems. 11 of them carry
  `"Infeasible"` as the reference output (see "Known protocol caveats").

Both follow the data format of Appendix F. Per dataset convention
(shared with Chain-of-Experts), each problem ships a `code_example.py`
that fixes the function interface the generated program must implement;
for ComplexOR the scaffold also pre-declares the decision variables, and
the generated code fills in the `TODO` region (objective + constraints).
All systems compared under this protocol receive the same scaffold.

Dataset notes:

- The `input.json` files inside some ComplexOR problem folders are legacy
  artifacts of the upstream data format; nothing in this harness reads
  them (`data.json` carries the graded samples, `input_targets.json` the
  problem statement).
- `prob_135` declares one of its arguments as a string
  (`constraint3: "twice"`) in its own docstring — intentional per the
  upstream data, not a typing error.

## Extended Mode (post-publication, off by default)

`--mode extended` runs `agent_team/reflective_orchestrator.py`, which
adds components developed after the paper was published: an adaptive
search controller, dual-view formalization with value-level consistency
scoring, an online preference verifier over candidate programs, an
experience memory, and **consensus counterfactual verification** — the
Section 3.3.4 mechanism deepened: two checkers audit the solution
through different verification lenses and return quantified,
machine-comparable violation reports. When both checkers produce valid
reports, only violations confirmed by both (matched on canonical
constraint expressions, ranked by violation magnitude) trigger a
revision, which suppresses checker-hallucinated repairs; if exactly one
checker yields a valid report, its findings are used as-is rather than
dropping verification entirely (`utils/adaptive_search.py`,
`utils/online_preference.py`, `utils/experience_distiller.py`, prompts
in `agent_team/extended_experts.py`).

Its learning signals (preference updates, memory records) are derived
from execution status and counterfactual checks only — like the paper
pipeline, it never sees reference outputs. Numbers produced in this mode
are not comparable to the paper and should be reported separately. The
flow diagram is in `docs/ormind_algorithm_flow.excalidraw`.

```bash
python run_exp.py --mode extended --num_candidates 4
```

## Tests

```bash
python tests/test_offline_pipeline.py
```

Offline regression suite (no API key needed; the LLM transport is
stubbed). Covers the Algorithm 1 happy path, syntax repair,
counterfactual revision, a causality check on the counterfactual loop
(the same wrong program is revised under a flagging checker and left
untouched under a clean one), consensus counterfactual verification,
every ablation flag, the standard baseline, extended mode, grader
classification (SR/MFFR/IEFR) including the `--accept_infeasible` and
tolerance flags, empty-input boundaries, cross-problem memory isolation,
fallback-model visibility, the paper-default runtime configuration, and
the no-label-leakage invariant.

## Replay Driver and Recorded Runs

`tools/replay_driver.py` runs the pipeline with a record/replay
transport: each LLM call is written to disk and satisfied from a
response file, so a full run can be driven by any completion source and
audited call by call afterwards.

`docs/replay_sessions/` contains four complete recorded runs (every
prompt, response, generated checker, trace, and blind grading log),
including a reproduction of the Appendix A counterfactual-repair case
study and the Appendix B syntax-repair failure mode on a live model. See
`docs/replay_sessions/README.md` for what each session demonstrates.

## Implementation Notes

- The experiments in the paper were run on LangChain 0.2.7 (Appendix E).
  The pipeline here runs the same workflow and prompts on a direct
  OpenAI-compatible client, which removes the heavyweight dependency and
  lets any OpenAI-compatible endpoint serve as the backbone.
- `gpt-3.5-turbo` (the paper's default backbone) is the built-in
  default, but provider-side model snapshots drift over time; expect
  variance against the published numbers. Per-problem logs record the
  completions served by each model ("Models Used").
- The LPWP release contains 288 of the 289 problems used in the paper.
- Algorithm 1 specifies a single error-triggered revision;
  `--max_repair_rounds` generalizes this (default 1 = Algorithm 1).
- When the Conductor ablation's LLM reply names no remaining expert, the
  release falls back to the first expert in the fixed Algorithm 1 order
  (deterministic) instead of a random choice.
- The counterfactual checker pairs the candidate solution with the data
  of the input that produced it. If the LLM-written checker itself
  crashes, the problem is recorded as `checker_failed` in its trace and
  the run-level summary, and no revision is attempted for it.

## Errata and known deviations from the paper

- **prob_203 data erratum.** The upstream `data.json` typed the reference
  output and inputs as strings (`"375"`, `"50.0"`, `"0.0"`), which made
  the problem ungradeable as correct (a numeric objective never compares
  equal to a string). This release fixes the types; the values are
  unchanged and match the problem's own docstring (optimum 375 at
  (50, 0), verified by hand). Runs predating the fix graded prob_203 as
  non-ACCEPT no matter what; re-runs can therefore differ by at most
  +1/288 (≈0.35%) SR on LPWP relative to the published table.
- **ComplexOR SR ceiling.** Under the published protocol the 11
  Infeasible-reference problems cannot be graded ACCEPT (max SR 26/37 ≈
  70.3%); the published ORMind number (40.5%) is consistent with and
  unaffected by this ceiling. See "Known protocol caveats".
- **Abstract arithmetic.** The abstract states a 9.5% improvement on
  NL4Opt; Table 1 gives 68.8% vs 58.9% for the best baseline, a 9.9 pp
  gap. The table is the authoritative number.
- Trace files now also record a per-comment timestamp (the memory-pool
  update metadata described in Appendix G) and the per-problem
  counterfactual checker status; neither affects any prompt or decision.

## Citation

```bibtex
@inproceedings{wang-etal-2025-ormind,
    title = "{ORM}ind: A Cognitive-Inspired End-to-End Reasoning Framework for Operations Research",
    author = "Wang, Zhiyuan and
      Chen, Bokui and
      Huang, Yinya and
      Cao, Qingxing and
      He, Ming and
      Fan, Jianping and
      Liang, Xiaodan",
    booktitle = "Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 6: Industry Track)",
    month = jul,
    year = "2025",
    address = "Vienna, Austria",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2025.acl-industry.10/",
    doi = "10.18653/v1/2025.acl-industry.10",
    pages = "104--131"
}
```
