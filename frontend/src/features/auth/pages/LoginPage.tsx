/**
 * LoginPage 组件
 *
 * 用户登录页面，对接后端 /api/v1/auth/login
 */

import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  Button,
  Container,
  Form,
  FormField,
  Header,
  Input,
  SpaceBetween,
  Alert,
} from "@cloudscape-design/components";
import { useAuthStore } from "../store/authStore";
import { loginWithCredentials } from "../api";
import { ROUTES } from "@/app/router/routes";

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const login = useAuthStore((s) => s.login);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 已登录用户直接跳转
  if (isAuthenticated) {
    const from =
      (location.state as { from?: { pathname: string } })?.from?.pathname ||
      ROUTES.HOME;
    navigate(from, { replace: true });
    return null;
  }

  const handleSubmit = async () => {
    setError(null);

    if (!username.trim() || !password.trim()) {
      setError("请输入用户名和密码");
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await loginWithCredentials(username, password);
      login(response);

      // 重定向到之前的页面或首页
      const from =
        (location.state as { from?: { pathname: string } })?.from?.pathname ||
        ROUTES.HOME;
      navigate(from, { replace: true });
    } catch (err) {
      const message = err instanceof Error ? err.message : "登录失败，请重试";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Container
      header={
        <Header variant="h2" description="使用工作账号访问训练平台">
          登录
        </Header>
      }
    >
      <Form
        actions={
          <Button
            variant="primary"
            loading={isSubmitting}
            loadingText="正在登录"
            fullWidth
            onClick={handleSubmit}
          >
            登录
          </Button>
        }
      >
        <SpaceBetween size="l">
          {error && (
            <Alert type="error" dismissible onDismiss={() => setError(null)}>
              {error}
            </Alert>
          )}

          <FormField label="用户名">
            <Input
              value={username}
              onChange={({ detail }) => setUsername(detail.value)}
              placeholder="请输入用户名"
              disabled={isSubmitting}
              autoComplete="username"
              autoFocus
            />
          </FormField>

          <FormField label="密码">
            <Input
              type="password"
              value={password}
              onChange={({ detail }) => setPassword(detail.value)}
              placeholder="请输入密码"
              disabled={isSubmitting}
              autoComplete="current-password"
              onKeyDown={({ detail }) => {
                if (detail.key === "Enter") {
                  handleSubmit();
                }
              }}
            />
          </FormField>
        </SpaceBetween>
      </Form>
    </Container>
  );
}
