import pulumi
import pulumi_aws as aws
from pulumi_aws import iam

class KmsModule:
    def __init__(self,
                 name: str,
                 enable_iam_permissions: bool = True,
                 enable_key_rotation: bool = True,
                 key_rotation_days: int = 365,
                 delete_hold: int = 7,
                 key_spec: str = "SYMMETRIC_DEFAULT",
                 key_usage: str = "ENCRYPT_DECRYPT",
                 enabled_cloudwatch_log_delivery: bool = False,
                 enabled_route53_dnssec: bool = False,
                 enabled_route53_dnssec_cloudwatch_logs: bool = False,
                 enabled_service_identifiers: list[str] = [],
                 additional_cloudwatch_log_delivery_arns: list[str] = [],
                 custom_key_policy: dict = None):

        # AWS identity/region info
        identity = aws.get_caller_identity()
        region = aws.get_region()
        partition = aws.get_partition()

        statements = []

        if enable_iam_permissions:
            statements.append(iam.GetPolicyDocumentStatementArgs(
                sid="EnableIAMUserPermissions",
                actions=["kms:*"],
                resources=["*"],
                principals=[iam.GetPolicyDocumentStatementPrincipalArgs(
                    type="AWS",
                    identifiers=[f"arn:{partition.partition}:iam::{identity.account_id}:root"]
                )]
            ))

        # CloudWatch statement
        if enabled_cloudwatch_log_delivery:
            cw_arns = [
                f"arn:{partition.partition}:logs:{region.name}:{identity.account_id}:*{name}*"
            ]
            if enabled_route53_dnssec_cloudwatch_logs:
                cw_arns.append(f"arn:{partition.partition}:logs:{region.name}:{identity.account_id}:log-group:/aws/route53/*")
            cw_arns += additional_cloudwatch_log_delivery_arns

            statements.append(iam.GetPolicyDocumentStatementArgs(
                sid="CloudWatchAccess",
                actions=[
                    "kms:Encrypt*", "kms:Decrypt*", "kms:ReEncrypt*",
                    "kms:GenerateDataKey*", "kms:Describe*"
                ],
                resources=["*"],
                principals=[iam.GetPolicyDocumentStatementPrincipalArgs(
                    type="Service",
                    identifiers=[f"logs.{region.name}.amazonaws.com"]
                )],
                conditions=[{
                    "test": "ArnLike",
                    "variable": "kms:EncryptionContext:aws:logs:arn",
                    "values": cw_arns
                }]
            ))

        # Add additional statements here for:
        # - custom_key_policy
        # - route53 DNSSEC
        # - general AWS service access

        policy_doc = iam.get_policy_document(statements=statements)

        # Create KMS Key
        self.kms_key = aws.kms.Key(f"{name}-key",
            description=f"CMK for stack {name}",
            deletion_window_in_days=delete_hold,
            enable_key_rotation=enable_key_rotation,
            rotation_period_in_days=key_rotation_days if enable_key_rotation else None,
            customer_master_key_spec=key_spec,
            key_usage=key_usage,
            policy=policy_doc.json,
            tags={"Name": name}
        )

        self.kms_alias = aws.kms.Alias(f"{name}-alias",
            name=f"alias/{name}",
            target_key_id=self.kms_key.key_id
        )
