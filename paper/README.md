# 最新公开论文

- `manuscript.pdf`：最新经审阅、补充表5样本量并修订AI说明的匿名公开版。
- `main.tex`、`sections/`、`references.bib`：对应内容的LaTeX源码，姓名和学号已移除。
- `generated/`：由保存的结果提取的表格及数字；表5的K来自整数成功计数。
- `figures/`：用于论文的7组印刷适配图，研究曲线和数据与根目录figures一致。
- `build_paper.py`：跨平台构建入口，准备BibTeX输入并检查编译结果。
- `build_assets.py`、`print_figures.py`：刷新表格、校验交换性系数并生成印刷图。
- `verify_paper.py`：检查PDF结构、字体、表5、最新AI说明及可选私有词表。

## 构建

```sh
python -m pip install -r ../requirements.txt -r ../requirements-paper.txt
python build_paper.py
```

刷新数据表格及图：`python build_paper.py --refresh-assets`。加 `--update-pdf` 才会把通过检查的构建复制为manuscript.pdf。Windows亦可运行`./build.ps1`及其对应开关。

构建产物位于忽略的build目录。公开PDF以已确认版为底稿，删除作者信息、学号、元数据中的个人身份和嵌入附件，正文及AI说明未重新生成。源码使用可移植字体配置，重新编译时可能出现不同换行。

源码和发布PDF均保留表5的有效成功样本数，以及作者负责概率公式构建、AI参与代码和部分文字生成的分工说明。统计数据仍来自根目录data，不新增或改写实验观察。
