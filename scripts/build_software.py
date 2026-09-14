import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
S=[]
def step(title,explanation,command,expected,troubleshooting='先读最后一条错误，核对执行位置、软件版本和路径；不要重复执行不理解的管理员命令。'):
 return dict(title=title,explanation=explanation,command=command,expected=expected,troubleshooting=troubleshooting)
def add(id,name,category,stage,summary,scope,source,resource,steps,verify,uninstall,notes=[]):
 S.append(dict(id=id,name=name,category=category,stage=stage,summary=summary,scope=scope,source=source,license='使用开源发行版；再分发保留各工具原始许可证和第三方声明。',resource=resource,steps=steps,verify=verify,uninstall=uninstall,notes=notes))
add('linux-tools','Linux 基础工具','文件、文本与版本管理','基础必修','认识系统、编辑文件、查询帮助和管理软件。','第1周课程容器；本机安装时在个人终端执行sudo。','https://documentation.ubuntu.com/server/how-to/software/package-management/','基础镜像内预装常用工具；tree作为真实安装练习。',[
step('识别发行版与目录','先确认操作对象。容器uname共享宿主内核，发行版以os-release为准。','cat /etc/os-release\nwhoami\npwd','Ubuntu 24.04、student、/workspace。'),
step('了解软件索引','apt-get update刷新索引，不等同升级全部软件。本周使用已准备的本地APT仓库。','sudo apt-get update','软件索引读取成功。','如果找不到/opt/apt-repo，请重新准备课程镜像。'),
step('安装并验证tree','只在第1周管理员课程环境执行。宿主机与容器的软件安装相互独立。','sudo apt-get install -y tree\ntree --version\ndpkg-query -W tree','tree真实安装并显示版本。'),
step('查看帮助与文件归属','学会自己查参数，避免机械复制。','tree --help\ndpkg -L tree\nls -l /workspace','知道程序位置与目录权限。')],
'command -v bash nano git tree\ntree --version','sudo apt-get remove tree',['课程普通周不提供管理员权限。不要使用chmod 777修复未知权限问题。'])
add('python','Python 科学计算与控制','数值计算与绘图','基础必修','NumPy、SciPy、Matplotlib、python-control，用于电机分析和独立对照。','/workspace/.venv；避免改动系统Python。','https://python-control.readthedocs.io/en/stable/intro.html','使用适配Python3.12的二进制wheels；不安装完整Conda或Slycot。',[
step('创建隔离环境','每个工程维护独立依赖。课程已经提供python3-venv。','python3 -m venv .venv\n.venv/bin/python --version','Python 3.12环境可用。','宿主机缺venv时，先在宿主终端sudo apt-get install python3-venv。'),
step('从课堂缓存安装','固定版本清单在镜像内。--no-index防止课堂临时依赖互联网。','.venv/bin/python -m pip install --no-index --find-links=/opt/wheels -r /opt/course/science-requirements.txt','四个库及依赖安装成功。','没有匹配wheel时检查Python版本与CPU架构，不要修改系统Python。'),
step('实际导入并记录版本','版本文件比截图更适合复现。',".venv/bin/python -c \"import sys,numpy,scipy,matplotlib,control; print(sys.version,sys.prefix); print(numpy.__version__,scipy.__version__,matplotlib.__version__,control.__version__)\"",'解释器前缀为项目.venv，四库导入成功。'),
step('运行一个实际算例','labtool的基础求解器无需第三方库；独立科学计算对照会明确检查已安装依赖。','labtool simulate --voltage 12 --output results/openloop.csv\n.venv/bin/python /opt/course/science_check.py','得到真实数值结果和独立对照误差。')],
'.venv/bin/python -m pip check\n.venv/bin/python /opt/course/science_check.py',
'# 确认pwd为/workspace且不需要此环境后\nrm -rf -- .venv',['正常联网的宿主项目可用pip按相同版本清单安装；不要sudo pip。','清理只删除当前项目虚拟环境，不删除系统Python。'])
add('remote','OpenSSH · rsync · tmux','远程计算','基础必修','密钥认证、同步结果、保留远程终端会话。','第4周主容器与workstation辅助容器，内部网络。','https://www.openssh.com/manual.html','两个轻量容器；不对宿主发布SSH端口。',[
step('确认工具','基础镜像已经准备客户端；安装是镜像准备阶段真实完成的。','ssh -V\nrsync --version\ntmux -V','三个工具可用。'),
step('核对主机与创建密钥','以页面显示的可信SSH指纹核对workstation。课堂初始口令仅为linuxlab。','test -f ~/.ssh/id_ed25519 || ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519\nchmod 600 ~/.ssh/id_ed25519\nssh-copy-id student@workstation','完成主机身份核对和公钥安装。','不要覆盖已有私钥，不关闭主机指纹检查。'),
step('测试连接与文件同步','先认证，再处理文件路径。','ssh -o BatchMode=yes student@workstation hostname\nssh student@workstation "mkdir -p jobs/motor"\nrsync -av config student@workstation:jobs/motor/','hostname为workstation，配置成功同步。')],
'ssh -o BatchMode=yes student@workstation hostname',
'# 使用页面“重置第4周实验”清理专属容器和课堂密钥。',['课程口令只属于隔离辅助机。真实服务器遵守管理员的认证和作业调度规定。'])
add('cpp','GCC · CMake · GDB','编译、测试与调试','基础必修','使用提供的C++工程定位并修复一个单位换算问题。','第5周课程容器。','https://cmake.org/cmake/help/latest/guide/tutorial/index.html','小型C++17工程，默认单线程编译。',[
step('检查工具链','本机安装可用sudo apt-get install build-essential cmake gdb；课程镜像已预装。','g++ --version\ncmake --version\ngdb --version','三个工具都报告版本。'),
step('配置与编译','Debug保留符号，-j1降低内存占用。','cmake -S sensor -B sensor/build -DCMAKE_BUILD_TYPE=Debug\ncmake --build sensor/build -j1','生成sensor_tool和test_units。'),
step('运行测试与调试','初始工程故意出错，测试失败是有效的教学证据。','ctest --test-dir sensor/build --output-on-failure\ngdb -q sensor/build/sensor_tool','CTest失败指出单位错误，GDB能加载符号。','若ptrace受限，记录环境异常并检查课堂调试配置，不使用privileged。')],
'sensor/build/sensor_tool 10\nctest --test-dir sensor/build --output-on-failure',
'# 仅删除可重新生成的构建目录\nrm -rf -- sensor/build',['修复前输出600，修复后应约95.492966；代码编译成功不代表物理正确。'])
add('openmodelica','OpenModelica · Modelica 标准库','机电系统仿真','基础必修','独立的电气—机械组件模型与Python结果对照。','第6周专用容器；OMEdit选做在本机桌面运行。','https://openmodelica.org/download/download-linux/','按需下载omc及编译依赖与标准库；先核对实际空间，GUI另行安装。',[
step('准备本周软件包','这一步在宿主机教程项目目录运行。脚本通过官方签名源构建缓存镜像，保留安装日志。','./scripts/prepare-labs.sh --modelica','mechlinux-modelica:1.0镜像准备完成。','空间不足应先腾出空间；基础实验无需等待这一镜像。'),
step('在课程容器安装','启动第6周后，从本地APT仓库实际安装编译器与库缓存。','sudo apt-get update\nsudo apt-get install -y --no-install-recommends omc omlibrary\nomc --version | tee results/omc-version.txt','显示实际omc版本。'),
step('准备标准库','编译器与库独立检查；Modelica标准库使用课程缓存版本4.0.0。','omc scripts/prepare_modelica.mos','loadModel返回true。','库未找到时检查/opt/modelica目录和MODELICAPATH，而不是伪造安装状态。'),
step('运行组件模型','无图形求解器实际编译模型，运行5秒12V无负载算例，再统一字段输出。','labtool modelica\nlabtool simulate --voltage 12 --output results/openloop.csv\nlabtool compare','两份真实CSV和误差报告。')],
'omc --version\nlabtool modelica\nlabtool compare',
'sudo apt-get remove omc omlibrary\n# 项目重置会清除本周安装和作品，先导出。',['OMEdit按需通过官方包安装，不是网页内嵌桌面应用。','首版通过CSV独立对照，不引入FMU联合仿真。','没有真实执行omc时，平台不得标记对照通过。'])
add('freecad','FreeCAD · Gmsh · CalculiX','CAD 与结构分析','方向按需','对电机安装支架进行参数建模、小网格线性静力验算。','第7–8周规划；本机桌面建模，项目目录交换文件。','https://www.freecad.org/downloads.php','需要图形桌面；小模型起步，不同时加载大型装配。',[
step('获取FreeCAD','从官方站选择Linux稳定AppImage并核对版本与文件名。以下文件名需替换为实际下载名称。','chmod u+x FreeCAD-实际版本-x86_64.AppImage\n./FreeCAD-实际版本-x86_64.AppImage','打开FreeCAD并记录About中的版本。','AppImage需要FUSE时按官方说明补依赖，或使用--appimage-extract解包运行；不要使用虚构文件名。'),
step('准备网格和求解器','在Ubuntu24.04宿主终端安装发行版包。','sudo apt-get update\nsudo apt-get install gmsh calculix-ccx\ncommand -v gmsh ccx','两个程序可定位。'),
step('配置与验证FEM流程','在FreeCAD FEM设置中指定Gmsh和CalculiX路径，不假设AppImage已捆绑它们。','gmsh --version\nccx -v','建立小型悬臂梁，施加载荷与固定约束，求解并与梁理论比较。')],
'最小算例：小型梁/支架，记录几何、材料、载荷、约束、网格与位移单位。',
'# 删除本人下载的AppImage；APT工具按需移除\nsudo apt-get remove gmsh calculix-ccx', ['这是进阶安装导航，完整专业实验尚未上线。','开源工具训练通用工程流程，不声称替代特定企业商业软件的全部功能。'])
add('openfoam','OpenFOAM 14 · ParaView','流体计算与后处理','方向按需','小型冷却管道层流算例、批量求解与结果验证。','第9–12周CAE规划；本机求解与桌面后处理。','https://openfoam.org/download/14-ubuntu/','较大安装；使用小网格层流案例，记录质量守恒和网格敏感性。',[
step('选择发行线','统一使用OpenFOAM Foundation 14，按官方Ubuntu安装页配置签名软件源。不要混用其它发行线的命令。','# 按上方官方安装页配置软件源后执行\nsudo apt-get update\nsudo apt-get install openfoam14','Foundation 14安装成功。'),
step('加载环境','只在当前终端source，先验证后再决定是否写入个人Shell配置。','source /opt/openfoam14/etc/bashrc\nfoamRun -help','求解器帮助可用。'),
step('验证小型示例','复制官方教程后先生成网格，检查日志再运行求解与后处理。','mkdir -p "$FOAM_RUN"\ncp -r "$FOAM_TUTORIALS/incompressibleFluid/pitzDailySteady" "$FOAM_RUN/"\ncd "$FOAM_RUN/pitzDailySteady"\nblockMesh\nfoamRun\nparaFoam','网格、求解日志和结果可用。','复制前确认目标不存在；图形后处理在桌面运行。')],
'检查网格、收敛历史、质量守恒和解析压降基准。',
'sudo apt-get remove openfoam14',['完整实验尚未上线；软件可运行不代表数值结果可信。','ParaView可使用Ubuntu提供版本；需要更新版时从官方站下载匹配Linux二进制并记录版本。'])
add('ros2','ROS 2 Jazzy · Gazebo Harmonic','机器人与虚拟控制','方向按需','从单关节到差速机器人，连接控制框架和物理仿真。','第7–12周机器人规划；Ubuntu24.04。','https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html','需要更多磁盘与图形资源；先单关节/低频传感器或无GUI求解。',[
step('准备官方ROS源','依官方安装页配置UTF-8 locale、Universe与ros2-apt-source签名源；本步骤不使用其它版本的源。','locale\ncat /etc/os-release','UTF-8与Ubuntu24.04。'),
step('安装匹配组件','源配置完成后安装Jazzy以及官方配对的Gazebo供应包。','sudo apt-get update\nsudo apt-get install ros-jazzy-desktop ros-jazzy-ros-gz ros-jazzy-ros2-control ros-jazzy-ros2-controllers ros-jazzy-gz-ros2-control','Jazzy与Harmonic相关包安装成功。'),
step('验证通信','分别在两个终端加载同一环境并运行示例。','source /opt/ros/jazzy/setup.bash\nros2 run demo_nodes_cpp talker\n# 第二终端加载同一环境后：\nros2 run demo_nodes_py listener','listener收到talker消息；再做单关节仿真。')],
'验证ros2节点通信与gz_ros2_control单关节示例，保存版本及启动日志。',
'# 按官方卸载章节逐项处理，先备份自己的工作空间。',['mock组件只用于接口联调，不证明电机电流或负载响应。','Gazebo关节模型不会自动包含电气驱动器、热模型或实机实时性。'])
add('industrial','Mosquitto · PyModbus','工业通信与虚拟设备','方向按需','将虚拟电机接到寄存器与消息接口，测试断连、超时和恢复。','第7–12周工业设备规划；先仅本机或隔离网络。','https://mosquitto.org/download/','轻量无GUI服务，默认不向公网暴露端口。',[
step('安装消息代理','宿主安装服务会改变本机服务状态，先了解监听范围；课堂优先在专用环境操作。','sudo apt-get install mosquitto mosquitto-clients\nmosquitto -h','工具可用。'),
step('建立协议项目环境','单独venv，安装后固定实际版本。','python3 -m venv .venv\n.venv/bin/python -m pip install pymodbus\n.venv/bin/python -m pip freeze > requirements.txt','pymodbus可导入。'),
step('验证消息往返','在已启动本地代理的两个终端分别订阅与发布。','mosquitto_sub -h localhost -t lab/motor/state\n# 另一个终端：\nmosquitto_pub -h localhost -t lab/motor/state -m "ready"','订阅端收到ready。')],
'先验证协议往返，再把真实模型的转速/电流接入；记录单位、字节序、超时和恢复行为。',
'sudo apt-get remove mosquitto mosquitto-clients\n# 项目venv确认不用后可删除。',['协议返回固定假数值只证明通信，不构成机电闭环仿真。','PyModbus不同版本API可能变化，按已锁定版本的官方文档使用。'])
add('linuxcnc','LinuxCNC 仿真','数控与虚拟轴','选修','认识G-code、HAL与虚拟数控轴运动。','独立Debian虚拟机；不作为Ubuntu24.04基础必装。','https://linuxcnc.org/docs/html/getting-started/getting-linuxcnc.html','额外虚拟机磁盘与桌面资源；没有硬件时只用仿真配置。',[
step('选择官方仿真环境','通过官方支持的Debian安装路线准备隔离虚拟机，不替换当前学生操作系统。','# 在独立虚拟机按官方安装说明准备 linuxcnc-uspace\nlinuxcnc','配置选择器可打开。'),
step('打开sim配置','选择自带sim示例，观察坐标、轴与G-code；记录命令与虚拟位置。','# 在配置选择器选择sim示例，不选择真实机床驱动配置。','虚拟轴随示例程序运动。')],
'验证虚拟坐标、限位和HAL信号逻辑，说明没有实机与实时性验证。',
'# 备份项目后删除专用虚拟机即可；不改动主系统内核。',['普通内核可做仿真；实机控制需要适合的实时内核与硬件。'])
(R/'course/software.json').write_text(json.dumps(S,ensure_ascii=False,indent=2))
print('Saved',len(S),'software guides')
