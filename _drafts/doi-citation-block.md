# pyobfus DOI / 如何引用 — 可贴内容块（arong.eu.org WordPress + 任何品牌页）

> 用途：往 arong.eu.org（有心工坊 / 嵘说）的 pyobfus 产品页、个人 projects/about 页粘贴。
> concept DOI = `10.5281/zenodo.20846053`（始终指向最新版本）。来源：`docs/JOSS_REJECTION_20260624.md`。

---

## A. 「如何引用」区块 — HTML 版（WordPress「自定义 HTML」区块直接贴）

```html
<!-- pyobfus 学术引用区块 -->
<div style="border:1px solid #ddd;border-radius:8px;padding:16px;margin:16px 0;background:#fafafa;">
  <p style="margin:0 0 10px;">
    <a href="https://doi.org/10.5281/zenodo.20846053" target="_blank" rel="noopener">
      <img src="https://zenodo.org/badge/DOI/10.5281/zenodo.20846053.svg" alt="DOI: 10.5281/zenodo.20846053">
    </a>
  </p>
  <p><strong>如何引用 pyobfus</strong> — 在学术或技术文献中引用本软件，请使用 Zenodo 永久 DOI（concept DOI 始终解析到最新版本）：</p>
  <p><strong>APA</strong><br>
  Zhu, R. (2026). <em>pyobfus: An AST-based Python obfuscator with reverse stack-trace mapping for AI-assisted development</em>. Zenodo. https://doi.org/10.5281/zenodo.20846053</p>
  <p><strong>BibTeX</strong></p>
  <pre style="white-space:pre-wrap;overflow-x:auto;background:#f0f0f0;padding:10px;border-radius:6px;"><code>@software{zhu_pyobfus,
  author    = {Zhu, Rong},
  title     = {pyobfus: An AST-based Python obfuscator with reverse stack-trace mapping for AI-assisted development},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.20846053},
  url       = {https://doi.org/10.5281/zenodo.20846053}
}</code></pre>
</div>
```

## B. 「如何引用」区块 — Markdown 版（页面若支持 Markdown）

```markdown
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20846053.svg)](https://doi.org/10.5281/zenodo.20846053)

**如何引用 pyobfus**（请使用 Zenodo concept DOI，始终指向最新版本）：

**APA**
> Zhu, R. (2026). *pyobfus: An AST-based Python obfuscator with reverse stack-trace mapping for AI-assisted development*. Zenodo. https://doi.org/10.5281/zenodo.20846053

**BibTeX**
​```bibtex
@software{zhu_pyobfus,
  author    = {Zhu, Rong},
  title     = {pyobfus: An AST-based Python obfuscator with reverse stack-trace mapping for AI-assisted development},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.20846053},
  url       = {https://doi.org/10.5281/zenodo.20846053}
}
​```
```

## C. projects / 作品列表条目（个人主页 / about 页一行式）

```markdown
- **pyobfus** — 基于 Python AST 的代码混淆工具，独有「反向栈追踪映射」让混淆后的代码仍可被开发者或 AI 助手调试；提供机器可读 JSON CLI + MCP server。开源（Apache-2.0）。
  DOI: [10.5281/zenodo.20846053](https://doi.org/10.5281/zenodo.20846053) ·
  [GitHub](https://github.com/zhurong2020/pyobfus) ·
  [PyPI](https://pypi.org/project/pyobfus/) ·
  [文档](https://pyobfus.readthedocs.io/)
```

---

**放置建议**：A/B 放在 pyobfus 产品/介绍页底部「引用与开源」区；C 放在个人 about/projects 页的作品列表。badge 图片由 Zenodo CDN 提供，无需自己托管。
