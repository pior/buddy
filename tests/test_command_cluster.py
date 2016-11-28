from buddy.command.cluster import cli
import pytest
import yaml


@pytest.fixture
def data():
    return {
        'targets': {
            'production': {
                'cluster': 'CLUSTERNAME',
                'service': 'SERVICENAME',
                'task': 'TASKNAME',
                'environment': 'ENVNAME',
            },
        },
        'tasks': {
            'TASKNAME': {
                'containers': ['CONTAINERNAME'],
            },
        },
        'environments': {
            'ENVNAME': {
                'VARIABLE_NAME': 'VARIABLE_VALUE',
            },
        },
        'containers': {
            'CONTAINERNAME': {
                'properties': {
                    'cpu': 10,
                    'memory': 20,
                    'command': ['prog', 'arg1', 'arg2'],
                    'logConfiguration': {
                        'logDriver': 'awslogs',
                    },
                },
                'environment': ['VARIABLE_NAME'],
            },
        },
    }


def write_config(data):
    name = 'config.yaml'
    with open(name, 'w') as fh:
        fh.write(yaml.safe_dump(data))
    return name


def test_nominal(runner, data):
    config = write_config(data)

    args = ['deploy', '--dry-run', config, 'production', 'image:tag', 'rev']
    result = runner.invoke(cli, args)

    assert not result.exception

    assert 'awslogs-group: TASKNAME' in result.output
    assert 'awslogs-region: us-east-1' in result.output
    assert 'awslogs-stream-prefix: rev' in result.output
    assert 'command: [prog, arg1, arg2]' in result.output
    assert 'cpu: 10' in result.output
    assert 'environment:' in result.output
    assert 'image: image:tag' in result.output
    assert 'logDriver: awslogs' in result.output
    assert 'memory: 20' in result.output
    assert 'name: CONTAINERNAME' in result.output
    assert '{name: VARIABLE_NAME, value: VARIABLE_VALUE}' in result.output


def test_missing_port(runner, data):
    data['containers']['CONTAINERNAME']['environment'].append('MISSINGVAR')
    config = write_config(data)

    args = ['deploy', '--dry-run', config, 'production', 'image:tag', 'rev']
    result = runner.invoke(cli, args)

    assert 'Unknown environment variable' in result.output
    assert 'MISSINGVAR' in result.output
    assert result.exit_code == 1
