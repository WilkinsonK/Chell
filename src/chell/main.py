import click


@click.group()
@click.option("-s", "--shell", "shell", help="enter the shell", is_flag=True)
def main(shell: bool):
    """Chell direct management tool."""
