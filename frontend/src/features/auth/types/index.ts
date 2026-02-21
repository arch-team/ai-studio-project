/**
 * Auth 模块类型定义
 *
 * 与后端 auth API Schema 对齐
 */

// === 请求类型 ===

/** 登录请求 - 支持本地凭证或 SSO Token */
export interface LoginRequest {
  username?: string;
  password?: string;
  id_token?: string;
}

/** Token 刷新请求 */
export interface RefreshTokenRequest {
  refresh_token: string;
}

// === 响应类型 ===

/** Token 响应 */
export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

/** 用户响应 (登录/账户管理) */
export interface UserResponse {
  id: number;
  username: string;
  email: string;
  display_name: string | null;
  role: string;
  status: string;
  auth_type: string;
}

/** 登录响应 */
export interface LoginResponse {
  tokens: TokenResponse;
  user: UserResponse;
}

/** 通用消息响应 */
export interface MessageResponse {
  message: string;
}
