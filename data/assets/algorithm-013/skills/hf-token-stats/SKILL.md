---
name: hf-token-stats
description: 统计 Hugging Face 数据集中指定字段的 token 长度分布。Use when the user wants to analyze token length statistics for a HF dataset field, including distribution, percentiles, and optional histogram visualization.
---

# HF Token Stats

统计 Hugging Face 数据集中指定字段的 token 长度分布。

## 工作流

1. **加载 tokenizer** — 根据用户指定的模型名从 HF Hub 加载
2. **加载数据集** — 根据用户指定的 repo/subset/split 加载，按需采样
3. **提取目标字段** — 从每条数据中取出用户关心的文本字段
4. **分词并计算长度** — 用 tokenizer 编码，记录每条的 token 数
5. **统计 & 保存** — 计算统计量，按用户要求的格式和路径保存结果

## 关键 API 速查

### 加载 tokenizer

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.1-8B")
# 某些模型需要 trust_remote_code=True
```

### 加载数据集

```python
from datasets import load_dataset

# 基础用法
ds = load_dataset("tatsu-lab/alpaca", split="train")

# 带 subset
ds = load_dataset("cais/mmlu", name="anatomy", split="test")

# 只取前 N 条
ds = load_dataset("tatsu-lab/alpaca", split="train[:1000]")

# 流式加载（超大数据集）
ds = load_dataset("cerebras/SlimPajama-627B", split="train", streaming=True)
```

### 分词计数

```python
# 单条
tokens = tokenizer.encode(text, add_special_tokens=False)
length = len(tokens)

# 批量（更快）
encoded = tokenizer(texts, add_special_tokens=False, truncation=False)
lengths = [len(ids) for ids in encoded["input_ids"]]
```

### 统计量计算

```python
import numpy as np

arr = np.array(lengths)
stats = {
    "count": len(arr),
    "mean": arr.mean(),
    "median": np.median(arr),
    "std": arr.std(),
    "min": arr.min(),
    "max": arr.max(),
    "percentiles": {q: np.percentile(arr, q) for q in [25, 50, 75, 90, 95, 99]},
    "total_tokens": arr.sum(),
}
```

### 保存结果

```python
# JSON
import json
with open(output_path, "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

# CSV
import csv
with open(output_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["index", "token_length"])
    for i, l in enumerate(lengths):
        writer.writerow([i, l])

# 可视化（可选）
import matplotlib.pyplot as plt
plt.hist(lengths, bins=30)
plt.savefig(output_path.replace(".json", ".png"))
```

## 注意事项

- 数据集字段可能是嵌套的（如对话数据的 `messages` 是 list of dict），需要根据实际结构灵活提取
- 超大数据集建议用 `streaming=True` 或 split 切片 `split="train[:5000]"` 来控制内存
- `add_special_tokens=False` 可以只统计纯文本 token，设为 True 则包含 BOS/EOS 等
- 某些 tokenizer 需要 `trust_remote_code=True`

## 依赖

```
pip install datasets transformers numpy
# 可选：pip install matplotlib
```
