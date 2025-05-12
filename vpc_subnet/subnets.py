import pulumi
import pulumi_aws as aws
from typing import List, Optional, Dict

class VpcSubnets(pulumi.ComponentResource):
    def __init__(self,
                 name: str,
                 vpc_id: str,
                 cidr_block_public: str,
                 cidr_block_private: str,
                 azs: List[str],
                 create_public_subnets: bool = True,
                 enable_ipv6: bool = False,
                 tags: Optional[Dict[str, str]] = None,
                 opts: Optional[pulumi.ResourceOptions] = None):
        super().__init__('custom:aws:VpcSubnets', name, None, opts)

        self.public_subnet_ids = []
        self.private_subnet_ids = []
        self.private_route_table_ids = []

        ipv6_cidr_block = None
        if enable_ipv6:
            ipv6_assoc = aws.ec2.VpcIpv6CidrBlockAssociation(
                f"{name}-ipv6-assoc",
                vpc_id=vpc_id,
                amazon_provided_ipv6_cidr_block=True,
                opts=pulumi.ResourceOptions(parent=self)
            )
            ipv6_cidr_block = ipv6_assoc.ipv6_cidr_block

        if create_public_subnets:
            self.igw = aws.ec2.InternetGateway(
                f"{name}-igw",
                vpc_id=vpc_id,
                tags={**(tags or {}), "Name": f"{name}-igw"},
                opts=pulumi.ResourceOptions(parent=self)
            )

            self.public_route_table = aws.ec2.RouteTable(
                f"{name}-public-rt",
                vpc_id=vpc_id,
                routes=[{
                    "cidr_block": "0.0.0.0/0",
                    "gateway_id": self.igw.id,
                }] + ([{
                    "ipv6_cidr_block": "::/0",
                    "gateway_id": self.igw.id,
                }] if enable_ipv6 else []),
                tags={**(tags or {}), "Name": f"{name}-public-rt"},
                opts=pulumi.ResourceOptions(parent=self)
            )

        for i, az in enumerate(azs):
            if create_public_subnets:
                public_subnet = aws.ec2.Subnet(
                    f"{name}-public-subnet-{az}",
                    vpc_id=vpc_id,
                    cidr_block=self._cidr_offset(cidr_block_public, i),
                    availability_zone=az,
                    map_public_ip_on_launch=True,
                    assign_ipv6_address_on_creation=enable_ipv6,
                    ipv6_cidr_block=(f"{ipv6_cidr_block.split('::')[0]}:{i * 10}::/64" if enable_ipv6 else None),
                    tags={**(tags or {}), "Name": f"{name}-public-{az}"},
                    opts=pulumi.ResourceOptions(parent=self)
                )
                self.public_subnet_ids.append(public_subnet.id)

                aws.ec2.RouteTableAssociation(
                    f"{name}-public-rt-assoc-{az}",
                    subnet_id=public_subnet.id,
                    route_table_id=self.public_route_table.id,
                    opts=pulumi.ResourceOptions(parent=self)
                )

            private_subnet = aws.ec2.Subnet(
                f"{name}-private-subnet-{az}",
                vpc_id=vpc_id,
                cidr_block=self._cidr_offset(cidr_block_private, i),
                availability_zone=az,
                map_public_ip_on_launch=False,
                assign_ipv6_address_on_creation=enable_ipv6,
                ipv6_cidr_block=(f"{ipv6_cidr_block.split('::')[0]}:{100 + i * 10}::/64" if enable_ipv6 else None),
                tags={**(tags or {}), "Name": f"{name}-private-{az}"},
                opts=pulumi.ResourceOptions(parent=self)
            )
            self.private_subnet_ids.append(private_subnet.id)

            private_rt = aws.ec2.RouteTable(
                f"{name}-private-rt-{az}",
                vpc_id=vpc_id,
                tags={**(tags or {}), "Name": f"{name}-private-rt-{az}"},
                opts=pulumi.ResourceOptions(parent=self)
            )
            self.private_route_table_ids.append(private_rt.id)

            aws.ec2.RouteTableAssociation(
                f"{name}-private-rt-assoc-{az}",
                subnet_id=private_subnet.id,
                route_table_id=private_rt.id,
                opts=pulumi.ResourceOptions(parent=self)
            )

        self.register_outputs({
            "public_subnet_ids": self.public_subnet_ids,
            "private_subnet_ids": self.private_subnet_ids,
            "private_route_table_ids": self.private_route_table_ids
        })

    def _cidr_offset(self, base_cidr: str, index: int) -> str:
        parts = base_cidr.split(".")
        parts[2] = str(int(parts[2]) + index)
        return ".".join(parts)