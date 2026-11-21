# 接通第一个真实模型

当前默认模板面向 DeepSeek 官方 API，可替换为支持工具调用的兼容服务。

1. 在 VSCode 打开根目录 `.env`；没有该文件时从 `.env.example` 复制。
2. 在 `LLM_API_KEY=` 后填入你自己的密钥，保留在本机，不要粘贴到聊天或 GitHub。
3. 默认 `LLM_BASE_URL=https://api.deepseek.com`，`LLM_MODEL=deepseek-flash`。
4. 在运行服务的终端按 Ctrl+C，再执行 `.\scripts\Project.ps1 Start`；刷新网页。
5. 选择“模型诊断”，先运行人工演示案例。检查实际工具事件、模型调用和来源引用。

模型配置存在只表示字段齐全，不代表密钥有效、额度充足或真实调用已经通过。不要把离线脚本模型测试视为模型效果评测。

## 兼容说明

DeepSeek 当前默认启用思考模式；工具调用时要求保留并回传 reasoning_content。首版通用 ChatOpenAI 适配器不处理该字段，因此仅对官方 DeepSeek 端点显式关闭思考模式。其他供应商不会附带此专用参数。

官方依据：[模型参数](https://api-docs.deepseek.com/quick_start/pricing/)、[思考模式与工具调用](https://api-docs.deepseek.com/guides/thinking_mode/)。具体模型支持与名字以使用时的官方文档为准。

本地检索不会向模型发送资料。模型诊断会将问题及检索资料片段发给所配置供应商，首轮只使用项目自带的人工演示案例。
