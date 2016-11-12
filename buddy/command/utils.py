import click


def echo_step(s):
    click.secho(s, fg='green', bold=True)


def echo_action(s):
    click.secho(s, fg='yellow', bold=True)


def echo_error(s):
    click.secho(s, fg='red', bold=True)


def failure(s, exit_code=1):
    exc = click.ClickException(s)
    exc.exit_code = exit_code
    raise exc
