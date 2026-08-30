# ShimStacker

**用你实际拥有的有限垫片库存，同时满足多个装配间隙，并证明每组垫片在最坏公差下仍落在目标范围内。**

[在线报告示例](https://kanadek.github.io/shimstacker/) · [输入格式](docs/INPUT.md) · [差异化调研](docs/RESEARCH.md)

ShimStacker 是一个完全离线、运行时零第三方依赖的命令行工具。它解决的不是“目标厚度减当前厚度”这种单次计算，而是同一批有限库存如何分给多个任务：同一片垫片不能被两个任务同时占用，名义值接近也不等于公差范围一定合格。

## 快速体验

需要 Python 3.11 或更新版本。

```console
python -m pip install https://github.com/KanadeK/shimstacker/releases/download/v0.1.0/shimstacker-0.1.0-py3-none-any.whl
shimstacker demo --output shim-report
```

示例会得到：

```text
FEASIBLE · 3/3 jobs allocated · 53 states · shim-report
```

`shim-report` 中有四个确定性文件：完整 JSON 证据、CSV 领料表、Markdown 工作台清单，以及不含脚本和远程资源的独立 HTML 报告。输出目录若已存在，程序会拒绝覆盖。

## 实际使用

输入是严格的 UTF-8 JSON。所有尺寸必须写成字符串，以 `Decimal` 精确计算：

```json
{
  "schema_version": 1,
  "project": "减速箱返修",
  "unit": "mm",
  "max_states": 200000,
  "stock": [
    {"id": "S-010", "thickness": "0.10", "tolerance": "0.005", "quantity": 4},
    {"id": "S-020", "thickness": "0.20", "tolerance": "0.005", "quantity": 2}
  ],
  "jobs": [
    {"id": "input-bearing", "target_min": "0.285", "target_max": "0.315", "max_pieces": 3}
  ]
}
```

```console
shimstacker validate gearbox.json
shimstacker plan gearbox.json --output gearbox-report
```

一组垫片只有在 `sum(thickness - tolerance)` 不低于目标下限，且 `sum(thickness + tolerance)` 不高于目标上限时才算保证合格。全局可行方案依次按总片数最少、偏离目标中点最小、稳定 ID 顺序选择。

## 结果与退出码

| 退出码 | 结果 | 含义 |
| ---: | --- | --- |
| `0` | `feasible` | 所有任务都获得了不超库存的有效组合。 |
| `1` | `infeasible` | 已穷尽有界搜索；`SHS101` 表示单个任务就无解，`SHS102` 表示共享库存冲突。 |
| `2` | 输入或 I/O 错误 | JSON、字段、路径或输出请求不合法。 |
| `3` | `indeterminate` | 达到 `max_states`，尚不能证明可行或不可行。 |

## 明确边界

ShimStacker 只证明输入中声明的厚度、公差、数量、目标区间和片数约束。它不判断材料相容性、压缩、腐蚀、热行为、预紧力、磨损或设备能否安全运行。必须遵循设备制造商流程，并由合格人员复测实际装配间隙。

程序不会连接设备、自动修改库存、执行输入内容、创建账号或联网发送数据。

开发与发布门禁见英文 [README](README.md)，问题排查见 [Troubleshooting](docs/TROUBLESHOOTING.md)。

