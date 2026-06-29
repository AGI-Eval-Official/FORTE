---
name: go-testify-unit-test
description: "为 Go 项目编写与优化基于 testing/testify 的单元测试，支持表驱动测试、t.Run 子测试、依赖 mock、错误断言与副作用校验，覆盖核心业务分支、边界条件和异常场景。"
---
# Skill: Go 标准测试 + testify 单元测试编写

## 概述

本技能用于为 Go 应用编写基于 **Go 标准 testing 包** + **testify** 的单元测试。

## reference 路由

当任务涉及以下任一情况时，先读取 `references/reference.md`：
- 用户提到 `auth-service`、`auth/service.go`、`AuthService`
- 需要为 `Authenticate` / `RefreshToken` 设计测试场景
- 需要确认领域模型、依赖接口、哨兵错误或业务规则（如失败计数、账户锁定、令牌轮换）

读取后再开始编写测试，确保用例与业务语义一致。

如果用户只要求通用 Go/testify 单测写法（不依赖具体业务模型），可跳过 reference，直接按技能通用流程执行。

优先级规则：若用户在当前任务中提供的内容与 `references/reference.md` 冲突，必须以用户提供内容为准；reference 仅作为默认背景信息与补充依据。

## 工作流程

编写测试的推荐步骤：

1. **通读被测包源码**：先完整阅读被测结构体及其所有依赖接口和数据模型，理清分支路径和调用关系，再动手写测试
2. **识别需要 mock 的依赖**：被测结构体构造函数中注入的所有接口依赖都需要创建 mock 实现
3. **设计表驱动测试**：把同一方法的多个测试场景组织到一个 `[]struct` 切片中，配合 `t.Run` 逐个执行
4. **按分支覆盖场景**：每个子测试覆盖一条业务分支，遵循 Arrange → Act → Assert 三段式
5. **验证副作用**：对于有副作用的方法（保存、通知等），通过 mock 的调用记录验证它们被正确调用

## Go testing 基础

### 测试函数

```go
func TestMyFunction(t *testing.T) {
    // test code
}
```

测试函数必须以 `Test` 开头，接受 `*testing.T` 参数。

### 子测试（t.Run）

```go
func TestAuthenticate(t *testing.T) {
    t.Run("valid credentials", func(t *testing.T) {
        // ...
    })
    t.Run("wrong password", func(t *testing.T) {
        // ...
    })
}
```

### 表驱动测试

Go 最具特色的测试模式——用结构体切片定义所有测试用例：

```go
func TestCalculate(t *testing.T) {
    tests := []struct {
        name     string
        input    int
        expected int
        wantErr  bool
    }{
        {"positive", 5, 25, false},
        {"zero", 0, 0, false},
        {"negative", -1, 0, true},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            result, err := Calculate(tt.input)
            if tt.wantErr {
                assert.Error(t, err)
            } else {
                assert.NoError(t, err)
                assert.Equal(t, tt.expected, result)
            }
        })
    }
}
```

## testify 基础

### assert — 断言（失败后继续执行）

```go
import "github.com/stretchr/testify/assert"

assert.Equal(t, expected, actual)
assert.NotEqual(t, a, b)
assert.Nil(t, obj)
assert.NotNil(t, obj)
assert.True(t, condition)
assert.False(t, condition)
assert.Error(t, err)
assert.NoError(t, err)
assert.ErrorIs(t, err, ErrExpected)
assert.Contains(t, str, substring)
assert.NotEmpty(t, str)
```

### require — 断言（失败后立即停止当前测试）

```go
import "github.com/stretchr/testify/require"

require.NoError(t, err)  // 如果有错误，立即终止
require.NotNil(t, result) // 如果为 nil，立即终止
```

`require` 和 `assert` API 相同，区别在于 `require` 失败会立即终止当前测试。

### 哨兵错误验证

```go
// 定义哨兵错误
var ErrNotFound = errors.New("not found")

// 测试中验证
assert.ErrorIs(t, err, ErrNotFound)
```

## Mock 模式

### 手写 mock 结构体

为每个接口创建一个 mock 实现，用字段记录调用参数和控制返回值：

```go
type mockUserRepo struct {
    findByUsernameFunc func(username string) (*User, error)
    saveFunc           func(user *User) error
    saveCalled         bool
    saveCalledWith     *User
}

func (m *mockUserRepo) FindByUsername(username string) (*User, error) {
    return m.findByUsernameFunc(username)
}

func (m *mockUserRepo) Save(user *User) error {
    m.saveCalled = true
    m.saveCalledWith = user
    return m.saveFunc(user)
}
```

### testify/mock

```go
import "github.com/stretchr/testify/mock"

type MockUserRepo struct {
    mock.Mock
}

func (m *MockUserRepo) FindByUsername(username string) (*User, error) {
    args := m.Called(username)
    if args.Get(0) == nil {
        return nil, args.Error(1)
    }
    return args.Get(0).(*User), args.Error(1)
}

// 测试中使用
mockRepo := new(MockUserRepo)
mockRepo.On("FindByUsername", "alice").Return(&user, nil)
// ... 执行测试 ...
mockRepo.AssertExpectations(t)
```

## 最佳实践

1. **表驱动测试优先**：同一方法的多个场景放在一个表中，结构清晰
2. **t.Run 隔离子测试**：每个场景作为独立子测试，失败不影响其他场景
3. **require 用于前置条件**：如果某个断言失败后续代码无意义，用 `require` 而非 `assert`
4. **命名见意**：子测试名称描述场景，如 `"wrong password increments failed attempts"`
5. **验证哨兵错误**：用 `assert.ErrorIs` 而非字符串比较来验证错误类型
6. **mock 保持简单**：手写 mock 用函数字段控制行为，比 testify/mock 更直观
7. **覆盖边界场景**：空字符串输入、nil 返回、错误路径
8. **验证副作用**：通过 mock 的 `Called` 字段或 `AssertCalled` 验证方法是否被调用
