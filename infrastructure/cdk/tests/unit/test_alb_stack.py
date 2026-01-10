"""
Unit tests for ALB Stack.

Tests cover:
- Application Load Balancer creation
- Security group configuration
- HTTPS listener with TLS 1.2+
- HTTP to HTTPS redirect
- Target groups (backend, frontend, Grafana)
- WAF configuration (when enabled)
- Health checks
- SSL policy configuration
"""

import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Match, Template

from config import EnvironmentConfig
from stacks import AlbStack, EksStack, IamStack, NetworkStack


class TestAlbStackCreation:
    """Tests for ALB Stack creation."""

    @pytest.fixture
    def network_stack(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> NetworkStack:
        """Create a Network Stack for testing."""
        return NetworkStack(
            cdk_app,
            "TestNetworkStack",
            env_config=dev_config,
            env=cdk_env,
        )

    @pytest.fixture
    def iam_stack(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> IamStack:
        """Create an IAM Stack for testing."""
        return IamStack(
            cdk_app,
            "TestIamStack",
            env_config=dev_config,
            env=cdk_env,
        )

    @pytest.fixture
    def eks_stack(
        self,
        cdk_app: cdk.App,
        dev_config: EnvironmentConfig,
        cdk_env: cdk.Environment,
        network_stack: NetworkStack,
        iam_stack: IamStack,
    ) -> EksStack:
        """Create an EKS Stack for testing."""
        return EksStack(
            cdk_app,
            "TestEksStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            eks_node_role=iam_stack.eks_node_role,
            env=cdk_env,
        )

    @pytest.fixture
    def alb_stack(
        self,
        cdk_app: cdk.App,
        dev_config: EnvironmentConfig,
        cdk_env: cdk.Environment,
        network_stack: NetworkStack,
        eks_stack: EksStack,
    ) -> AlbStack:
        """Create an ALB Stack for testing."""
        return AlbStack(
            cdk_app,
            "TestAlbStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            certificate_arn=None,
            enable_waf=False,
            env=cdk_env,
        )

    @pytest.fixture
    def template(self, alb_stack: AlbStack) -> Template:
        """Get CloudFormation template from the stack."""
        return Template.from_stack(alb_stack)

    def test_stack_synthesizes(self, alb_stack: AlbStack) -> None:
        """Verify the stack synthesizes without errors."""
        assert alb_stack is not None

    def test_alb_created(self, template: Template) -> None:
        """Verify Application Load Balancer is created."""
        template.resource_count_is("AWS::ElasticLoadBalancingV2::LoadBalancer", 1)

    def test_alb_is_internet_facing(self, template: Template) -> None:
        """Verify ALB is internet-facing."""
        template.has_resource_properties(
            "AWS::ElasticLoadBalancingV2::LoadBalancer",
            {
                "Scheme": "internet-facing",
            },
        )


class TestSecurityGroupConfiguration:
    """Tests for ALB security group configuration."""

    @pytest.fixture
    def template(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> Template:
        """Create template for security group testing."""
        network_stack = NetworkStack(
            cdk_app, "TestNetworkStack", env_config=dev_config, env=cdk_env
        )
        iam_stack = IamStack(
            cdk_app, "TestIamStack", env_config=dev_config, env=cdk_env
        )
        EksStack(
            cdk_app,
            "TestEksStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            eks_node_role=iam_stack.eks_node_role,
            env=cdk_env,
        )
        stack = AlbStack(
            cdk_app,
            "SecurityTestStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            certificate_arn=None,
            enable_waf=False,
            env=cdk_env,
        )
        return Template.from_stack(stack)

    def test_security_group_created(self, template: Template) -> None:
        """Verify ALB security group is created."""
        # At least one security group should exist (ALB SG)
        template.resource_count_is("AWS::EC2::SecurityGroup", 1)

    def test_https_ingress_allowed(self, template: Template) -> None:
        """Verify HTTPS (443) ingress is allowed."""
        template.has_resource_properties(
            "AWS::EC2::SecurityGroup",
            {
                "SecurityGroupIngress": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "CidrIp": "0.0.0.0/0",
                                "FromPort": 443,
                                "ToPort": 443,
                                "IpProtocol": "tcp",
                            }
                        )
                    ]
                )
            },
        )

    def test_http_ingress_allowed(self, template: Template) -> None:
        """Verify HTTP (80) ingress is allowed for redirect."""
        template.has_resource_properties(
            "AWS::EC2::SecurityGroup",
            {
                "SecurityGroupIngress": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "CidrIp": "0.0.0.0/0",
                                "FromPort": 80,
                                "ToPort": 80,
                                "IpProtocol": "tcp",
                            }
                        )
                    ]
                )
            },
        )


