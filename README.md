# STS2 随机卡组的组合概率与收益稳定性

以《杀戮尖塔2》的消耗机制为原型，研究有限随机牌组的组件可及性、同一次洗牌的条件收益和构筑操作。包含中文论文、可编译 LaTeX 源码、精确有理数计算、独立排列模拟和完整结果数据。

**最新论文：[阅读 PDF](paper/manuscript.pdf) · [LaTeX 源文件](paper/main.tex)**

公开版移除了姓名、学号及 PDF 附件和个人元数据，保留最新 AI 辅助说明，以及表5的条件样本量 K=19,365、98,648。旧稿、课程要求原件、审阅过程记录和编译临时文件不在本仓库内。

## 研究结果

- 基准牌组为24张，设置阶段揭示10张，随后从同一排列抽取4张。
- 基准组件成功概率为25/253；成功条件下的格挡均值为592/35。
- 固定规模的S/T替换下，条件均值为一次式、条件方差为二次式；合法整数参数中，条件方差在S=9时最大。
- 增加6张S后，条件均值提高，但组件稀释使总体均值由约1.67降至1.04。

上述结论针对论文定义的静态抽样协议。精确计数和证明、蒙特卡洛结果、真实游戏中的动态过程分别解释。

## 快速使用

已验证环境为 Python 3.13.11、NumPy 2.5.4、Matplotlib 3.11.2。

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

直接调用精确模型：

```python
from src.model import Deck, joint_forward, summarize

result = summarize(joint_forward(Deck(), 10, 4))
print(result['p'])                 # 25/253
print(result['conditional_mean'])  # 592/35
```

## 复现实验

```sh
python -m experiments.run_all
python -m unittest discover -s tests -v
```

默认107个配置各200,000次，基准独立复验1,000,000次；四档样本量各重复30次，总计30,260,000次实体排列。种子、配置和整数直方图保存在data目录。**重跑会覆盖data、figures及research_report.md。** 不保存逐次排列日志；保存的充分统计量可重算当前指标。

重绘中文图需要 Microsoft YaHei、SimHei、SimSun 或 Noto Sans CJK SC。Linux 可安装 `fonts-noto-cjk`。绘图采用无界面后端。

```sh
python -m experiments.make_figures
python -m experiments.write_report
```

单独重绘会改变图表文件的字节摘要；需要更新完整交付校验时应运行完整实验命令。减小试验次数会产生另一套数据，不能当作默认实验结果。

## 文件导航

| 路径 | 内容 |
|---|---|
| paper/ | 最新匿名PDF、LaTeX正文、参考文献、表格与7组印刷图 |
| src/model.py | 容斥、顺序概率、时间分布、双方向联合计数和精确矩 |
| src/simulation.py | 实体排列模拟、Wilson与均值区间 |
| experiments/ | 配置、结果导出、10组图与研究报告生成 |
| data/ | 107组精确分布、模拟计数、复验、收敛实验和哈希清单 |
| figures/ | 10组研究图的PNG、矢量PDF与说明 |
| tests/ | 小牌组全排列、边界、统计量及交付一致性检查 |
| model_audit.md | 严格模型定义、推导和适用范围 |
| research_report.md | 根据保存数据生成的结果分析 |

## 编译论文

安装包含XeLaTeX、latexmk和BibTeX的MiKTeX或TeX Live；源码使用Fandol和TeX Gyre Termes，不依赖Windows系统字体。

```sh
python -m pip install -r requirements.txt -r requirements-paper.txt
cd paper
python build_paper.py
```

需要刷新表格和印刷图时运行 `python build_paper.py --refresh-assets`。默认构建不会覆盖发布的manuscript.pdf；确认版面后可加 `--update-pdf`。Windows 也可运行 `./build.ps1`，对应开关为 `-RefreshAssets`、`-UpdatePdf`。

发布PDF保留了已审查版本的排版，只移除了个人信息；不同TeX环境重新编译时，字体和换行可能略有不同。详见 [论文说明](paper/README.md)。

## 数据与AI辅助

数据来自明确设定的抽象随机实验，不是采集的真实对战样本。主实验的部分置信区间未覆盖理论值，原结果与独立复验均予以保留。

作者负责整体思路与概率公式的构建，以及结果审核和定稿。AI主要用于Python代码构建、部分文字生成，并辅助程序运行、数值核验与LaTeX排版；完整说明保留在论文附录中。

## 许可

本仓库原创代码与材料采用 [MIT License](LICENSE)。引用文献、游戏名称和第三方字体等保留各自权利；本项目与游戏开发商无关联。
