# 参考文档：用户认证服务

## 项目概述

`auth-service` 是一个用户认证服务，负责处理用户登录验证和令牌刷新，包含密码校验、失败计数、账户锁定等安全机制。

## 技术栈

- Go 1.21
- testify（assert + require + mock）
- Go 标准 testing 包

## 核心类型

| 类型 | 位置 | 职责 |
|------|------|------|
| `AuthService` | `auth/service.go` | 应用服务，编排认证和令牌刷新流程 |
| `User` | `auth/models.go` | 用户实体，包含 Username、PasswordHash、FailedAttempts、Locked |
| `AuthResult` | `auth/models.go` | 认证结果，包含 AccessToken、RefreshToken、ExpiresIn、Username |
| `TokenPair` | `auth/models.go` | 令牌对，包含 AccessToken、RefreshToken、ExpiresIn |
| `StoredToken` | `auth/models.go` | 持久化令牌，包含 Token、Username、ExpiresAt、Revoked |

## 依赖接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `UserRepository` | `FindByUsername(username)` | 按用户名查找用户，未找到返回 nil |
| `UserRepository` | `Save(user)` | 保存用户（更新失败次数、锁定状态） |
| `TokenStore` | `Store(token)` | 存储令牌 |
| `TokenStore` | `Find(token)` | 查找已存储的令牌，未找到返回 nil |
| `TokenStore` | `Revoke(token)` | 撤销令牌 |
| `PasswordHasher` | `Verify(password, hash)` | 校验密码是否匹配哈希值 |
| `TokenGenerator` | `GenerateAccessToken(username)` | 生成访问令牌 |
| `TokenGenerator` | `GenerateRefreshToken(username)` | 生成刷新令牌 |

## 哨兵错误

| 错误变量 | 触发场景 |
|----------|----------|
| `ErrUserNotFound` | 用户名不存在 |
| `ErrAccountLocked` | 账户因多次失败已被锁定 |
| `ErrInvalidCredentials` | 密码校验失败 |
| `ErrInvalidToken` | 刷新令牌不存在 |
| `ErrTokenExpired` | 刷新令牌已过期 |
| `ErrTokenRevoked` | 刷新令牌已被撤销 |

## 业务术语

| 术语 | 含义 |
|------|------|
| 失败计数 | 每次密码校验失败，`User.FailedAttempts` 递增 1 |
| 账户锁定 | 当 `FailedAttempts >= MaxFailedAttempts`（默认 5）时，`User.Locked` 置为 true |
| 成功重置 | 密码校验成功后，`FailedAttempts` 重置为 0 |
| 令牌轮换 | 刷新令牌时，旧令牌被撤销（Revoke），新令牌对被生成和存储 |

## 注意事项

- `AuthService` 通过 `NewAuthService` 构造函数注入 4 个接口依赖
- `MaxFailedAttempts` 是包级常量，值为 5
- 运行测试：`go test ./auth/...`
