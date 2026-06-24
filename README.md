# WITec Suite Help — 中文翻译

将 WITec Suite 6.2 软件帮助文件 (`WITecSuiteHelp.chm`) 完整翻译为简体中文。14 个 AI 子代理并行翻译，统一术语表保证专业术语一致性。

## 文件说明

| 文件 | 说明 |
|---|---|
| `WITecSuiteHelp.chm` | 原始英文帮助文件（~15 MB） |
| `WITecSuiteHelp_CN.chm` | 中文翻译版帮助文件，可直接使用 |
| `glossary.json` | WITec 专业术语中英对照表（180+ 条） |
| `translated_terms.json` | 目录/索引完整术语翻译（620 条） |
| `translate_chm.py` | 批量翻译脚本（需 OpenAI 兼容 API key） |
| `recompile_chm.py` | 一键重新编译 CHM 脚本 |
| `chm_to_pdf.py` | CHM → PDF 转换脚本 |
| `chm_extracted_cn/` | 翻译工作目录（HTML + 资源 + HHP 项目文件） |

## 翻译内容

- **402** 个 HTML 帮助页面，**1,088** 张图片
- 涵盖全部模块：拉曼光谱、AFM、SNOM、共聚焦显微镜、WITec Control、WITec Project、TrueMatch、ParticleScout、COM 自动化、用户管理等

### 将文档喂给 AI

如需将全部帮助内容提供给 AI 作为上下文，使用合并后的单文件 HTML：

```
chm_extracted_cn/_combined.html
```

该文件包含全部 402 页内容，内部链接已转为页内锚点，可直接拖入 AI 对话窗口或作为知识库导入。

---

## 完整工作流程

### 环境要求

| 工具 | 用途 | 获取方式 |
|---|---|---|
| **HTML Help Workshop** | CHM 编译（`hhc.exe`） | [htmlhelp.exe](https://github.com/EWSoftware/SHFB/raw/master/ThirdPartyTools/htmlhelp.exe)（~3.5 MB，微软数字签名） |
| **Python 3.x** | 运行翻译和编译脚本 | [python.org](https://www.python.org/downloads/) |

> **注意**：Microsoft 官方下载页面已失效。以上链接来自 [Sandcastle Help File Builder](https://github.com/EWSoftware/SHFB) 项目托管的第三方工具镜像。

Python 依赖（仅翻译脚本需要）：

```powershell
pip install beautifulsoup4 openai tqdm
```

安装后 `hhc.exe` 默认路径：
```
C:\Program Files (x86)\HTML Help Workshop\hhc.exe
```

### 第一步：反编译原始 CHM

Windows 自带 `hh.exe` 即可反编译，无需额外工具：

```powershell
hh -decompile chm_extracted WITecSuiteHelp.chm
```

生成 `chm_extracted/` 目录，包含全部 HTML、图片、CSS、JS 以及目录文件 (`.hhc`) 和索引文件 (`.hhk`)。

### 第二步：翻译

**方式 A — 运行翻译脚本（需 API key）：**

```powershell
$env:OPENAI_API_KEY = "sk-..."
$env:OPENAI_BASE_URL = "https://api.openai.com/v1"  # 或其他兼容 API
python translate_chm.py
```

脚本流程：
1. 加载 `glossary.json` 术语表
2. 遍历全部 HTML，调用 LLM API 翻译正文
3. 翻译 `.hhc` 目录和 `.hhk` 索引
4. 输出到 `chm_extracted_cn/`

**方式 B — AI 子代理翻译（本项目使用的方式）：**

将 HTML 分批提交给 AI 子代理并行翻译，术语表嵌入 prompt 保证一致性。

### 第三步：修复编码

CHM 编译器对中文语言标识（`Language=0x804`）强制使用 GB2312，需将目录/索引文件转为 GB2312 编码，同时 HTML 添加 UTF-8 声明：

```powershell
# 为所有 HTML 添加 <meta charset="UTF-8">
python -c "
from pathlib import Path
for f in Path('chm_extracted_cn').glob('*.html'):
    c = f.read_text(encoding='utf-8')
    if 'charset' not in c:
        c = c.replace('<meta http-equiv=\"Content-Style-Type\"', '<meta charset=\"UTF-8\">\n<meta http-equiv=\"Content-Style-Type\"')
        f.write_text(c, encoding='utf-8')
"

# HHC/HHK 转为 GB2312
python -c "
from pathlib import Path
for fn in ['WITecSuiteHelp.hhc','WITecSuiteHelp.hhk']:
    f = Path('chm_extracted_cn') / fn
    f.write_text(f.read_text('utf-8').replace('<meta charset=\"UTF-8\">\n',''), encoding='gb2312')
"
```

### 第四步：编译 CHM

```powershell
# 一键编译（复制资源 + 生成 HHP + 编译）
python recompile_chm.py
```

或手动：

```powershell
# 1. 复制 JS/CSS/图片到 chm_extracted_cn/
# 2. 确保 chm_extracted_cn/WITecSuiteHelp.hhp 文件列表正确
# 3. 编译
& "C:\Program Files (x86)\HTML Help Workshop\hhc.exe" "chm_extracted_cn\WITecSuiteHelp.hhp"
```

编译输出：`chm_extracted_cn\WITecSuiteHelp_CN.chm`（约 15 MB，402 主题，1,088 图片）

### 技术要点

- **HTML 编码**：正文使用 UTF-8 + `<meta charset="UTF-8">`
- **HHC/HHK 编码**：必须使用 GB2312，CHM 编译器忽略 charset 声明
- **HHP 语言设置**：`Language=0x804 中文(简体，中国)`
- **术语一致性**：`glossary.json` 作为权威术语源，所有翻译 agent 引用同一文件

---

## 翻译署名

由 [DeepSeek](https://www.deepseek.com/) 和 [Augtumn](https://github.com/Augtumn) 翻译。

---

*原始英文 CHM 版权归 WITec GmbH 所有。*
