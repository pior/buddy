import json
import os

from click.testing import CliRunner
from moto import mock_cloudformation
import boto3
import pytest

from buddy.command.stack import cli


TEST_TEMPLATE = {
    "AWSTemplateFormatVersion": "2010-09-09",
    "Resources": {
        "Sns": {
            "Type": "AWS::SNS::Topic",
            "Properties": {
                "TopicName": "Hello"
            }
        }
    }
}
TEST_TEMPLATE_BODY = json.dumps(TEST_TEMPLATE)


def setup_test_stack():
    client = boto3.client('cloudformation')
    client.create_stack(
        StackName='HelloWorld', TemplateBody=TEST_TEMPLATE_BODY)


def assert_if_cwd_not_empty():
    cwd = os.getcwd()
    dir_content = os.listdir(cwd)
    if dir_content:
        raise Exception('Current working directory not empty:'
                        ' %s: %s' % (cwd, dir_content))


@pytest.fixture
def runner():
    cli_runner = CliRunner()
    with cli_runner.isolated_filesystem():
        yield cli_runner
        assert_if_cwd_not_empty()


@mock_cloudformation
def test_list_empty(runner):
    result = runner.invoke(cli, ['list'])
    assert result.exit_code == 0


@mock_cloudformation
def test_list(runner):
    setup_test_stack()
    result = runner.invoke(cli, ['list'])
    assert result.exit_code == 0
    assert 'HelloWorld' in result.output
    assert 'CREATE_COMPLETE' in result.output
