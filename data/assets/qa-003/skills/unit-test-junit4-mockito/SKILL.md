---
name: unit-test-junit4-mockito
description: 当用户需要为 Java 业务代码（如服务、处理器、工作流组件）编写或补充基于 JUnit 4 + Mockito 的单元测试，并覆盖主要业务分支与异常路径时触发本技能。
---

# Skill: JUnit 4 + Mockito 单元测试编写

## 概述

本技能用于为 Java 应用编写基于 **JUnit 4** + **Mockito** 的单元测试。

## Reference 路由

- 当任务涉及具体业务语义（如退款流程、批处理、重试策略、事件发布、领域对象）时，先读取 `references/reference.md`，再设计测试用例。
- 当用户提到业务名词但未给出完整上下文时，优先从 `references/reference.md` 获取术语定义和领域约束。
- 当任务仅是通用测试语法或框架用法（与具体业务无关）时，可不读取 reference，直接按通用 JUnit 4 + Mockito 规范执行。
- 若用户提供的源码/需求与 reference 存在冲突，以用户提供的源码和明确要求为准，reference 仅作补充。

## 工作流程

编写测试的推荐步骤：

1. **通读被测类源码**：先完整阅读被测类及其所有依赖接口和域对象，理清分支路径和调用关系，再动手写测试
2. **识别需要 mock 的依赖**：被测类构造函数里的所有外部依赖都需要用 `@Mock` 模拟
3. **设计 `@Before` 初始化方法**：把多个测试共用的测试数据（如域对象）和 mock 默认返回值放在 `@Before` 方法里，避免每个测试重复构造
4. **按分支逐个编写 `@Test` 方法**：每个测试方法覆盖一条业务分支，遵循 Arrange → Act → Assert 三段式
5. **验证交互行为**：对于有副作用的方法（保存、通知、发布事件等），用 `verify` 确认它们被正确调用

## 注意事项

### mock 之间的协调

当被测逻辑依赖**多个 mock 的返回值协同工作**时，stub 的顺序和值必须互相匹配。例如：一个 mock 控制重试次数 N，另一个 mock 需要模拟前 N-1 次失败、第 N 次成功——两者必须对齐，否则测试行为会不符合预期。

### 动态次数验证

如果被测类中某个行为的执行次数**不是硬编码常量**，而是由某个依赖在运行时返回的值决定的，那么 `verify(..., times(n))` 里的 `n` 就需要根据你 mock 的返回值来推算，而不是随便写一个固定数字。

### 富对象捕获

当需要验证传给 mock 方法的参数是一个包含多个字段的复杂对象时，用 `ArgumentCaptor` 捕获后逐字段断言，比直接构造期望对象做 `assertEquals` 更灵活、更易排查。

## JUnit 4 基础

- **@Test**：标注测试方法，JUnit 会独立运行每个 `@Test` 方法
- **@Test(expected = XxxException.class)**：声明该测试预期抛出指定异常
- **断言方法**：`assertEquals`, `assertNotNull`, `assertNull`, `assertTrue`, `assertFalse`
- **@Before / @After**：每个测试方法执行前/后运行，用于初始化和清理

## Mockito 基础

- **@RunWith(MockitoJUnitRunner.class)**：让 JUnit 自动初始化 Mockito 注解
- **@Mock**：创建依赖的 mock 实例
- **@InjectMocks**：创建被测对象，自动注入 `@Mock` 字段
- **when(...).thenReturn(...)**：设定 mock 方法的返回值
- **verify(mock).method(args)**：验证 mock 方法被调用过
- **verify(mock, never()).method(...)**：验证 mock 方法从未被调用
- **verify(mock, times(n)).method(...)**：验证调用恰好 n 次
- **verify(mock, atLeast(n)).method(...)**：验证调用至少 n 次

## 高级模式

### ArgumentCaptor — 参数捕获

用于捕获传给 mock 方法的参数，再逐字段断言：

```java
ArgumentCaptor<MyEvent> captor = ArgumentCaptor.forClass(MyEvent.class);
verify(publisher).publish(captor.capture());

MyEvent event = captor.getValue();
assertEquals("ORD-001", event.getOrderId());
assertEquals(EventType.SUCCESS, event.getEventType());
assertEquals(3, event.getAttemptCount());
```

### thenThrow / doThrow — 异常模拟

模拟依赖抛出异常，触发被测类的异常处理分支：

```java
// 有返回值的方法：
when(mock.method()).thenThrow(new RuntimeException("error"));

// void 方法：
doThrow(new RuntimeException("error")).when(mock).voidMethod();

// 链式：前几次抛异常，最后一次成功
when(mock.method())
    .thenThrow(new RuntimeException("fail"))
    .thenThrow(new RuntimeException("fail"))
    .thenReturn(successValue);
```

### 链式 Stubbing — 连续调用返回不同值

```java
when(mock.method())
    .thenReturn(firstValue)
    .thenReturn(secondValue)
    .thenThrow(new RuntimeException("third call fails"));
```

## 测试类模板

```java
@RunWith(MockitoJUnitRunner.class)
public class MyServiceTest {

    @Mock
    private DependencyA depA;

    @Mock
    private DependencyB depB;

    @InjectMocks
    private MyService service;

    private MyEntity sharedEntity;

    @Before
    public void setUp() {
        sharedEntity = new MyEntity("id-1", "data");
        when(depA.getConfig(anyString())).thenReturn(defaultConfig);
    }

    @Test
    public void testNormalCase() {
        when(depB.process(any())).thenReturn(true);

        Result result = service.execute("id-1");

        assertEquals("expected", result.getValue());
        verify(depB).process(any());
    }

    @Test(expected = IllegalArgumentException.class)
    public void testInvalidInput() {
        service.execute(null);
    }
}
```

## 最佳实践

1. **一个测试验证一个行为**：每个 `@Test` 方法聚焦一条分支逻辑
2. **Arrange → Act → Assert**：三段式结构清晰可读
3. **命名见意**：如 `testProcessBatch_orderNotFound_countedAsFailed`
4. **只 mock 外部依赖**：不要 mock 被测类本身
5. **@Before 复用夹具**：共享的测试数据和默认 stub 放在 setUp 里
6. **覆盖边界场景**：null 输入、空集合、零值、异常路径
7. **用 ArgumentCaptor 验证复杂参数**：比构造完整期望对象更灵活
8. **测试重试逻辑**：用 `thenThrow(...).thenReturn(...)` 链式模拟瞬时故障
