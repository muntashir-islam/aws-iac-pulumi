import pulumi
import pulumi_aws as aws
from typing import Dict, Optional, Any

class VpcAcl(pulumi.ComponentResource):
    def __init__(self,
                 name: str,
                 vpc: aws.ec2.Vpc,
                 subnets: Dict[str, Dict[str, str]],  # e.g., {"subnet-a": {"id": "..."}}
                 rules: Dict[str, Dict[str, Any]],
                 tags: Optional[Dict[str, str]] = None,
                 opts: Optional[pulumi.ResourceOptions] = None):
        super().__init__('custom:aws:VpcAcl', name, None, opts)

        subnet_ids = [subnet["id"] for subnet in subnets.values()]

        # Create the Network ACL
        nacl = aws.ec2.NetworkAcl(f"{name}-nacl",
            vpc_id=vpc.id,
            subnet_ids=subnet_ids,
            tags={**(tags or {}), "Name": name},
            opts=pulumi.ResourceOptions(parent=self)
        )

        # Add rules
        for key, rule in rules.items():
            base_args = {
                "network_acl_id": nacl.id,
                "rule_number": rule["number"],
                "rule_action": rule["action"],
                "protocol": rule["protocol"],
                "from_port": rule.get("from_port", 0),
                "to_port": rule.get("to_port", 0),
                "cidr_block": rule.get("ipv4_cidr"),
                "ipv6_cidr_block": rule.get("ipv6_cidr"),
                "icmp_type": rule.get("icmp_type", 0),
                "icmp_code": rule.get("icmp_code", 0),
                "egress": rule["direction"] == "egress",
            }

            aws.ec2.NetworkAclRule(f"{name}-rule-{key}",
                **base_args,
                opts=pulumi.ResourceOptions(parent=nacl)
            )

        self.nacl = nacl
        self.register_outputs({"network_acl_id": self.nacl.id})
