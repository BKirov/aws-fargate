import pulumi
from pulumi import export, ResourceOptions
import base64
import pulumi_aws as aws
import json
import pulumi_docker as docker
config = pulumi.Config()
username = config.require('bkirov)
password = config.require_secret('passsssss')

def get_registry(pwd):
    return docker.ImageRegistry(
        server='docker.io',
        username=username,
        password=password,
    )
registry_info=accessToken.apply(get_registry_info)
#ETO TUKA MI GURMI ..........
image = docker.Image('bkirov-fargate,
    build='app',
    image_name=image_name,
    registry=registry_info,
)
####ProblemS#############









cluster = aws.ecs.Cluster('ECSClusterRRR')


default_vpc = aws.ec2.get_vpc(default=True)
default_vpc_subnets = aws.ec2.get_subnet_ids(vpc_id=default_vpc.id)

# създаваме секюрити група и егрес
group = aws.ec2.SecurityGroup('web-secgrp',
	vpc_id=default_vpc.id,
	description='Enable HTTP access',
	ingress=[aws.ec2.SecurityGroupIngressArgs(
		protocol='tcp',
		from_port=80,
		to_port=80,
		cidr_blocks=['0.0.0.0/0'],
	)],
  	egress=[aws.ec2.SecurityGroupEgressArgs(
		protocol='-1',
		from_port=0,
		to_port=0,
		cidr_blocks=['0.0.0.0/0'],
	)],
)

# Създаваме Лоуд Балансер който да слуша за хттп трафик на порт  80.
alb = aws.lb.LoadBalancer('app-lb',
	security_groups=[group.id],
	subnets=default_vpc_subnets.ids,
)

atg = aws.lb.TargetGroup('app-tg',
	port=80,
	protocol='HTTP',
	target_type='ip',
	vpc_id=default_vpc.id,
)

wl = aws.lb.Listener('web',
	load_balancer_arn=alb.arn,
	port=80,
	default_actions=[aws.lb.ListenerDefaultActionArgs(
		type='forward',
		target_group_arn=atg.arn,
	)],
)

# IAM роля
role = aws.iam.Role('task-exec-role',
	assume_role_policy=json.dumps({
		'Version': '2008-10-17',
		'Statement': [{
			'Sid': '',
			'Effect': 'Allow',
			'Principal': {
				'Service': 'ecs-tasks.amazonaws.com'
			},
			'Action': 'sts:AssumeRole',
		}]
	}),
)

rpa = aws.iam.RolePolicyAttachment('task-exec-policy',
	role=role.name,
	policy_arn='arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy',
)

# дефиниране на контейнера
task_definition = aws.ecs.TaskDefinition('app-task',
    family='fargate-task-definition',
    cpu='256',
    memory='512',
    network_mode='awsvpc',
    requires_compatibilities=['FARGATE'],
    execution_role_arn=role.arn,
    container_definitions=json.dumps([{
		'name': 'boby-fargate',
		'image': 'bkirov/boby-fargate',
		'portMappings': [{
			'containerPort': 80,
			'hostPort': 80,
			'protocol': 'tcp'
		}]
	}])
)

service = aws.ecs.Service('app-svc',
	cluster=cluster.arn,
    desired_count=3,
    launch_type='FARGATE',
    task_definition=task_definition.arn,
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
		assign_public_ip=True,
		subnets=default_vpc_subnets.ids,
		security_groups=[group.id],
	),
    load_balancers=[aws.ecs.ServiceLoadBalancerArgs(
		target_group_arn=atg.arn,
		container_name='boby-fargate',
		container_port=80,
	)],
    opts=ResourceOptions(depends_on=[wl]),
)

export('Adres na uslugata: ', alb.dns_name)