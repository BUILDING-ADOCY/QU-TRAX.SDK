
"""
Standalone script runner for Q-TRAX optimization.
Use this if you want to bypass CLI and invoke directly in code.
"""

from qtrax_sdk.core.optimizer import optimize_routes


def run():
    config_file = "examples/sample_config.yaml"
    output_file = "outputs/solution.json"

    print("🚀 Running Q-TRAX optimization...")
    solution = optimize_routes(
        config_path=config_file,
        output_path=output_file,
        use_yaml=True,
        max_tick=50
    )
    print(" Done.")
    print(solution)


if __name__ == "__main__":
    run()
