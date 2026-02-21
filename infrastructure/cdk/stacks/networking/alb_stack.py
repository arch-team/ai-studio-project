"""ALB Stack — Application Load Balancer with TLS 终端。

参考: spec.md FR-018 (传输层加密要求)
"""

from typing import Any

import aws_cdk as cdk
from aws_cdk import Duration
from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from aws_cdk import aws_wafv2 as wafv2

from config import EnvironmentConfig, EnvironmentType
from constructs import Construct
from utils.outputs import create_output


class AlbStack(cdk.Stack):
    """ALB Stack — Internet-facing ALB, TLS 终端, WAF 集成。"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_config: EnvironmentConfig,
        vpc: ec2.IVpc,
        certificate_arn: str | None = None,
        enable_waf: bool = False,
        **kwargs: Any,
    ) -> None:
        # certificate_arn 为 None 时进入 HTTP-only 模式 (dev 环境)
        super().__init__(scope, construct_id, **kwargs)

        self.env_config = env_config
        self._vpc = vpc
        self._certificate_arn = certificate_arn
        self._enable_waf = enable_waf

        # Dev 环境无证书时降级为 HTTP-only 模式
        self._https_enabled = (
            bool(certificate_arn) or env_config.name != EnvironmentType.DEV
        )

        self._security_group = self._create_security_group()
        self._alb = self._create_alb()

        self._https_listener: elbv2.ApplicationListener | None = None
        if self._https_enabled and certificate_arn:
            self._https_listener = self._create_https_listener()
            self._create_http_redirect()
        else:
            self._http_listener = self._create_http_listener()

        self._create_target_groups()

        if self._enable_waf:
            self._create_waf()

        self._create_outputs()

    def _create_security_group(self) -> ec2.SecurityGroup:
        """创建 ALB 安全组，允许公网 HTTPS (443) 和 HTTP (80) 入站。"""
        sg = ec2.SecurityGroup(
            self,
            "AlbSecurityGroup",
            vpc=self._vpc,
            description="Security group for Application Load Balancer",
            allow_all_outbound=True,
        )

        sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(443),
            description="Allow HTTPS from internet",
        )

        sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(80),
            description="Allow HTTP from internet (redirect to HTTPS)",
        )

        cdk.Tags.of(sg).add("Name", f"{self.env_config.resource_prefix}-alb-sg")

        return sg

    def _create_alb(self) -> elbv2.ApplicationLoadBalancer:
        """创建 Internet-facing ALB (Public 子网)。"""
        alb = elbv2.ApplicationLoadBalancer(
            self,
            "ApplicationLoadBalancer",
            vpc=self._vpc,
            internet_facing=True,
            security_group=self._security_group,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC,
            ),
            load_balancer_name=f"{self.env_config.resource_prefix}-alb",
            http2_enabled=True,
            idle_timeout=Duration.seconds(60),
            # 丢弃无效 header 防止 HTTP desync 攻击
            drop_invalid_header_fields=True,
        )

        cdk.Tags.of(alb).add("Name", f"{self.env_config.resource_prefix}-alb")

        return alb

    def _get_or_create_certificate(self) -> acm.ICertificate:
        """获取已有 ACM 证书或创建参数占位符。"""
        if self._certificate_arn:
            return acm.Certificate.from_certificate_arn(
                self,
                "ImportedCertificate",
                certificate_arn=self._certificate_arn,
            )

        # 生产环境应使用 Route53 DNS 验证或导入已有 ACM 证书
        cert_arn_param = cdk.CfnParameter(
            self,
            "CertificateArn",
            type="String",
            description="ACM Certificate ARN for HTTPS listener",
            default="",
        )

        return acm.Certificate.from_certificate_arn(
            self,
            "CertificateFromParam",
            certificate_arn=cert_arn_param.value_as_string,
        )

    def _create_https_listener(self) -> elbv2.ApplicationListener:
        """创建 HTTPS listener (TLS 1.2+, 强密码套件, 前向保密)。"""
        certificate = self._get_or_create_certificate()

        listener = self._alb.add_listener(
            "HttpsListener",
            port=443,
            protocol=elbv2.ApplicationProtocol.HTTPS,
            certificates=[certificate],
            ssl_policy=elbv2.SslPolicy.TLS12,
            default_action=elbv2.ListenerAction.fixed_response(
                status_code=404,
                content_type="text/plain",
                message_body="Not Found",
            ),
        )

        return listener

    def _create_http_redirect(self) -> elbv2.ApplicationListener:
        """创建 HTTP → HTTPS 301 重定向。"""
        return self._alb.add_listener(
            "HttpRedirectListener",
            port=80,
            protocol=elbv2.ApplicationProtocol.HTTP,
            default_action=elbv2.ListenerAction.redirect(
                protocol="HTTPS",
                port="443",
                permanent=True,
            ),
        )

    def _create_http_listener(self) -> elbv2.ApplicationListener:
        """创建 HTTP-only listener (仅 dev 环境无证书时使用)。

        WARNING: 不安全，禁止用于生产环境!
        """
        listener = self._alb.add_listener(
            "HttpListener",
            port=80,
            protocol=elbv2.ApplicationProtocol.HTTP,
            default_action=elbv2.ListenerAction.fixed_response(
                status_code=404,
                content_type="text/plain",
                message_body="Not Found",
            ),
        )

        return listener

    def _create_target_group(
        self,
        construct_id: str,
        port: int,
        health_check_path: str,
        name_suffix: str,
    ) -> elbv2.ApplicationTargetGroup:
        """创建标准化的 target group。"""
        return elbv2.ApplicationTargetGroup(
            self,
            construct_id,
            vpc=self._vpc,
            port=port,
            protocol=elbv2.ApplicationProtocol.HTTP,
            target_type=elbv2.TargetType.IP,
            health_check=elbv2.HealthCheck(
                path=health_check_path,
                port=str(port),
                protocol=elbv2.Protocol.HTTP,
                healthy_threshold_count=2,
                unhealthy_threshold_count=3,
                interval=Duration.seconds(30),
                timeout=Duration.seconds(5),
            ),
            target_group_name=f"{self.env_config.resource_prefix}-{name_suffix}",
        )

    def _create_target_groups(self) -> None:
        """创建各服务的 target group (Backend API / Grafana / Frontend)。"""
        active_listener = (
            self._https_listener if self._https_listener else self._http_listener
        )

        self._backend_target_group = self._create_target_group(
            "BackendTargetGroup",
            port=8000,
            health_check_path="/health",
            name_suffix="api",
        )
        active_listener.add_action(
            "BackendApiRule",
            priority=10,
            conditions=[elbv2.ListenerCondition.path_patterns(["/api/*", "/health"])],
            action=elbv2.ListenerAction.forward([self._backend_target_group]),
        )

        self._grafana_target_group = self._create_target_group(
            "GrafanaTargetGroup",
            port=3000,
            health_check_path="/api/health",
            name_suffix="grafana",
        )
        active_listener.add_action(
            "GrafanaRule",
            priority=20,
            conditions=[elbv2.ListenerCondition.path_patterns(["/grafana/*"])],
            action=elbv2.ListenerAction.forward([self._grafana_target_group]),
        )

        # Frontend catch-all (最低优先级, port=3000 匹配 nginx 监听端口)
        self._frontend_target_group = self._create_target_group(
            "FrontendTargetGroup",
            port=3000,
            health_check_path="/",
            name_suffix="frontend",
        )
        active_listener.add_action(
            "FrontendRule",
            priority=100,
            conditions=[elbv2.ListenerCondition.path_patterns(["/*"])],
            action=elbv2.ListenerAction.forward([self._frontend_target_group]),
        )

    @staticmethod
    def _waf_visibility_config(
        metric_name: str,
    ) -> wafv2.CfnWebACL.VisibilityConfigProperty:
        """创建 WAF 可见性配置。"""
        return wafv2.CfnWebACL.VisibilityConfigProperty(
            cloud_watch_metrics_enabled=True,
            metric_name=metric_name,
            sampled_requests_enabled=True,
        )

    @staticmethod
    def _waf_managed_rule(
        name: str,
        priority: int,
    ) -> wafv2.CfnWebACL.RuleProperty:
        """创建 AWS 托管规则组引用。"""
        return wafv2.CfnWebACL.RuleProperty(
            name=name,
            priority=priority,
            override_action=wafv2.CfnWebACL.OverrideActionProperty(none={}),
            statement=wafv2.CfnWebACL.StatementProperty(
                managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                    vendor_name="AWS",
                    name=name,
                ),
            ),
            visibility_config=AlbStack._waf_visibility_config(name),
        )

    def _create_waf(self) -> None:
        """创建 WAF WebACL: 速率限制 + AWS 托管规则 + SQLi 防护。"""
        web_acl = wafv2.CfnWebACL(
            self,
            "WafWebAcl",
            name=f"{self.env_config.resource_prefix}-waf",
            scope="REGIONAL",
            default_action=wafv2.CfnWebACL.DefaultActionProperty(
                allow=wafv2.CfnWebACL.AllowActionProperty(),
            ),
            visibility_config=self._waf_visibility_config(
                f"{self.env_config.resource_prefix}-waf"
            ),
            rules=[
                # 速率限制规则
                wafv2.CfnWebACL.RuleProperty(
                    name="RateLimitRule",
                    priority=1,
                    action=wafv2.CfnWebACL.RuleActionProperty(
                        block=wafv2.CfnWebACL.BlockActionProperty(),
                    ),
                    statement=wafv2.CfnWebACL.StatementProperty(
                        rate_based_statement=wafv2.CfnWebACL.RateBasedStatementProperty(
                            limit=2000,
                            aggregate_key_type="IP",
                        ),
                    ),
                    visibility_config=self._waf_visibility_config("RateLimitRule"),
                ),
                # AWS 托管规则组
                self._waf_managed_rule("AWSManagedRulesCommonRuleSet", priority=2),
                self._waf_managed_rule("AWSManagedRulesSQLiRuleSet", priority=3),
            ],
        )

        wafv2.CfnWebACLAssociation(
            self,
            "WafAlbAssociation",
            resource_arn=self._alb.load_balancer_arn,
            web_acl_arn=web_acl.attr_arn,
        )

    def _create_outputs(self) -> None:
        """创建 CloudFormation 输出。"""
        prefix = self.env_config.resource_prefix
        create_output(
            self,
            "AlbDnsName",
            self._alb.load_balancer_dns_name,
            "ALB DNS name for frontend access",
            export_name=f"{prefix}-alb-dns",
        )
        create_output(
            self, "AlbArn", self._alb.load_balancer_arn, "ALB ARN for reference"
        )

        if self._https_listener:
            create_output(
                self,
                "HttpsListenerArn",
                self._https_listener.listener_arn,
                "HTTPS Listener ARN",
            )
        else:
            create_output(
                self,
                "HttpListenerArn",
                self._http_listener.listener_arn,
                "HTTP Listener ARN (dev environment - no TLS)",
            )
            cdk.CfnOutput(
                self,
                "HttpOnlyWarning",
                value="WARNING: This ALB uses HTTP only (no TLS). Not suitable for production!",
                description="Security warning for HTTP-only configuration",
            )

        create_output(
            self,
            "BackendTargetGroupArn",
            self._backend_target_group.target_group_arn,
            "Backend API Target Group ARN",
            export_name=f"{prefix}-backend-tg-arn",
        )
        create_output(
            self,
            "FrontendTargetGroupArn",
            self._frontend_target_group.target_group_arn,
            "Frontend Target Group ARN",
            export_name=f"{prefix}-frontend-tg-arn",
        )
        create_output(
            self,
            "SecurityGroupId",
            self._security_group.security_group_id,
            "ALB Security Group ID",
            export_name=f"{prefix}-alb-sg-id",
        )

    @property
    def alb(self) -> elbv2.ApplicationLoadBalancer:
        return self._alb

    @property
    def https_listener(self) -> elbv2.ApplicationListener | None:
        return self._https_listener

    @property
    def http_listener(self) -> elbv2.ApplicationListener | None:
        return getattr(self, "_http_listener", None)

    @property
    def active_listener(self) -> elbv2.ApplicationListener:
        return self._https_listener if self._https_listener else self._http_listener

    @property
    def security_group(self) -> ec2.SecurityGroup:
        return self._security_group

    @property
    def dns_name(self) -> str:
        return self._alb.load_balancer_dns_name

    @property
    def backend_target_group(self) -> elbv2.ApplicationTargetGroup:
        return self._backend_target_group

    @property
    def frontend_target_group(self) -> elbv2.ApplicationTargetGroup:
        return self._frontend_target_group

    @property
    def grafana_target_group(self) -> elbv2.ApplicationTargetGroup:
        return self._grafana_target_group
