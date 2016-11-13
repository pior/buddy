from buddy.command.stack import cli


def test_list_empty(mock_cloudformation, runner):
    result = runner.invoke(cli, ['list'])
    assert result.exit_code == 0


def test_list(mock_cloudformation, runner, stack):
    result = runner.invoke(cli, ['list'])
    assert result.exit_code == 0
    assert 'HelloWorld' in result.output
    assert 'CREATE_COMPLETE' in result.output
