import os
import json

from _pytest.monkeypatch import monkeypatch
from click.testing import CliRunner
import moto
import boto3
import pytest


@pytest.fixture(scope="session")
def monkeypatch_session(request):
    mp = monkeypatch(request)
    request.addfinalizer(mp.undo)
    return mp


@pytest.fixture(scope='session')
def aws_config(monkeypatch_session):
    monkeypatch_session.setenv('AWS_DEFAULT_REGION', 'us-east-1')
    monkeypatch_session.setenv('AWS_ACCESS_KEY_ID', 'AKIAIOSFODNN7EXAMPLE')
    monkeypatch_session.setenv(
        'AWS_SECRET_ACCESS_KEY',
        'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
    )


@pytest.fixture
def runner():
    cli_runner = CliRunner()
    with cli_runner.isolated_filesystem():
        yield cli_runner


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


@pytest.fixture
def stack():
    client = boto3.client('cloudformation')
    client.create_stack(
        StackName='HelloWorld', TemplateBody=TEST_TEMPLATE_BODY)


@pytest.fixture
def mock_cloudformation():
    with moto.mock_cloudformation():
        yield