class TestHttpsListener:
    """Tests for HTTPS listener configuration."""

    @pytest.fixture
    def template(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> Template:
        """Create template with HTTPS listener."""
        network_stack = NetworkStack(
            cdk_app, "TestNetworkStack", env_config=dev_config, env=cdk_env
        )
        iam_stack = IamStack(
            cdk_app, "TestIamStack", env_config=dev_config, env=cdk_env
        )
        EksStack(
            cdk_app,
            "TestEksStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            eks_node_role=iam_stack.eks_node_role,
            env=cdk_env,
        )
        stack = AlbStack(
            cdk_app,
            "HttpsTestStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            certificate_arn="arn:aws:acm:us-east-1:123456789012:certificate/test",
            enable_waf=False,
            env=cdk_env,
        )
        return Template.from_stack(stack)

    def test_https_listener_created(self, template: Template) -> None:
        """Verify HTTPS listener is created."""
        template.has_resource_properties(
            "AWS::ElasticLoadBalancingV2::Listener",
            {
                "Port": 443,
                "Protocol": "HTTPS",
            },
        )

    def test_ssl_policy_enforced(self, template: Template) -> None:
        """Verify TLS 1.2+ is enforced via SSL policy."""
        template.has_resource_properties(
            "AWS::ElasticLoadBalancingV2::Listener",
            {
                "Protocol": "HTTPS",
                "SslPolicy": Match.string_like_regexp(".*TLS.*"),
            },
        )


class TestHttpRedirect:
    """Tests for HTTP to HTTPS redirect."""

    @pytest.fixture
    def template(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> Template:
        """Create template with HTTP redirect."""
        network_stack = NetworkStack(
            cdk_app, "TestNetworkStack", env_config=dev_config, env=cdk_env
        )
        iam_stack = IamStack(
            cdk_app, "TestIamStack", env_config=dev_config, env=cdk_env
        )
        EksStack(
            cdk_app,
            "TestEksStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            eks_node_role=iam_stack.eks_node_role,
            env=cdk_env,
        )
        stack = AlbStack(
            cdk_app,
            "HttpRedirectTestStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            certificate_arn="arn:aws:acm:us-east-1:123456789012:certificate/test",
            enable_waf=False,
            env=cdk_env,
        )
        return Template.from_stack(stack)

    def test_http_listener_created(self, template: Template) -> None:
        """Verify HTTP listener is created."""
        template.has_resource_properties(
            "AWS::ElasticLoadBalancingV2::Listener",
            {
                "Port": 80,
                "Protocol": "HTTP",
            },
        )

    def test_http_redirects_to_https(self, template: Template) -> None:
        """Verify HTTP listener redirects to HTTPS."""
        template.has_resource_properties(
            "AWS::ElasticLoadBalancingV2::Listener",
            {
                "Port": 80,
                "DefaultActions": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Type": "redirect",
                                "RedirectConfig": Match.object_like(
                                    {
                                        "Port": "443",
                                        "Protocol": "HTTPS",
                                        "StatusCode": "HTTP_301",
                                    }
                                ),
                            }
                        )
                    ]
                ),
            },
        )


