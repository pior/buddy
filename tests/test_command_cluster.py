import os
import tempfile

from buddy.command.cluster import cli
import pytest
import vcr
import yaml
import boto3


def teardown():
    ecs_client = boto3.client('ecs')
    ecs_client.delete_service(cluster='CLUSTERNAME', service='SERVICENAME')
    ecs_client.delete_cluster(cluster='CLUSTERNAME')


def setup():
    ecs_client = boto3.client('ecs')

    containers = [
        {
            'name': 'NAME',
            'image': 'nginx',
            'memory': 10,
        }
    ]
    response = ecs_client.register_task_definition(
        family='TASKNAME',
        containerDefinitions=containers,
    )
    task_definition_arn = response['taskDefinition']['taskDefinitionArn']

    response = ecs_client.create_cluster(clusterName='CLUSTERNAME')
    ecs_cluster = response['cluster']['clusterName']

    response = ecs_client.create_service(
        cluster=ecs_cluster,
        serviceName='SERVICENAME',
        taskDefinition=task_definition_arn,
        desiredCount=0,

    )
    ecs_service = response['service']['serviceName']

    return ecs_cluster, ecs_service


def make_deploy_config_data(cluster, service):
    return {
        'targets': {
            'production': {
                'cluster': cluster,
                'service': service,
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


def deploy_config(ecs_service, ecs_cluster):
    data = make_deploy_config_data(cluster=ecs_cluster, service=ecs_service)
    fh, name = tempfile.mkstemp()
    fh.write(yaml.safe_dump(data))
    fh.close()
    return name


@vcr.use_cassette('tests/vcr/deploy.yaml')
def test_deploy():
    cluster, service = setup()
    config = deploy_config(cluster, service)

    try:
        args = ['deploy', config, 'production', 'image:tag', 'rev']
        # result = runner.invoke(cli, args, catch_exceptions=True)

        # print(result.output)

        # assert result.exit_code == 0

        # assert 'CREATE_COMPLETE' in result.output
    except:
        try:
            teardown()
        except:
            pass
        raise
