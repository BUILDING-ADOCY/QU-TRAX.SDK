# qtrax_sdk/main.py

import typer  # type: ignore
from pathlib import Path
from qtrax_sdk.core.optimizer import optimize_routes

app = typer.Typer(help="Q-TRAX SDK CLI — Quantum-Inspired Logistics Optimizer") # type: ignore


@app.command("optimize") # type: ignore
def optimize(
    config_path: str = typer.Argument(..., help="Path to config YAML/JSON"), # type: ignore
    output_path: str = typer.Argument(..., help="Path to save result JSON"), # type: ignore
    use_yaml: bool = typer.Option(True, help="Is the config file YAML?"), # type: ignore
    max_tick: int = typer.Option(50, help="Maximum ticks for the annealer"), # type: ignore
):
    """
    Run the Q-TRAX optimization on a problem definition.
    """
    
    # Validate config file path
    config_file = Path(config_path)
    if not config_file.exists():
        typer.echo(f"Config file {config_file} does not exist.", err=True) # type: ignore
        raise typer.Exit(code=1) # type: ignore
    # Prepare output directory
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        solution = optimize_routes(
            config_path=config_path,
            output_path=output_path,
            use_yaml=use_yaml,
            max_tick=max_tick
        )
    except Exception as e:
        typer.echo(f"Error during optimization: {e}", err=True) # type: ignore
        raise typer.Exit(code=1) # type: ignore

    typer.echo("Optimization complete.") # type: ignore
    typer.echo(f"Result Summary: {solution}") # type: ignore


if __name__ == "__main__":
    app()
