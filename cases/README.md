# cases 目录说明

`cases/` 是 benchmark 的 case 声明层。这里定义每个可运行实例的元数据、问题类型、规模信息、建模方式、参考值和结果解码逻辑；不放 dashboard 结果。

## 目录分层

```text
cases/
  README.md
  tsplib/
  jsplib/
  psplib/
  qaplib/
  miplib2017/
  custom/
```

每个来源目录都应提供自己的 `README.md`。来源目录下的 README 会继续说明该来源包含哪些 case，以及每个 case 对应的问题描述、数据含义和使用方式。

## 各来源入口

- [TSPLIB](tsplib/README.md)
- [JSPLIB](jsplib/README.md)
- [PSPLIB](psplib/README.md)
- [QAPLIB](qaplib/README.md)
- [MIPLIB 2017](miplib2017/README.md)
- [Custom](custom/README.md)

## 组织约定

- 公开 benchmark 通常按 `cases/<来源>/<问题类型>/` 组织。
- 自定义 benchmark 放在 `cases/custom/` 下，优先表达问题建模和实例规模。
- `raw/` 目录保存原始实例缓存或来源文件，不应把它当作文档入口。

## 发现链路

`benchmarks.run` 不逐个 import 具体 case，而是通过 `cases/registry.py` 发现来源包，再由来源包聚合各实例模块的 `CASES`。
