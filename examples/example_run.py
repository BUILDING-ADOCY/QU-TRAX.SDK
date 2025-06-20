from qtrax_sdk.core.optimizer import optimize_routes

if __name__ == "__main__":
    solution = optimize_routes(
        config_path="examples/example_input.json",
        output_path="examples/solution.json",
        use_yaml=False,
        max_tick=50,
    )
    print("Solution:", solution)
