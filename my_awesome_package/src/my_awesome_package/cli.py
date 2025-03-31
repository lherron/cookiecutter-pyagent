"""Console script for my_awesome_package."""
import my_awesome_package

import typer
from rich.console import Console

app = typer.Typer()
console = Console()


@app.command()
def main():
    """Console script for my_awesome_package."""
    console.print("Replace this message by putting your code into "
               "my_awesome_package.cli.main")
    console.print("See Typer documentation at https://typer.tiangolo.com/")
    


if __name__ == "__main__":
    app()
