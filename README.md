# WITec Suite Help — 中文翻译

将 WITec Suite 6.2 软件帮助文件 (`WITecSuiteHelp.chm`) 完整翻译为简体中文，使用 AI 子代理并行翻译，保持术语一致性。

## 文件说明

| 文件 | 说明 |
|---|---|
| `WITecSuiteHelp.chm` | 原始英文帮助文件（~15 MB） |
| `WITecSuiteHelp_CN.chm` | 中文翻译版帮助文件 |
| `glossary.json` | WITec 专业术语中英对照表（~180 条） |
| `translated_terms.json` | 目录/索引完整术语翻译（620 条） |
| `translate_chm.py` | 批量翻译脚本（需 OpenAI 兼容 API key） |
| `recompile_chm.py` | 一键重新编译 CHM 脚本 |
| `chm_extracted_cn/` | 翻译工作目录（HTML + 资源 + 项目文件） |

## 翻译内容

- **402** 个 HTML 帮助页面，**1,088** 张图片
- 涵盖：拉曼光谱、AFM、SNOM、共聚焦显微镜、WITec Control、WITec Project、TrueMatch、ParticleScout、COM 自动化等全部模块

## 翻译方法

1. `hh.exe -decompile` 反编译 CHM → 1,504 个文件
2. 从目录 (`.hhc`) 和索引 (`.hhk`) 提取 620 条术语，建立统一术语表
3. **14 个 AI 子代理并行翻译**全部 HTML
4. 目录/索引文件转换为 GB2312 编码以兼容 CHM 编译器
5. `hhc.exe` 重新编译为 CHM

## 重新编译

如果修改了 `chm_extracted_cn/` 中的 HTML 内容：

```powershell
python recompile_chm.py
```

或手动编译：

```powershell
& "C:\Program Files (x86)\HTML Help Workshop\hhc.exe" "chm_extracted_cn\WITecSuiteHelp.hhp"
```

编译输出：`chm_extracted_cn\WITecSuiteHelp_CN.chm`

## 翻译署名

由 [DeepSeek](https://www.deepseek.com/) 和 [Augtumn](https://github.com/Augtumn) 翻译。

---

*原始英文 CHM 版权归 WITec GmbH 所有。*
