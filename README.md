# Buddy, your Cloudformation/ECS valet

Opinionated tools to manage your AWS infrastructure.

## Buddy stack (`bstack`)

Manage your cloudformation stacks with templates and stack definition stored
as yaml files.

Examples:

```shell
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
```

## Buddy cluster (`bcluster`)

Deploy and manage services on AWS ECS.

```shell
$ cat .aws/cluster.yaml
targets:
  production:
    cluster: production
    service: service-Service-1234567890JVM
    task: HelloWorld
    environment: production
tasks:
  HelloWorld:
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
```

