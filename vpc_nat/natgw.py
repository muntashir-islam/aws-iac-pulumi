import pulumi
import pulumi_aws as aws
from typing import List, Dict, Optional

class NatGateway(pulumi.ComponentResource):
    def __init__(self,
                 name: str,
                 public_subnet_ids: List[str],
                 private_route_table_ids: List[str],
                 tags: Optional[Dict[str, str]] = None,
                 opts: Optional[pulumi.ResourceOptions] = None):
        super().__init__('custom:aws:NatGateway', name, None, opts)

        if len(public_subnet_ids) != len(private_route_table_ids):
            raise ValueError("Length of public_subnet_ids and private_route_table_ids must match (1:1 mapping)")

        self.eips = []
        self.nat_gateways = []

        for i in range(len(public_subnet_ids)):
            eip = aws.ec2.Eip(f"{name}-eip-{i}",
                tags={**(tags or {}), "Name": f"{name}-eip-{i}"},
                opts=pulumi.ResourceOptions(parent=self)
            )

            natgw = aws.ec2.NatGateway(f"{name}-natgw-{i}",
                subnet_id=public_subnet_ids[i],
                allocation_id=eip.id,
                tags={**(tags or {}), "Name": f"{name}-natgw-{i}"},
                opts=pulumi.ResourceOptions(parent=self)
            )

            aws.ec2.Route(f"{name}-nat-route-{i}",
                route_table_id=private_route_table_ids[i],
                destination_cidr_block="0.0.0.0/0",
                nat_gateway_id=natgw.id,
                opts=pulumi.ResourceOptions(parent=self)
            )

            self.eips.append(eip)
            self.nat_gateways.append(natgw)

        self.register_outputs({
            "eip_ids": [e.id for e in self.eips],
            "nat_gateway_ids": [n.id for n in self.nat_gateways]
        })
