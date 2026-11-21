# 首版验证记录

日期：2026-11-21（北京时间）。

| 检查 | 实际结果 |
|---|---|
| Conda | 独立环境，Python 3.12.16 |
| 核心依赖 | deepagents 0.7.41、langgraph 1.2.24、fastapi 0.165.0；全量版本见 requirements.lock.txt |
| pip check | No broken requirements found |
| 后端测试 | 15 passed；覆盖版本过滤、无证据、路径拒绝、上传限制、工作区隔离、报告/历史、本地检查点、未配置模型拒绝、直接工具及专家委派；新增 DeepSeek 和其他兼容服务的参数隔离验证 |
| Ruff | All checks passed |
| 前端构建 | TypeScript 检查与 Vite 8.3.8 生产构建成功 |
| 浏览器 | Chrome 桌面完整操作与390px手机无横向溢出，2 passed；完整操作无页面异常 |
| 本机服务 | /api/health 返回 ok，model_ready=false |

模型集成测试使用脚本模型，不访问供应商，不代表真实模型效果。人工演示案例不构成真实故障评测集。没有执行或修改导入代码。
