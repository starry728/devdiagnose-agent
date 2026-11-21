"""Synthetic example, intentionally not represented as upstream documentation."""

QUESTION = "升级 sample-client 到 2.0 后启动失败：TypeError: SampleClient.__init__() got an unexpected keyword argument 'timeout'。请结合代码和版本资料给出排查依据。"

SOURCES = [
    {"path": "requirements.txt", "content": "sample-client==2.0.0\n", "kind": "config"},
    {
        "path": "src/app.py",
        "content": "from sample_client import SampleClient\n\nclient = SampleClient(timeout=30)\nclient.get('/health')\n",
        "kind": "code",
    },
    {
        "path": "docs/migration-v2.md",
        "kind": "doc",
        "package": "sample-client",
        "version": "2.0.0",
        "content": "# 人工构造的演示迁移说明\n此资料仅用于演示，不是实际第三方项目的官方文档。\n\n## sample-client 2.0\nSampleClient 构造参数 timeout 已改为 request_timeout。\n升级后使用 SampleClient(request_timeout=30)。\n若出现 unexpected keyword argument 'timeout'，请检查代码是否仍在使用旧参数。\n修改后需在实际环境运行导入检查和测试；此说明不能代替运行验证。\n",
    },
    {
        "path": "docs/usage-v1.md",
        "kind": "doc",
        "package": "sample-client",
        "version": "1.0.0",
        "content": "# 人工构造的旧版说明\nsample-client 1.0 示例：SampleClient(timeout=30)。\n旧版本支持 timeout 参数。\n",
    },
    {
        "path": "logs/startup.log",
        "kind": "log",
        "content": "Traceback (most recent call last):\n  File 'src/app.py', line 3, in <module>\n    client = SampleClient(timeout=30)\nTypeError: SampleClient.__init__() got an unexpected keyword argument 'timeout'\n",
    },
]
