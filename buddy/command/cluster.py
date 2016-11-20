import time

import click
import yaml

from buddy.client import EcsClient, get_aws_region_name
from buddy.command.utils import echo_action, echo_step, echo_error, failure


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
        click.echo("\nWait: deployment in progress")
        for dep in state['deployments']:
            msg = ("%(taskDefinition)s - %(status)s - "
                   "running: %(runningCount)s")
            click.echo(msg % dep)

    def _is_deployed(self, state):
        return len(state['deployments']) < 2

    def _print_state(self):
        state = self._get_state()
        state['events'] = state['events'][0:15]
        click.echo(yaml.safe_dump(state))

    def get_active_task_definition_arn(self):
        state = self._get_state()
        return state['taskDefinition']

    def _poll_current_deployment(self):
        state = self._get_state()
        self._print_deployments_progress(state)
        return self._is_deployed(state)

    def wait_for_deploy(self, timeout):
        is_deployed = retry_it(self._poll_current_deployment, timeout)
        click.echo("Final state:")
        self._print_state()
        return is_deployed


def retry_it(fn, timeout, interval=5):
    STEPS = int(float(timeout) / interval)
    for _ in range(STEPS):
        result = fn()
        if result:
            return result
        time.sleep(interval)


def cloudwatch_log_configurator(context, properties):
    config = properties.get('logConfiguration', {})
    if config.get('logDriver') == 'awslogs':
        options = {
            'awslogs-group': context.get('task_name'),
            'awslogs-region': context.get('aws_region'),
            'awslogs-stream-prefix': context.get('build_rev'),
        }
        options.update(config.get('options', {}))
        config['options'] = options
    return properties


class Target(object):

    def __init__(self, data, target_name):
        self.data = data
        self.target_name = target_name

        target_data = data['targets'][target_name]
        self.cluster_name = target_data['cluster']
        self.service_name = target_data['service']
        self.task_name = target_data['task']
        self.task = data['tasks'][self.task_name]

        self.environment = {}
        environment_name = target_data.get('environment')
        if environment_name:
            try:
                plain_vars = data['environments'][environment_name]
            except KeyError:
                raise KeyError('Missing environment %s' % environment_name)
            self.environment.update(**plain_vars)

        self.container_definitions = self.data['containers']


def get_task_containers(app, image, context):
    def make(container_name):
        return make_container_definition(
            definition=app.container_definitions[container_name],
            name=container_name,
            image=image,
            environment=app.environment,
            context=context,
        )
    return [make(el) for el in app.task['containers']]


def make_container_definition(definition, name, image, environment, context):
    props = definition['properties'].copy()
    props['name'] = name
    props.setdefault('image', str(image))

    def get_variables(name):
        return {'name': name, 'value': environment[name]}

    required_variables = definition.get('environment')
    if required_variables:
        props['environment'] = [get_variables(v) for v in required_variables]

    for configurator in [cloudwatch_log_configurator]:
        props = configurator(context, props)

    return props


def read_app_cluster_config(path):
    with open(path) as fp:
        data = yaml.safe_load(fp)
    return data


def deploy_service(app, containers):
    ecs = EcsClient()
    ecs_service = EcsServiceAction(ecs, app.cluster_name, app.service_name)

    echo_action('Register task...')
    resp = ecs.register_task_definition(family=app.task_name,
                                        containers=containers)
    task_definition_arn = resp['taskDefinition']['taskDefinitionArn']
    echo_step('Registered task: %s' % task_definition_arn)

    echo_action('Updating service %s' % app.service_name)
    ecs.update_service(
        app.cluster_name, app.service_name, task_definition_arn)
    echo_step('Updated')

    echo_step('Waiting for deployment to complete (300s)')
    deployed = ecs_service.wait_for_deploy(timeout=300)
    if not deployed:
        failure('Deployment didn\'t finish in 300s')

    active_task_definition_arn = ecs_service.get_active_task_definition_arn()
    if active_task_definition_arn != task_definition_arn:
        failure('Deployment failed (active: %s)' % active_task_definition_arn)

    echo_step('Success')


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

    app = Target(config, target_name)

    context = {}
    context['task_name'] = app.task_name
    context['build_rev'] = build_rev
    context['aws_region'] = get_aws_region_name()

    containers = get_task_containers(app, image, context)

    click.secho('Definition:')
    click.echo(yaml.safe_dump(containers))

    if dry_run:
        echo_error("Dry-run!")
    else:
        deploy_service(app, containers)


cli.add_command(deploy)
