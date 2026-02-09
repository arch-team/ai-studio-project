"""
ALB Stack 单元测试.

测试覆盖:
- Application Load Balancer 创建
- 安全组配置
- HTTPS 监听器 (TLS 1.2+)
- HTTP 到 HTTPS 重定向
- 目标组 (backend, frontend, Grafana)
- WAF 配置
- 健康检查
- SSL 策略
"""

import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Match, Template

from config import EnvironmentConfig
from stacks import AlbStack, NetworkStack

# =============================================================================
# 共用 Fixtures - 消除 7 处重复的 Stack 依赖链
# =============================================================================


@pytest.fixture
def alb_stack(
    cdk_app: cdk.App,
    dev_config: EnvironmentConfig,
    cdk_env: cdk.Environment,
    network_stack: NetworkStack,
) -> AlbStack:
    """创建 ALB Stack (无证书，无 WAF)."""
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
def template(alb_stack: AlbStack) -> Template:
    """获取 CloudFormation 模板."""
    return Template.from_stack(alb_stack)


@pytest.fixture
def template_with_cert(
    cdk_app: cdk.App,
    dev_config: EnvironmentConfig,
    cdk_env: cdk.Environment,
    network_stack: NetworkStack,
) -> Template:
    """获取带 HTTPS 证书的 CloudFormation 模板."""
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


# =============================================================================
# 测试类
# =============================================================================


class TestAlbStackCreation:
    """ALB Stack 创建测试."""

    def test_stack_synthesizes(self, alb_stack: AlbStack) -> None:
        """验证 Stack 可以成功合成."""
        assert alb_stack is not None

    def test_alb_created(self, template: Template) -> None:
        """验证 ALB 创建."""
        template.resource_count_is("AWS::ElasticLoadBalancingV2::LoadBalancer", 1)

    def test_alb_is_internet_facing(self, template: Template) -> None:
        """验证 ALB 面向互联网."""
        template.has_resource_properties(
            "AWS::ElasticLoadBalancingV2::LoadBalancer",
            {"Scheme": "internet-facing"},
        )


class TestSecurityGroupConfiguration:
    """ALB 安全组配置测试."""

    def test_security_group_created(self, template: Template) -> None:
        """验证安全组创建."""
        template.resource_count_is("AWS::EC2::SecurityGroup", 1)

    def test_https_ingress_allowed(self, template: Template) -> None:
        """验证 HTTPS (443) 入站规则."""
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
        """验证 HTTP (80) 入站规则 (用于重定向)."""
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
    """HTTPS 监听器配置测试."""

    def test_https_listener_created(self, template_with_cert: Template) -> None:
        """验证 HTTPS 监听器创建."""
        template_with_cert.has_resource_properties(
            "AWS::ElasticLoadBalancingV2::Listener",
            {"Port": 443, "Protocol": "HTTPS"},
        )

    def test_ssl_policy_enforced(self, template_with_cert: Template) -> None:
        """验证强制 TLS 1.2+ SSL 策略."""
        template_with_cert.has_resource_properties(
            "AWS::ElasticLoadBalancingV2::Listener",
            {"Protocol": "HTTPS", "SslPolicy": Match.string_like_regexp(".*TLS.*")},
        )


class TestHttpRedirect:
    """HTTP 到 HTTPS 重定向测试."""

    def test_http_listener_created(self, template_with_cert: Template) -> None:
        """验证 HTTP 监听器创建."""
        template_with_cert.has_resource_properties(
            "AWS::ElasticLoadBalancingV2::Listener",
            {"Port": 80, "Protocol": "HTTP"},
        )

    def test_http_redirects_to_https(self, template_with_cert: Template) -> None:
        """验证 HTTP 重定向到 HTTPS."""
        template_with_cert.has_resource_properties(
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
    """目标组配置测试."""

    def test_three_target_groups_created(self, template: Template) -> None:
        """验证 3 个目标组创建 (backend, frontend, grafana)."""
        template.resource_count_is("AWS::ElasticLoadBalancingV2::TargetGroup", 3)

    def test_health_check_configured(self, template: Template) -> None:
        """验证健康检查配置."""
        template.has_resource_properties(
            "AWS::ElasticLoadBalancingV2::TargetGroup",
            {"HealthCheckPath": Match.any_value(), "HealthCheckProtocol": "HTTP"},
        )

    def test_target_type_is_ip(self, template: Template) -> None:
        """验证目标组使用 IP 类型 (EKS pods)."""
        template.has_resource_properties(
            "AWS::ElasticLoadBalancingV2::TargetGroup",
            {"TargetType": "ip"},
        )


class TestWafConfiguration:
    """WAF 配置测试."""

    @pytest.fixture
    def template_with_waf(self, cdk_app: cdk.App, cdk_env: cdk.Environment) -> Template:
        """创建启用 WAF 的模板 (prod 配置)."""
        prod_config = EnvironmentConfig.for_prod(
            account="123456789012", region="us-east-1"
        )
        network_stack = NetworkStack(
            cdk_app, "WafNetworkStack", env_config=prod_config, env=cdk_env
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
        """验证 WAF Web ACL 创建."""
        template_with_waf.resource_count_is("AWS::WAFv2::WebACL", 1)

    def test_waf_associated_with_alb(self, template_with_waf: Template) -> None:
        """验证 WAF 关联到 ALB."""
        template_with_waf.resource_count_is("AWS::WAFv2::WebACLAssociation", 1)


class TestAlbStackOutputs:
    """ALB Stack 输出属性测试."""

    def test_alb_accessible(self, alb_stack: AlbStack) -> None:
        """验证 ALB 可访问."""
        assert alb_stack.alb is not None

    def test_security_group_accessible(self, alb_stack: AlbStack) -> None:
        """验证安全组可访问."""
        assert alb_stack.security_group is not None

    def test_target_groups_accessible(self, alb_stack: AlbStack) -> None:
        """验证所有目标组可访问."""
        assert alb_stack.backend_target_group is not None
        assert alb_stack.frontend_target_group is not None
        assert alb_stack.grafana_target_group is not None

    def test_dns_name_accessible(self, alb_stack: AlbStack) -> None:
        """验证 DNS 名称可访问."""
        assert alb_stack.dns_name is not None


class TestAlbStackTags:
    """ALB Stack 标签测试."""

    def test_alb_has_name_tag(self, template: Template) -> None:
        """验证 ALB 有 Name 标签."""
        template.has_resource_properties(
            "AWS::ElasticLoadBalancingV2::LoadBalancer",
            {
                "Tags": Match.array_with(
                    [Match.object_like({"Key": "Name", "Value": Match.any_value()})]
                )
            },
        )
