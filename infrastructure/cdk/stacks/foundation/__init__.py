"""Foundation layer stacks - VPC and IAM base infrastructure."""

from .iam_stack import IamStack
from .network_stack import NetworkStack

__all__ = ["NetworkStack", "IamStack"]
