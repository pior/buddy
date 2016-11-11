import boto3


class CfnClient(object):
    def __init__(self, **session_args):
        session = boto3.session.Session(**session_args)
        self.boto = session.client(u'cloudformation')

    def _format_parameters(self, params):
        def one(key, value):
            p = {'ParameterKey': key}
            if value is None:
                p['UsePreviousValue'] = True
            else:
                p['ParameterValue'] = value
            return p
        return [one(key, value) for key, value in params.items()]

    def create_stack(self, name, template, parameters, capabilities):
        parameters = self._format_parameters(parameters)
        return self.boto.create_stack(
            StackName=name,
            TemplateBody=template,
            Parameters=parameters,
            Capabilities=capabilities,
        )

    def update_stack(self, name, template, parameters, capabilities):
        parameters = self._format_parameters(parameters)
        return self.boto.update_stack(
            StackName=name,
            TemplateBody=template,
            Parameters=parameters,
            Capabilities=capabilities,
        )

    def delete_stack(self, name, retain_resources):
        opts = {}
        if retain_resources:
            opts['RetainResources'] = retain_resources
        return self.boto.delete_stack(StackName=name, **opts)

    STACK_STATUS_ACTIVE = [
        'CREATE_IN_PROGRESS',
        'CREATE_FAILED',
        'CREATE_COMPLETE',
        'ROLLBACK_IN_PROGRESS',
        'ROLLBACK_FAILED',
        'ROLLBACK_COMPLETE',
        'DELETE_IN_PROGRESS',
        'DELETE_FAILED',
        'UPDATE_IN_PROGRESS',
        'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS',
        'UPDATE_COMPLETE',
        'UPDATE_ROLLBACK_IN_PROGRESS',
        'UPDATE_ROLLBACK_FAILED',
        'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS',
        'UPDATE_ROLLBACK_COMPLETE',
    ]

    def list_stacks(self, status_filter):
        paginator = self.boto.get_paginator('list_stacks')
        pages = paginator.paginate(StackStatusFilter=status_filter)
        return [e for p in pages for e in p['StackSummaries']]

    def describe_stack(self, name):
        return self.boto.describe_stacks(StackName=name)['Stacks'][0]

    def describe_stack_events(self, name):
        paginator = self.boto.get_paginator('describe_stack_events')
        pages = paginator.paginate(StackName=name)
        return [e for p in pages for e in p['StackEvents']]

    def list_stack_resources(self, name):
        paginator = self.boto.get_paginator('list_stack_resources')
        pages = paginator.paginate(StackName=name)
        return [e for p in pages for e in p['StackResourceSummaries']]

    def validate_template(self, template_body):
        return self.boto.validate_template(TemplateBody=template_body)


class EcsClient(object):
    def __init__(self, **session_args):
        session = boto3.session.Session(**session_args)
        self.boto = session.client(u'ecs')

    def describe_services(self, cluster_name, service_name):
        return self.boto.describe_services(
            cluster=cluster_name, services=[service_name])

    def describe_task_definition(self, task_definition_arn):
        return self.boto.describe_task_definition(
            taskDefinition=task_definition_arn)

    def list_tasks(self, cluster_name, service_name):
        return self.boto.list_tasks(
            cluster=cluster_name, serviceName=service_name)

    def describe_tasks(self, cluster_name, task_arns):
        return self.boto.describe_tasks(
            cluster=cluster_name, tasks=task_arns)

    def register_task_definition(self, family, containers, volumes=None):
        args = {}
        if volumes:
            args['volumes'] = volumes
        return self.boto.register_task_definition(
            family=family, containerDefinitions=containers, **args)

    def deregister_task_definition(self, task_definition_arn):
        return self.boto.deregister_task_definition(
            taskDefinition=task_definition_arn)

    def update_service(self, cluster, service, task_definition):
        return self.boto.update_service(
            cluster=cluster,
            service=service,
            taskDefinition=task_definition,
        )

    def run_task(self, cluster, task_definition, count, started_by, overrides):
        return self.boto.run_task(
            cluster=cluster,
            taskDefinition=task_definition,
            count=count,
            startedBy=started_by,
            overrides=overrides
        )
