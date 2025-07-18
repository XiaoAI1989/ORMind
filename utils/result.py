from enum import Enum


class Result(Enum):
    """Grading outcome for one problem.

    Mapping to the paper's metrics:
      ACCEPT        -> counted in SR (Success Rate)
      MODEL_FAILURE -> counted in MFFR (Model Formulation Failure Rate):
                       the program executed but the formulated model was
                       invalid (solver reports Infeasible/Unbounded, or no
                       objective value was produced).
      RUNTIME_ERROR / COMPILE_ERROR
                    -> counted in IEFR (Implementation Execution Failure
                       Rate): the program could not be executed.
      WRONG_ANSWER  -> residual bucket: a feasible model was solved but the
                       objective does not match the reference optimum.
    """

    ACCEPT = 0
    WRONG_ANSWER = 1
    RUNTIME_ERROR = 2
    COMPILE_ERROR = 3
    MODEL_FAILURE = 4
