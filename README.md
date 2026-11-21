# DevDiagnose · 研发排障助手

输入项目文档、代码和报错，查看带版本依据的候选证据与诊断建议。
项目为本次独立实现，使用公开框架；当前版本不是任何生产支持系统的复刻。

## Windows 启动

在 VSCode 中打开项目根目录，PowerShell 执行：

```powershell
.\scripts\Project.ps1 Setup
.\scripts\Project.ps1 Start
```

打开 http://127.0.0.1:8765 。停止时 Ctrl+C。
Conda 环境位于 `.conda/devdiagnose`，VSCode 解释器选择其中的 `python.exe`。
脚本设置 `PYTHONNOUSERSITE=1`，避免读取其他环境/用户级 Python 包。
如 PowerShell 执行策略阻止脚本，可直接在已激活的项目环境执行 `python -m uvicorn devdiagnose.api:app --host 127.0.0.1 --port 8765`。

## 先体验

1. 点击“加载演示案例”。示例是人工构造的 sample-client API 参数迁移问题，不是实际项目官方文档。
2. 点击“开始调查”，查看文件行号、证据片段、被版本过滤排除的旧文档。
3. 展开来源、查看轨迹、下载 Markdown 报告；刷新页面后可从运行记录重新打开。
4. 添加自己的 UTF-8 文档、代码、日志；版本文档通过“添加资料”填写依赖包名和版本。

## 两种实际执行模式

| 模式 | 能力与限制 |
|---|---|
| 本地检索 | 真实的关键词检索、requirements 约束过滤、LangGraph 检查点、证据报告；不调用模型、不推断已确认根因 |
| 模型诊断 | Deep Agents 主助手，按需委派文档/代码专家；同样使用关键词工具；未执行代码，模型结论需核验 |

复制 `.env.example` 为 `.env`，在本机填写 `LLM_API_KEY`、支持工具调用的 `LLM_MODEL` 和供应商的 `LLM_BASE_URL`，重启后可使用模型模式。密钥不要发到聊天中，不要提交 Git。
模型模式会把提问和检索到的资料片段发送给配置的模型供应商；本地检索不发送资料。

## Harness 首版

- SQLite 保存工作区、资料、任务与事件；任务创建时冻结资料快照和内容指纹。
- `requirements.txt` 声明依赖约束过滤文档版本；未知版本保留并标记未核验，不等同于实际安装环境。
- LangGraph 检查点支持本地流程节点间恢复。模型任务重试使用原始资料快照重新执行，尚不支持模型轨迹断点续跑。
- 模型图步骤上限20（API可调整），检索总预算10次，模型请求超时60秒、自动重试1次。不是精确金额预算。
- 轨迹只保存事件摘要，不保存或展示模型内部思维链。引用检查仅校验编号存在。
- 模型执行环境只有虚拟文件，不允许执行宿主机命令。

## 尚未实现

Qdrant 向量/混合检索、隔离代码复现与补丁测试、多用户鉴权、完整模型断点恢复、开发/保留集评测、离线策略自改进。这些属于后续阶段，当前不宣称已有收益。

## 验证与开发

```powershell
.\scripts\Project.ps1 Check
```

前端开发：在 `frontend` 目录执行 `npm run dev`；另一个终端运行后端，Vite 代理 `/api` 到8765。
数据位于 `data/`，环境、密钥、导入资料和日志均已忽略。服务只供本机使用，不可直接暴露公网。

## 来源与个人实现

- 依赖：[Deep Agents](https://github.com/langchain-ai/deepagents)、[LangGraph](https://github.com/langchain-ai/langgraph)、[FastAPI](https://github.com/fastapi/fastapi)、[React](https://react.dev/)、[Vite](https://vite.dev/)。
- 本项目实现：资料与版本元数据、检索基线、资料快照、任务接口、诊断工具与提示词、报告界面和验收案例。
- 实验结果只记录实际运行所得；使用 AI 辅助开发，不将框架内置功能宣称为新算法。
