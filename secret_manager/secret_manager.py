import pulumi
import pulumi_aws as aws
from typing import Optional, Dict, Union
import json
import os

class SecretManagerSecret(pulumi.ComponentResource):
    def __init__(self,
                 name: str,
                 secret_value: Optional[Union[str, Dict]] = None,
                 secret_value_from_file: Optional[str] = None,
                 description: Optional[str] = None,
                 kms_key_id: Optional[str] = None,
                 tags: Optional[Dict[str, str]] = None,
                 opts: Optional[pulumi.ResourceOptions] = None):
        super().__init__('custom:aws:SecretManagerSecret', name, None, opts)

        if secret_value_from_file:
            with open(secret_value_from_file, 'r') as f:
                file_content = f.read()
                try:
                    secret_value = json.loads(file_content)
                except json.JSONDecodeError:
                    secret_value = file_content.strip()

        if secret_value is None:
            raise ValueError("Either 'secret_value' or 'secret_value_from_file' must be provided.")

        # Convert dict to JSON string
        if isinstance(secret_value, dict):
            secret_value_str = json.dumps(secret_value)
        else:
            secret_value_str = secret_value

        # Create the secret (metadata)
        self.secret = aws.secretsmanager.Secret(
            f"{name}-metadata",
            name=name,
            description=description,
            kms_key_id=kms_key_id,
            tags=tags,
            opts=pulumi.ResourceOptions(parent=self)
        )

        # Create the secret value (version)
        self.secret_version = aws.secretsmanager.SecretVersion(
            f"{name}-version",
            secret_id=self.secret.id,
            secret_string=secret_value_str,
            opts=pulumi.ResourceOptions(parent=self)
        )

        self.register_outputs({
            "secret": self.secret,
            "version": self.secret_version,
        })
