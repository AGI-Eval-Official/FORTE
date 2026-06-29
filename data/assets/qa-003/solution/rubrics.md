# Rubrics
> **通过标准：所有 rubric 均须满足，该任务才算通过。任一 rubric 不通过，则改任务整体判定为不通过。**

## 文件读取路径
```path
/workspace/input/dashboard-toolkit/tests/metricsCalculator.test.js
/workspace/input/dashboard-toolkit/tests/dataTransformer.test.js
/workspace/input/dashboard-toolkit/tests/filterEngine.test.js
/workspace/input/dashboard-toolkit/vitest.config.js
/workspace/input/dashboard-toolkit/src/utils/metricsCalculator.js
/workspace/input/dashboard-toolkit/src/utils/dataTransformer.js
/workspace/input/dashboard-toolkit/src/utils/filterEngine.js
```

```json
[
  {
    "id": "01",
    "content": "<file>/workspace/input/dashboard-toolkit/tests/metricsCalculator.test.js</file>、<file>/workspace/input/dashboard-toolkit/tests/dataTransformer.test.js</file>和<file>/workspace/input/dashboard-toolkit/tests/filterEngine.test.js</file>三个文件合计包含至少 8 个测试用例（`it(` 或 `test(` 出现至少 8 次）",
    "weight": 1
  },
  {
    "id": "02",
    "content": "<file>/workspace/input/dashboard-toolkit/tests/metricsCalculator.test.js</file>中导入 `metricsCalculator` ，<file>/workspace/input/dashboard-toolkit/tests/dataTransformer.test.js</file>中导入 `dataTransformer` ，<file>/workspace/input/dashboard-toolkit/tests/filterEngine.test.js</file>中导入 `filterEngine` 导入（测试覆盖了 3 个不同的 src/utils/ 模块）",
    "weight": 1
  },
  {
    "id": "03",
    "content": "<file>/workspace/input/dashboard-toolkit/vitest.config.js</file>文件中 resolve alias 路径已修正：`@` 别名指向 `./src` 而非 `./source`（文件中出现 `./src` 且不再包含 `./source`）",
    "weight": 1
  },
  {
    "id": "04",
    "content": "<file>/workspace/input/dashboard-toolkit/tests/metricsCalculator.test.js</file>、<file>/workspace/input/dashboard-toolkit/tests/dataTransformer.test.js</file>和<file>/workspace/input/dashboard-toolkit/tests/filterEngine.test.js</file>三个文件中，至少 2 个测试用例验证了边界条件或异常输入（如空数组、null、零值、无效日期等非正常路径场景）",
    "weight": 1
  },
  {
    "id": "05",
    "content": "<file>/workspace/input/dashboard-toolkit/tests/metricsCalculator.test.js</file>、<file>/workspace/input/dashboard-toolkit/tests/dataTransformer.test.js</file>和<file>/workspace/input/dashboard-toolkit/tests/filterEngine.test.js</file>三个文件中，使用了 `expect(` 搭配 `.toBe(`、`.toEqual(`、`.toStrictEqual(`、`.toContain(`、`.toHaveLength(` 中的至少 2 种不同断言方法",
    "weight": 1
  },
  {
    "id": "06",
    "content": "<file>/workspace/input/dashboard-toolkit/src/utils/metricsCalculator.js</file>文件中 `calculateGrowthRate` 函数的增长率公式除数已修正为 oldValue：函数体内出现 `/ oldValue` 而非 `/ newValue`",
    "weight": 1
  },
  {
    "id": "07",
    "content": "<file>/workspace/input/dashboard-toolkit/src/utils/dataTransformer.js</file>文件中 `sortByField` 函数不再原地修改入参数组：函数体内使用了展开运算符 `[...data]` 或 `.slice()` 创建副本后再 sort",
    "weight": 1
  },
  {
    "id": "08",
    "content": "<file>/workspace/input/dashboard-toolkit/src/utils/filterEngine.js</file>文件中 存在`filterByDateRange` 函数，且日期比较包含了相应的边界，以及日期边界允许开区间和闭区间的写法",
    "weight": 1
  }
]
```
