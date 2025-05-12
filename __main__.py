"""An AWS Python Pulumi program"""

import pulumi
from kms.kms import KmsModule
from ssm_parameter.ssm import SsmParameter
from secret_manager.secret_manager import SecretManagerSecret
from vpc.vpc import VpcOnly
from vpc_subnet.subnets import VpcSubnets
from vpc_nat.natgw import NatGateway
from vpc_endpoints.endpoint import VpcEndpoint
from vpc_acl.acl import VpcAcl

kms = KmsModule(name="myapp", enable_iam_permissions=True, enable_key_rotation=True)

pulumi.export("kms_key_arn", kms.kms_key.arn)

# Call ssm Param and add some parameter into ssm
param = SsmParameter("db-password",
    value="super-secret-password",
    type="SecureString",
    key_id= kms.kms_key.id,
    tags={"App": "backend"},
)
pulumi.export("ssm_param_name", param.parameter.name)
pulumi.export("ssm_param_version", param.parameter.version)

secret = SecretManagerSecret("db-credentialsv2",
    secret_value={"username": "admin", "password": "super-secret"},
    description="Database credentials for app",
    kms_key_id=kms.kms_key.arn,
    tags={"App": "backend", "Env": "prod"},
)

pulumi.export("secret_arn", secret.secret.arn)



vpc = VpcOnly("core-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags={"Environment": "dev", "Owner": "team-network"}
)

pulumi.export("vpc_id", vpc.vpc.id)
pulumi.export("vpc_cidr", vpc.vpc.cidr_block)

config = pulumi.Config()

# Retrieve the subnetDefinitions from the config
subnet_definitions = config.require_object("subnetDefinitions")



subnet_module = VpcSubnets("app-network",
    vpc_id=vpc.vpc.id,
    cidr_block_public="10.0.1.0/24",
    cidr_block_private="10.0.101.0/24",
    azs=["us-east-2a", "us-east-2b", "us-east-2c"],
    create_public_subnets=True,
    enable_ipv6=False,
    tags={"Environment": "dev"}
)

pulumi.export("public_subnet_ids", subnet_module.public_subnet_ids)
pulumi.export("private_subnet_ids", subnet_module.private_subnet_ids)

natgw = NatGateway("my-nat",
    public_subnet_ids=subnet_module.public_subnet_ids,
    private_route_table_ids=subnet_module.private_route_table_ids,
    tags={"Environment": "dev"}
)

acl = VpcAcl(
    name=f"{pulumi.get_stack()}-public-acl",
    vpc=vpc.vpc,
    subnets={
        f"subnet-{i}": {"id": subnet} for i, subnet in enumerate(subnet_module.public_subnet_ids)
    },
    rules={
        "allow_all_egress": {
            "number": 100,
            "action": "allow",
            "direction": "egress",
            "ipv4_cidr": "0.0.0.0/0",
            "protocol": "-1",
            "from_port": 0,
            "to_port": 0
        },
        "allow_all_ingress": {
            "number": 100,
            "action": "allow",
            "direction": "ingress",
            "ipv4_cidr": "0.0.0.0/0",
            "protocol": "-1",
            "from_port": 0,
            "to_port": 0
        }
    },
    tags={"Environment": "dev"}
)

vpc_endpoint = VpcEndpoint(
    name="s3-gateway",
    vpc=vpc.vpc,
    endpoint_service="com.amazonaws.__REGION__.s3",
    endpoint_type="Gateway",
    gateway_route_tables=subnet_module.private_route_table_ids,
    tags={"Environment": "dev"}
)

interface_endpoint = VpcEndpoint(
    name="ssm-endpoint",
    vpc=vpc.vpc,
    endpoint_service="com.amazonaws.__REGION__.ssm",
    endpoint_type="Interface",
    allowed_subnets=subnet_module.private_subnet_ids,
    tags={"Environment": "dev"}
)
#
# # Create an AWS resource (S3 Bucket)
# bucket = s3.BucketV2('my-bucket-x234591')
#
# with open("text.txt", "r") as f:
#     content = f.read()
#
# obj =  s3.BucketObject('my-text-file', bucket=bucket.id, content=content)
#
# # Export the name of the bucket
# pulumi.export('bucket_name', bucket.id)
