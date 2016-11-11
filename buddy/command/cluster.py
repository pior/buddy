import copy
import os
import pprint
import string
import sys
import time

import click
import yaml

from buddy.client import EcsClient


class EcsServiceAction(object):
    def __init__(self, client, cluster, service):
        self.client = client
        self.cluster = cluster
        self.service = service

    def _get_state(self):
        response = self.client.describe_services(self.cluster,
                                                 self.service)
        return response['services'][0]

    def _print_deployments_progress(self, state):
        for dep in state['deployments']:
            msg = ("%(taskDefinition)s - %(status)s - "
                   "running: %(runningCount)s")
            print(msg % dep)

    def _evaluate_deployments(self):
        state = self._get_state()
        if len(state['deployments']) > 1:
            print("Wait: deployment in progress")
            self._print_deployments_progress(state)
            print("")
            return False
        return True

    def _print_state(self):
        state = self._get_state()
        state['events'] = state['events'][0:15]
        pprint.pprint(state)
        print("")
        sys.stdout.flush()

    def get_active_task_definition(self):
        state = self._get_state()
        return state['taskDefinition']

    def wait_for_deploy(self, timeout=300):
        SLEEP = 5.0
        STEPS = int(timeout / SLEEP)
        for _ in range(STEPS):
            if self._evaluate_deployments():
                deployed = True
                break
            deployed = False
            time.sleep(SLEEP)

        print("Final state:")
        self._print_state()
        return deployed


class Application(object):

    def __init__(self, data, target_name, image, build_rev):
        self.data = data
        self.target_name = target_name
        self.image = image
        self.build_rev = build_rev

    @property
    def target(self):
        return self.data['targets'][self.target_name]

    @property
    def cluster_name(self):
        return self.target['cluster']

    @property
    def service_name(self):
        return self.target['service']

    @property
    def task_name(self):
        return self.target['task']

    @property
    def _environment(self):
        try:
            env_name = self.target['environment']
        except KeyError:
            raise KeyError('Missing environment key in target')
        try:
            return self.data['environments'][env_name]
        except KeyError:
            raise KeyError('Missing environment %s' % env_name)

    def get_task(self, name):
        data = self.data['tasks'][name]
        data['containers'] = [
            self.get_container_definition(container_name)
            for container_name in data['containers']
        ]
        return data

    def get_container_definition(self, name):
        data = self.data['containers'][name]
        props = data['properties'].copy()
        props['name'] = name
        props.setdefault('image', str(self.image))

        environment = data.get('environment')
        if environment:
            props['environment'] = [
                {'name': vname, 'value': self._environment[vname]}
                for vname in environment
            ]
        self._process_properties(props)
        return props

    def _interpolate_string(self, s):
        variables = {'build_rev': self.build_rev}
        click.echo('Interpolate: %s' % s)
        template = string.Template(s)
        return template.substitute(**variables)

    def _process_properties(self, properties):
        for key, value in properties.items():
            if isinstance(value, dict):
                properties[key] = self._process_properties(value)
            if isinstance(value, (str, unicode)):
                properties[key] = self._interpolate_string(value)


def read_app_cluster_config(path):
    with open(path) as fp:
        data = yaml.load(fp)
    return data


def header(s, fg='green', bold=True):
    click.secho(s, fg=fg, bold=bold)


@click.group()
def cli():  # pragma: no cover
    pass


@click.command()
@click.argument('app-config-file')
@click.argument('target-name')
@click.argument('image')
@click.argument('build-rev')
@click.option('--dry-run', is_flag=True)
def deploy(app_config_file, target_name, image, build_rev, dry_run):
    config = read_app_cluster_config(app_config_file)
    app = Application(config, target_name, image, build_rev)
    task = app.get_task(app.task_name)

    ecs = EcsClient()
    ecs_service = EcsServiceAction(ecs, app.cluster_name, app.service_name)

    click.secho('Definition:')
    click.echo(yaml.dump(task['containers']))

    if dry_run:
        sys.exit('Dry-run, stop now.')

    header('Register task...')
    resp = ecs.register_task_definition(family=app.task_name,
                                        containers=task['containers'])
    task_definition_arn = resp['taskDefinition']['taskDefinitionArn']
    header(
        'Registered task: %s' % task_definition_arn,
        fg='green', bold=True,
    )

    header('Updating service %s' % app.service_name)
    ecs.update_service(app.cluster_name, app.service_name, task_definition_arn)
    header('Updated')

    header('Deploying', fg='yellow')
    deployed = ecs_service.wait_for_deploy()
    if not deployed:
        print("Deployment failed (timeout)")
        sys.exit(1)

    active_task_definition = ecs_service.get_active_task_definition()
    if active_task_definition != task_definition_arn:
        print("Deployment failed (active: %s)" % active_task_definition)
        sys.exit(1)

    print("Success")


cli.add_command(deploy)
