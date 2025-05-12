import pulumi
import pulumi_aws as aws
from typing import Optional, Dict

class VpcOnly(pulumi.ComponentResource):
    def __init__(self,
                 name: str,
                 cidr_block: str,
                 enable_dns_support: bool = True,
                 enable_dns_hostnames: bool = True,
                 instance_tenancy: Optional[str] = "default",  # default or dedicated
                 tags: Optional[Dict[str, str]] = None,
                 opts: Optional[pulumi.ResourceOptions] = None):
        super().__init__('custom:aws:VpcOnly', name, None, opts)

        self.vpc = aws.ec2.Vpc(
            resource_name=f"{name}-vpc",
            cidr_block=cidr_block,
            enable_dns_support=enable_dns_support,
            enable_dns_hostnames=enable_dns_hostnames,
            instance_tenancy=instance_tenancy,
            tags={**(tags or {}), "Name": name},
            opts=pulumi.ResourceOptions(parent=self)
        )

        self.register_outputs({
            "vpc": self.vpc
        })
