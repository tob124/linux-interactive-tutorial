# Linux 工程实践 · 机械研究生交互课程

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Ubuntu%2024.04%20LTS-E95420?style=flat-square&logo=ubuntu&logoColor=white)](https://releases.ubuntu.com/24.04/)
[![Docker](https://img.shields.io/badge/Docker-rootless-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docs.docker.com/engine/security/rootless/)
[![Assets](https://img.shields.io/badge/assets-vendored%20%C2%B7%20no%20CDN-2ea44f?style=flat-square)](#-教师与维护者)
[![Locale](https://img.shields.io/badge/locale-zh--CN-red?style=flat-square)](#)

[![Weeks](https://img.shields.io/badge/course-6%20weeks-informational?style=flat-square)](#六周基础项目)
[![Units](https://img.shields.io/badge/units-24-informational?style=flat-square)](#六周基础项目)
[![Quiz](https://img.shields.io/badge/quiz-48-informational?style=flat-square)](#六周基础项目)
[![Tracks](https://img.shields.io/badge/advanced%20tracks-3-informational?style=flat-square)](#六周基础项目)
[![Local](https://img.shields.io/badge/runs-local%20%C2%B7%20single%20user-success?style=flat-square)](#先启动课程)
[![Unit Tests](https://img.shields.io/badge/unit%20tests-30%20passing-brightgreen?style=flat-square)](#-教师与维护者)

**课程作者：Connor He**  
面向机械专业研一新生，以工程项目训练 Linux、科学计算与虚拟调试能力。

这是本机运行、单人使用的学习网站。课程包含 6 周基础内容、24 个学习单元、48 道理解题、真实容器实验接口、数值电机实验台、软件安装指南、学习记录与作品导出。第 7–12 周提供机器人与控制、CAE、工业设备软件三条进阶项目规划，尚未提供完整进阶实验。

## 先启动课程

建议在 Ubuntu 24.04 LTS、Python 3.12 上使用。首次安装需要联网。以下操作在**宿主机项目目录**执行，不是在课程终端中执行：

```bash
python3 scripts/bootstrap.py
./start.sh
```

打开 <http://127.0.0.1:8765/>。当前项目已准备 Python 环境，可直接运行 `./start.sh`。如果系统缺少 venv，先安装发行版的 `python3-venv`。按 Ctrl+C 停止本地服务；学习记录保存在 `.state/`，下次启动继续使用。

不需要 Docker 就可以阅读全部基础课程、答题、运行网页电机仿真、填写和导出学习记录。真实终端与任务检查需要下面的实验环境。网页不会把环境缺失当作任务通过。

## 准备真实 Linux 实验

请先阅读[Docker 官方 Ubuntu 安装说明](https://docs.docker.com/engine/install/ubuntu/)和[rootless 模式说明](https://docs.docker.com/engine/security/rootless/)。课程仅使用名为 `rootless` 的 Docker context，要求 cgroup v2 能限制内存与进程数量。

仓库提供可审阅的 `scripts/setup-docker.sh`，适用于**尚未安装 Docker 的 Ubuntu 24.04**。此脚本会通过 sudo 添加官方 APT 软件源、安装 Docker 与 rootless 依赖、停用本次安装的系统 Docker 服务/套接字、创建并启动当前用户的 rootless 服务。已有 Docker 的机器会直接退出，需按官方说明保留并配置现有环境。它不会由网页自动执行。

管理员同意上述主机修改后，在宿主机执行：

```bash
bash scripts/setup-docker.sh
docker --context rootless info
./scripts/prepare-labs.sh
./scripts/prepare-labs.sh --modelica
```

第二次准备同时构建第 6 周 OpenModelica 缓存镜像；基础构建层可以复用。建议至少预留 8 GiB 空闲磁盘、4 GiB 内存；3D 仿真方向建议另行准备 16 GiB 内存与可用图形加速。空间取决于软件源版本及 Docker 缓存，应同时检查项目磁盘和 Docker 数据目录。

构建时联网获取依赖，课堂实验使用缓存的 APT 包和 Python wheels。运行期间普通项目没有外部网络；第 4 周使用内部网络中的第二个容器练习 SSH。课程中的 `sudo apt-get ...` 均指专用课程容器；软件页会标明宿主机操作。

## 六周基础项目

| 周 | 项目 | 主要能力 | 交付证据 |
|---|---|---|---|
| 1 | 建立实验工作站 | 系统、Shell、目录、文本、权限、APT | 实验目录与说明、可执行脚本 |
| 2 | 整理工程数据 | 管道、CSV、缺失值、Git | 原始数据、清洗结果、数据字典、提交 |
| 3 | 自动运行仿真 | Python venv、批处理、进程、日志 | 开环电机参数扫描与运行记录 |
| 4 | 远程计算与交付 | SSH、主机指纹、rsync、tmux | 远程结果、哈希一致性与排障说明 |
| 5 | 编译、测试与调试 | C++、CMake、CTest、GDB | 单位错误的失败证据、修复与复测 |
| 6 | 虚拟电机闭环调试 | OpenModelica、PI、模型对照、故障诊断 | 含参数、原始结果、英文摘要的作品包 |

按每周 6–8 小时组织：单元学习与引导练习约 3.25 小时，其余用于独立任务、排障、复盘和同伴复现。每个单元有解释、命令、预期输出、分层提示、参考解与理解题。完成需同时满足已阅读、理解题至少 80%、实际任务检查通过。

默认学生已有基础 C 或 MATLAB 经验，无需先有 Linux 经验。工具练习服务于机械问题；课程以可复现的工程能力对接招聘要求，录用仍取决于专业深度、项目质量、沟通及岗位条件。

## 电机与数据

网页每次启动一个本地计算进程，求解电气—机械耦合微分方程和数字 PI；曲线不是预存动画。支持开环、负载阶跃、反馈反接、单位混淆、传感器偏差与抗积分饱和，导出实际 CSV 和参数 JSON。

详细参数、单位、指标定义与验证边界见 [电机模型说明](docs/MOTOR_MODEL.md)。模型为教学设定，未经过实机辨识。OpenModelica 对照需要运行真实 `omc` 后才有结果。

学习进度及个人说明保存在 `.state/progress.sqlite3`。数值实验最多保留最近 30 次运行，重要结果及时导出；页面刷新后可重新仿真。容器 `/workspace` 和练习用户主目录使用独立命名卷。停止实验保留文件；**重置会删除当前周实验文件和练习密钥**，请先导出。学习检查历史保留，当前周通过标记清除。

每次只运行一个项目环境；切换项目停止上一项目的进程，第 4 周的远程工作站随项目一起停止。网页关闭不等于停止容器，结束课堂请点击“停止实验”。本地终端仅连接课程容器，无宿主机命令执行接口。

## 教师与维护者

- [教师使用说明](docs/TEACHER.md)：节奏、评价量表、招聘能力映射与课堂准备。
- `scripts/build_content.py`、`scripts/build_software.py` 是内容源文件；修改后分别运行，生成 `course/` 中的 JSON。
- `dist/` 为原生 HTML/CSS/JavaScript 前端，终端组件及许可证均随仓库提供，无远程字体或 CDN 依赖。
- `server/` 为本地 API、容器管理和数值求解；`lab/` 为课程镜像、初始数据与任务检查器。

```bash
.venv/bin/python -m unittest discover -s tests -v
python3 -m py_compile server/*.py lab/*.py scripts/*.py
node --check dist/app.js
```

以上 32 项自动测试覆盖数值物理、HTTP 权限边界、保存/导出、内容关联、命令语法、C++ 单位换算与可独立执行的实验参考解。另提供真实容器验收：

```bash
.venv/bin/python scripts/verify_labs.py --weeks 1 2 3 4 5
# 准备好 OpenModelica 镜像后：
.venv/bin/python scripts/verify_labs.py --weeks 6
```

验收使用独立标记的测试容器，不操作学生项目；正常结束后清理这些容器和卷，报告保存在 `.state/acceptance-report.json`。`--keep-failed` 可在失败时保留测试环境供诊断。脚本通过已知的辅助容器公钥准备 SSH 测试身份；课堂中学生仍需学习交互核对指纹与配置登录。

前五周的 20 个真实实验检查及终端 WebSocket、科学计算交叉对照、导出、停止后恢复已通过。第六周 OpenModelica 验收状态见教师说明及最新报告。开班前仍应在目标教学机器复测。

## 许可证

本项目以 **GNU General Public License v3.0**（GPL-3.0）发布，许可证全文见 [LICENSE](LICENSE)。

Copyright (C) 2026 Connor He

你可以自由地使用、修改和分发本项目，包括用于教学；但衍生作品必须以相同协议开源，且不得附加额外限制。本项目按“现状”提供，不附带任何明示或暗示的担保。

### 第三方组件

`dist/vendor/` 下的终端组件为第三方开源软件，其版权声明与许可证随文件一并分发，保留原始条款：

| 组件 | 版本 | 许可证 | 许可证文件 |
|---|---|---|---|
| [@xterm/xterm](https://github.com/xtermjs/xterm.js) | 5.5.0 | MIT | [`dist/vendor/xterm-LICENSE`](dist/vendor/xterm-LICENSE) |
| [@xterm/addon-fit](https://github.com/xtermjs/xterm.js) | 0.10.0 | MIT | [`dist/vendor/addon-fit-LICENSE`](dist/vendor/addon-fit-LICENSE) |

MIT 与 GPL-3.0 兼容，上述组件仍依其原始 MIT 条款授权。准确的版本号与完整性校验值记录于 [`dist/vendor/manifest.json`](dist/vendor/manifest.json)。项目不引用远程字体或 CDN，离线可用。
