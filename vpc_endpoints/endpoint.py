import pulumi
import pulumi_aws as aws
from typing import Optional, List, Dict

class VpcEndpoint(pulumi.ComponentResource):
    def __init__(self,
                 name: str,
                 vpc: aws.ec2.Vpc,
                 endpoint_service: str,
                 endpoint_type: str,
                 allowed_subnets: Optional[List[aws.ec2.Subnet]] = None,
                 gateway_route_tables: Optional[List[aws.ec2.RouteTable]] = None,
                 tags: Optional[Dict[str, str]] = None,
                 opts: Optional[pulumi.ResourceOptions] = None):
        super().__init__("custom:network:VpcEndpoint", name, {}, opts)

        region = aws.get_region()

        lower_type = endpoint_type.lower()
        is_interface = lower_type == "interface"
        is_gateway = lower_type == "gateway"

        # Security group for interface endpoints
        sg = None
        if is_interface:
            sg = aws.ec2.SecurityGroup(
                f"{name}-sg",
                name=f"{name}-sg",
                description=f"Security group for VPC endpoint {name}",
                vpc_id=vpc.id,
                tags={"Name": f"{name}-sg", **(tags or {})},
                opts=pulumi.ResourceOptions(parent=self)
            )

        # Replace "__REGION__" with actual region
        service_name = endpoint_service.replace("__REGION__", region.name)

        endpoint = aws.ec2.VpcEndpoint(
            f"{name}-endpoint",
            vpc_id=vpc.id,
            vpc_endpoint_type=endpoint_type.title(),
            service_name=service_name,
            private_dns_enabled=is_interface,
            subnet_ids=allowed_subnets if is_interface else None,
            route_table_ids=gateway_route_tables if is_gateway else None,
            security_group_ids=[sg.id] if is_interface and sg else None,
            tags={"Name": name, **(tags or {})},
            opts=pulumi.ResourceOptions(parent=self)
        )

        self.endpoint = endpoint
        self.register_outputs({
            "endpoint": endpoint,
            "security_group": sg
        })