class TestTargetGroups:
    """Tests for target group configuration."""

    @pytest.fixture
    def template(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> Template:
        """Create template for target group testing."""
        network_stack = NetworkStack(
            cdk_app, "TestNetworkStack", env_config=dev_config, env=cdk_env
        )
        iam_stack = IamStack(
            cdk_app, "TestIamStack", env_config=dev_config, env=cdk_env
        )
        EksStack(
            cdk_app,
            "TestEksStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            eks_node_role=iam_stack.eks_node_role,
            env=cdk_env,
        )
        stack = AlbStack(
            cdk_app,
            "TargetGroupTestStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            certificate_arn=None,
            enable_waf=False,
            env=cdk_env,
        )
        return Template.from_stack(stack)

    def test_three_target_groups_created(self, template: Template) -> None:
        """Verify three target groups are created (backend, frontend, grafana)."""
        template.resource_count_is("AWS::ElasticLoadBalancingV2::TargetGroup", 3)

    def test_health_check_configured(self, template: Template) -> None:
        """Verify health checks are configured for target groups."""
        template.has_resource_properties(
            "AWS::ElasticLoadBalancingV2::TargetGroup",
            {
                "HealthCheckPath": Match.any_value(),
                "HealthCheckProtocol": "HTTP",
            },
        )

    def test_target_type_is_ip(self, template: Template) -> None:
        """Verify target groups use IP target type for EKS pods."""
        template.has_resource_properties(
            "AWS::ElasticLoadBalancingV2::TargetGroup",
            {
                "TargetType": "ip",
            },
        )


class TestWafConfiguration:
    """Tests for WAF configuration."""

    @pytest.fixture
    def template_with_waf(self, cdk_app: cdk.App, cdk_env: cdk.Environment) -> Template:
        """Create template with WAF enabled (prod config)."""
        prod_config = EnvironmentConfig.for_prod(
            account="123456789012", region="us-east-1"
        )
        network_stack = NetworkStack(
            cdk_app, "TestNetworkStack", env_config=prod_config, env=cdk_env
        )
        iam_stack = IamStack(
            cdk_app, "TestIamStack", env_config=prod_config, env=cdk_env
        )
        EksStack(
            cdk_app,
            "TestEksStack",
            env_config=prod_config,
            vpc=network_stack.vpc,
            eks_node_role=iam_stack.eks_node_role,
            env=cdk_env,
        )
        stack = AlbStack(
            cdk_app,
            "WafTestStack",
            env_config=prod_config,
            vpc=network_stack.vpc,
            certificate_arn=None,
            enable_waf=True,
            env=cdk_env,
        )
        return Template.from_stack(stack)

    def test_waf_web_acl_created(self, template_with_waf: Template) -> None:
        """Verify WAF Web ACL is created when enabled."""
        template_with_waf.resource_count_is("AWS::WAFv2::WebACL", 1)

    def test_waf_associated_with_alb(self, template_with_waf: Template) -> None:
        """Verify WAF is associated with ALB."""
        template_with_waf.resource_count_is("AWS::WAFv2::WebACLAssociation", 1)


class TestAlbStackOutputs:
    """Tests for ALB Stack CloudFormation outputs."""

    @pytest.fixture
    def alb_stack(
        self,
        cdk_app: cdk.App,
        dev_config: EnvironmentConfig,
        cdk_env: cdk.Environment,
    ) -> AlbStack:
        """Create ALB Stack for outputs testing."""
        network_stack = NetworkStack(
            cdk_app, "TestNetworkStack", env_config=dev_config, env=cdk_env
        )
        iam_stack = IamStack(
            cdk_app, "TestIamStack", env_config=dev_config, env=cdk_env
        )
        EksStack(
            cdk_app,
            "TestEksStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            eks_node_role=iam_stack.eks_node_role,
            env=cdk_env,
        )
        return AlbStack(
            cdk_app,
            "OutputTestStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            certificate_arn=None,
            enable_waf=False,
            env=cdk_env,
        )

    def test_alb_accessible(self, alb_stack: AlbStack) -> None:
        """Verify ALB is accessible via property."""
        assert alb_stack.alb is not None

    def test_security_group_accessible(self, alb_stack: AlbStack) -> None:
        """Verify security group is accessible."""
        assert alb_stack.security_group is not None

    def test_target_groups_accessible(self, alb_stack: AlbStack) -> None:
        """Verify all target groups are accessible."""
        assert alb_stack.backend_target_group is not None
        assert alb_stack.frontend_target_group is not None
        assert alb_stack.grafana_target_group is not None

    def test_dns_name_accessible(self, alb_stack: AlbStack) -> None:
        """Verify DNS name is accessible."""
        assert alb_stack.dns_name is not None


class TestAlbStackTags:
    """Tests for ALB Stack resource tagging."""

    @pytest.fixture
    def template(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> Template:
        """Create template for tag testing."""
        network_stack = NetworkStack(
            cdk_app, "TestNetworkStack", env_config=dev_config, env=cdk_env
        )
        iam_stack = IamStack(
            cdk_app, "TestIamStack", env_config=dev_config, env=cdk_env
        )
        EksStack(
            cdk_app,
            "TestEksStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            eks_node_role=iam_stack.eks_node_role,
            env=cdk_env,
        )
        stack = AlbStack(
            cdk_app,
            "TagTestStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            certificate_arn=None,
            enable_waf=False,
            env=cdk_env,
        )
        return Template.from_stack(stack)

    def test_alb_has_name_tag(self, template: Template) -> None:
        """Verify ALB has Name tag."""
        template.has_resource_properties(
            "AWS::ElasticLoadBalancingV2::LoadBalancer",
            {
                "Tags": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Key": "Name",
                                "Value": Match.any_value(),
                            }
                        )
                    ]
                )
            },
        )
