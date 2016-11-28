
class DefinitionError(Exception):
    pass


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


def make_container_definition(definition, name, image, environment, context):
    props = definition['properties'].copy()
    props['name'] = name
    props.setdefault('image', str(image))

    def get_variables(name):
        return {'name': name, 'value': environment[name]}

    required_variables = definition.get('environment')
    if required_variables:
        try:
            props['environment'] = [
                get_variables(v)
                for v in required_variables
            ]
        except KeyError as err:
            raise DefinitionError("Unknown environment variable %s" % err)

    for configurator in [cloudwatch_log_configurator]:
        props = configurator(context, props)

    return props


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

    def get_task_containers(self, image, context):
        def make(container_name):
            return make_container_definition(
                definition=self.container_definitions[container_name],
                name=container_name,
                image=image,
                environment=self.environment,
                context=context,
            )
        return [make(el) for el in self.task['containers']]
