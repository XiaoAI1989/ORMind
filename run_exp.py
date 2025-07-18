from utils.experiment_runner import build_parser, run_experiment
from utils.utils import read_problem


def main():
    parser = build_parser(
        default_dataset="LPWP",
        default_problem="prob_.*",
        default_attention="""Note: While certain parameters in the example may not be utilized, it is imperative to include all of them in the function definition.
The function must return a tuple, with the first element being the objective value. A dictionary is not permitted as the return type.""",
    )
    args = parser.parse_args()
    run_experiment(args, read_problem)


if __name__ == "__main__":
    main()
