import os

from tabulate import tabulate
import arrow
import botocore.exceptions
import click
import yaml

from buddy.client import CfnClient
from buddy.error import handle_exception


class Template(object):
    def __init__(self, client, path):
        self.client = client
        self.path = path

    @property
    def template_body(self):
        with open(self.path) as fp:
            return fp.read()

    def validate(self):
        return self.client.validate_template(self.template_body)


class Stack(object):
    def __init__(self, client, name_or_path):
        self.client = client
        if self._detect_stack_file(name_or_path):
            self.path = name_or_path
            self.name = self._name_from_file()
        else:
            self.path = None
            self.name = name_or_path

    def _detect_stack_file(self, path):
        return path.endswith('.yaml') or path.endswith('.yml')

    def _name_from_file(self):
        from_filename = os.path.splitext(os.path.split(self.path)[-1])[0]
        return self.properties.get('name', from_filename)

    @property
    def properties(self):
        if not hasattr(self, '_properties'):
            with open(self.path) as fp:
                self._properties = yaml.load(fp)
        return self._properties

    @property
    def template_path(self):
        template_path = self.properties['template']
        base_path = os.path.dirname(self.path)
        return os.path.join(base_path, template_path)

    @property
    def template_body(self):
        with open(self.template_path) as fp:
            return fp.read()

    @property
    def parameters(self):
        p = self.properties.get('parameters', {})
        p = {k: str(v) for k, v in p.items()}
        return p

    def __str__(self):
        return '<Stack %s: %s>' % (self.name, self.template_path)

    def create(self):
        response = self.client.create_stack(
            name=self.name,
            template=self.template_body,
            parameters=self.parameters,
            capabilities=['CAPABILITY_IAM'],
        )
        return response

    def update(self):
        response = self.client.update_stack(
            name=self.name,
            template=self.template_body,
            parameters=self.parameters,
            capabilities=['CAPABILITY_IAM'],
        )
        return response

    def delete(self, retain_resources=None):
        self.client.delete_stack(
            name=self.name, retain_resources=retain_resources
        )

    @property
    def events(self):
        response = self.client.describe_stack_events(name=self.name)
        return response

    @property
    def status(self):
        response = self.client.describe_stack(name=self.name)
        return response

    @property
    def resources(self):
        response = self.client.list_stack_resources(name=self.name)
        return response


def echo_response(mapping):
    m = [[k, v] for k, v in mapping.items() if k != 'ResponseMetadata']
    click.echo(tabulate(m))


def echo_table(sequence_of_dict, columns, filters=None, pager=False):
    def filter_for(key):
        default = human_date if 'time' in key.lower() else lambda x: x
        return (filters or {}).get(key, default)
    data = [
        [filter_for(column)(element.get(column)) for column in columns]
        for element in sequence_of_dict
    ]
    output = tabulate(data, headers=columns)
    if pager:
        click.echo_via_pager(output)
    else:
        click.echo(output)


def human_date(date):
    return arrow.get(date).humanize()


class HandleBotoError(object):
    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        if type is botocore.exceptions.ClientError:
            raise click.ClickException(str(value))


# Commands


@click.group()
def cli():  # pragma: no cover
    pass


@click.command(name='list')
@handle_exception
def _list():
    client = CfnClient()
    columns = ['StackName', 'CreationTime', 'LastUpdatedTime', 'StackStatus']
    with HandleBotoError():
        echo_table(
            client.list_stacks(status_filter=client.STACK_STATUS_ACTIVE),
            columns=columns,
            filters={'CreationTime': human_date, 'LastUpdatedTime': human_date}
        )


@click.command()
@click.argument('stack')
@handle_exception
def create(stack):
    client = CfnClient()
    stack = Stack(client, stack)
    with HandleBotoError():
        response = stack.create()
    echo_response(response)


@click.command()
@click.argument('stack')
@handle_exception
def update(stack):
    client = CfnClient()
    stack = Stack(client, stack)
    with HandleBotoError():
        response = stack.update()
    echo_response(response)


@click.command()
@click.argument('stack')
@handle_exception
def events(stack):
    client = CfnClient()
    stack = Stack(client, stack)
    columns = [
        'LogicalResourceId',
        'ResourceStatus',
        'ResourceStatusReason',
        'Timestamp',
    ]
    with HandleBotoError():
        echo_table(
            stack.events,
            columns=columns,
            filters={'Timestamp': human_date},
            pager=True,
        )


@click.command()
@click.argument('stack')
@handle_exception
def show(stack):
    client = CfnClient()
    stack = Stack(client, stack)
    echo_response(stack.status)


@click.command()
@click.argument('stack')
@handle_exception
def resources(stack):
    client = CfnClient()
    stack = Stack(client, stack)
    columns = [
        'ResourceType',
        'PhysicalResourceId',
        'LastUpdatedTimestamp',
        'ResourceStatus',
        'LogicalResourceId',
    ]
    with HandleBotoError():
        echo_table(
            stack.resources,
            columns=columns,
            pager=True,
        )


@click.command()
@click.argument('template-file')
@handle_exception
def validate(template_file):
    client = CfnClient()
    template = Template(client, template_file)
    with HandleBotoError():
        response = template.validate()
    echo_response(response)


@click.command()
@click.argument('stack')
@click.option('--retain', multiple=True)
@handle_exception
def delete(stack, retain):
    client = CfnClient()
    stack = Stack(client, stack)
    stack.delete(retain_resources=retain)


cli.add_command(_list)
cli.add_command(create)
cli.add_command(update)
cli.add_command(delete)
cli.add_command(events)
cli.add_command(show)
cli.add_command(resources)
cli.add_command(validate)
