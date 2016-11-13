====================================
Buddy, your Cloudformation/ECS valet
====================================

*Opinionated tools to manage your AWS infrastructure.*

---------------------------------
Manage your cloudformation stacks
---------------------------------

Cloudformation stacks are described by *stack files*

- YAML format
- Specify which Cloudformation *template* to use
- Specify the parameters to use when creating/updating stacks

Examples:

.. code:: shell

  $ bstack list
  ...

  $ cat .aws/production.yaml
  name: helloworld
  template: service.yaml

  $ cat service.yaml
  AWSTemplateFormatVersion: 2010-09-09
  Description: Handle Service
  Resources:
  ...

  $ bstack create .aws/production.yaml
  $ bstack events helloworld  # or bstack events .aws/production.yaml
  $ bstack resources helloworld
  $ bstack update .aws/production.yaml
  $ bstack delete helloworld

-------------------------------------
Manage your services and tasks on ECS
-------------------------------------

Alpha: in development. Currently only implement deploy action for
continuous deployment on ECS.

.. code:: shell

  $ cat .aws/cluster.yaml
  targets:
    production:
      cluster: production
      service: service-Service-1234567890JVM
      task: helloworld
      environment: production
  tasks:
    helloworld:
      containers:
        - http
        - app
        - celery
  environments:
    production:
      SECRET_KEY: s3cr3t
      DATABASE_URL: postgis://user:pass@host/name
      REDIS_URL: redis://host:6379
  containers:
    http:
      properties:
        memory: 100
        cpu: 100
        portMappings:
          - containerPort: 80
            hostPort: 0  # 0 = dynamic port
        links: ['app']
        command: ['nginx', '-g', 'daemon off;']
    app:
      properties:
        memory: 200
        cpu: 200
      environment:
        [SECRET_KEY, DATABASE_URL, REDIS_URL]
    celery:
      properties:
        memory: 150
        cpu: 100
        command: ['celery', '-A', 'helloworld', 'worker', '-B', '-l', 'info']
      environment:
        [DATABASE_URL, REDIS_URL]

  $ bcluster deploy .aws/cluster.yaml production registry/myapp:latest a1b2c3d4
  Definition:
  [{'command': ['nginx', '-g', 'daemon off;'],
    'cpu': 100,
    ...
  ]

  Register task
  Registered task: arn:aws:ecs:us-east-1:000000000000:task-definition/helloworld:123
  Deploying...
  Wait: deployment in progress
  arn:aws:ecs:us-east-1:000000000000:task-definition/helloworld:123 - PRIMARY - running: 0
  arn:aws:ecs:us-east-1:000000000000:task-definition/helloworld:122 - ACTIVE - running: 2

  Wait: deployment in progress
  arn:aws:ecs:us-east-1:000000000000:task-definition/helloworld:123 - PRIMARY - running: 0
  arn:aws:ecs:us-east-1:000000000000:task-definition/helloworld:122 - ACTIVE - running: 2

  Wait: deployment in progress
  arn:aws:ecs:us-east-1:000000000000:task-definition/helloworld:123 - PRIMARY - running: 2
  arn:aws:ecs:us-east-1:000000000000:task-definition/helloworld:122 - ACTIVE - running: 0

  Final state:
  ...

  Success

-----------
Development
-----------

Running tests

.. code:: shell

  $ git clone git@github.com:pior/buddy.git
  ...
  $ mkvirtualenv buddy -p python3
  ...
  $ pip install -U -r requirements-test.txt
  ...
  $ pip install -e .
  ...
  $ pytest
