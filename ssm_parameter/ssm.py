import pulumi
import pulumi_aws as aws
from typing import Optional, Dict
import os

class SsmParameter(pulumi.ComponentResource):
    def __init__(self,
                 name: str,
                 value: Optional[str] = None,
                 value_from_file: Optional[str] = None,
                 type: str = "String",  # Can be String, SecureString, or StringList
                 key_id: Optional[str] = None,
                 description: Optional[str] = None,
                 tags: Optional[Dict[str, str]] = None,
                 overwrite: bool = True,
                 tier: Optional[str] = "Standard",  # Can be Standard or Advanced
                 opts: Optional[pulumi.ResourceOptions] = None):
        super().__init__('custom:aws:SsmParameter', name, None, opts)

        # Get parameter value
        if value_from_file:
            with open(value_from_file, 'r') as f:
                value = f.read().strip()

        if not value:
            raise ValueError("Either 'value' or 'value_from_file' must be provided.")

        # Create the SSM parameter
        self.parameter = aws.ssm.Parameter(
            f"{name}-param",
            name=f"/{name}",
            type=type,
            value=value,
            description=description,
            key_id=key_id if type == "SecureString" else None,
            tags=tags,
            overwrite=overwrite,
            tier=tier,
            opts=pulumi.ResourceOptions(parent=self)
        )

        self.register_outputs({
            "parameter": self.parameter
        })