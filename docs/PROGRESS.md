# DevDiagnose 接续记录

日期：2026-11-21（北京时间）。

## 目标
版本感知排障、按需多 Agent、可追溯证据；有真实失败数据后再做可评测的策略自改进。

## 已实现并验证
- Conda 独立环境 `.conda/devdiagnose`，Python 3.12.16。脚本设置 PYTHONNOUSERSITE=1，隔离用户级包。
- React/TypeScript/Vite 界面：工作区、资料导入、诊断、证据、轨迹、历史与报告下载。
- FastAPI/SQLite：保存资料版本、SHA256、任务源资料快照和事件。
- 关键词检索与 requirements.txt 声明约束版本过滤；未知版本标记未核验，不等于已确认运行版本。
- LangGraph 检查点支持本地流程节点间恢复；模型任务用原始快照重新执行。
- Deep Agents 主助手 + 文档/代码专家适配。文档专家覆盖 SDK 的 general-purpose 默认槽。
- 首版后端13测试通过，Ruff通过，pip check无冲突；前端构建通过；桌面完整操作与390px手机浏览器2测试通过。模型兼容配置新增测试结果见 VALIDATION.md。
- 模型调用与专家委派仅经过脚本模型的离线集成测试，尚未进行真实API调用。
- 服务通过 `scripts/Project.ps1 Start` 运行在 http://127.0.0.1:8765 ，接续时重新检查端口是否仍在运行。

## 限制与接续步骤
- 本机没有配置模型 Key/型号。用户在 `.env` 本地填写，不要在聊天发送密钥；重启后验证真实模型工具调用。
- 远端仓库 https://github.com/starry728/devdiagnose-agent 已创建（公开）。通过 GitHub 连接已分别保存说明、环境、后端与前端提交；后续提交记录见 GIT_CHECKPOINTS.md。
- 本地 `.git` 仍为本会话只读，尚不能通过原生Git同步远端历史；不能把远端成功误报为本地HEAD已同步。
- 公开上传本地 AGENTS.md 被自动审批拦截，原因是含有个人协作背景；已将该文件保留在本机并加入忽略规则，不影响其余源码发布。
- 默认模型模板采用 DeepSeek 官方接口和 deepseek-flash；真实密钥仍待用户在本机填写。使用步骤见 MODEL_SETUP.md。
- 用户先体验“加载演示案例 → 开始调查”；合成案例不是实际项目官方文档或故障评测集。
- 根据反馈迭代后，建立真实 Python API/依赖故障案例集，开展单/多Agent对比。

## 后续阶段（未实现）
Qdrant 混合检索、隔离复现/补丁验证、任务中断续跑、按预算调度实验、独立评测与离线策略优化。
