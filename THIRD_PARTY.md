# 第三方资源与许可

本仓库的**代码**是 MIT（见 LICENSE）。字库是把字体光栅化成点阵后的**派生数据**，
随仓库分发时遵循各自的字体许可：

## 1. `src/font8x16.h`（ASCII / 制表符 / 方块字符点阵）

来源：`cmtt10.ttf` —— Computer Modern Typewriter，随**笔上的 LaTeX 资源**提供
（`/etc/miniapp/resources/latex/res/fonts/latin/optional/cmtt10.ttf`）。

- 许可：**GUST Font License**（相当于 OFL 的字体许可，允许嵌入/派生/再分发）
- 生成的 `font8x16.h` 是该字体的**位图派生**，保留此声明即满足许可要求
- 制表符（`─│┌┐└┘├┤┬┴┼`）与方块字符（`█▀▄▌▐░▒▓`）是**程序化绘制**的（原字体没有这些字形），不受字体许可约束

## 2. `src/font_cjk.h`（中文点阵，6938 字形）

来源：`HarmonyOS_Sans_SC_Regular.ttf` —— 随**笔上的框架资源**提供
（`/etc/miniapp/resources/fonts/`，同目录下有 `LICENSE.txt` 与 `OFL.txt`）。

- 许可：**SIL Open Font License 1.1 (OFL)**
- 本仓库只包含 **16×16 单色位图派生数据**，不包含原字体文件本身
- OFL 允许对字体进行修改/派生并按同样许可再分发；本目录保留许可与来源声明
- 若要商用，请自行核对 OFL 全文（`https://scripts.sil.org/OFL`）与华为的字体声明

## 3. 其它

- API 名称、设备路径等对**有道词典笔**的引用仅用于说明兼容性，与本项目无隶属关系
- `.amr` 包内的 `libjsapi_term.so` 是本仓库 `src/term.c` + `src/term_vt.c` 的编译产物（MIT）
