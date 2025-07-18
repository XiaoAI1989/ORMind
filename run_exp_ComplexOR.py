from utils.experiment_runner import build_parser, run_experiment
from utils.utils import read_OR_problem


def main():
    parser = build_parser(
        default_dataset="ComplexOR",
        default_problem=".*",
        default_attention="""The function name must be "def solve(data):" and the return must be a dict with same key as example.
You need to give your final answer in the Todo domain of example. Don't modify other contents in the example""",
    )
    args = parser.parse_args()
    run_experiment(args, read_OR_problem)


if __name__ == "__main__":
    main()
