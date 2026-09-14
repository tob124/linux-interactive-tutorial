"""Authoritative, editable course content. Authors: Connor He and Astra."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
lessons=[]
W=[('建立实验工作站','认识系统、文件与权限','机械实验工作目录'),('整理工程数据','从原始日志到可信结果','电机数据质量报告'),('自动运行仿真','环境、脚本与批量实验','开环电机参数扫描'),('远程计算与交付','连接、同步、保活与排障','远程仿真交付包'),('编译、测试与调试','用证据定位代码问题','传感器工具修复提交'),('虚拟电机闭环调试','安装、对照、控制与故障','可复现虚拟电机作品')]
def L(week,n,title,summary,concept,practice,explain,commands,goal,solution,questions,software):
    ident=f'w{week}-{n}'
    quiz=[]
    for i,(question,correct,a,b,c) in enumerate(questions):
        options=[correct,a,b,c];offset=(week+n+i)%4;options=options[offset:]+options[:offset]
        quiz.append(dict(question=question,options=options,answer=options.index(correct),explanation=correct+'。请结合本课的实际输出解释原因，而不是只记住选项。'))
    lessons.append(dict(id=ident,week=week,order=n,title=title,duration=45 if n<4 else 60,summary=summary,objectives=[summary,goal,'保留命令、结果与判断依据，能向同学解释操作。'],sections=[dict(title='先理解这件事',body=concept),dict(title='一步一步完成',body=practice),dict(title='检查结果与常见问题',body=explain)],commands=[dict(command=c,explanation=e,expected=x) for c,e,x in commands],tasks=[dict(id=ident+'-t1',title=goal,description='在本周真实实验终端完成下面的交付。先按本课步骤操作，再点击“检查任务结果”。'+goal,check=ident,hints=['先用 pwd 确认当前是 /workspace；读懂错误信息中的路径、权限和程序名。',practice, '对照参考解检查目标文件与输出。允许使用其它能产生同等结果的方法。'],solution=solution)],quiz=quiz,deliverable=goal,glossary=[dict(en='working directory',zh='当前工作目录'),dict(en='exit status',zh='程序退出状态'),dict(en='reproducibility',zh='可复现性')],softwareIds=software))
L(1,1,'从这里认识 Linux','分清操作系统、终端和 Shell，认识课程实验环境。',
'Linux 是操作系统内核；Ubuntu 把内核、软件管理和桌面工具组合成一个发行版。机械研究中，批量计算、远程工作站、机器人软件和设备日志常通过 Linux 串成工作流。终端是输入输出窗口，Bash 是解释命令的 Shell。你敲下的命令并不是发给网页，而是由实验容器中的 Bash 执行。',
'先启动第 1 周实验，观察提示符中的用户与主机名。输入 whoami 确认普通账户 student，pwd 查看当前目录，uname 观察系统信息。课程目录是 /workspace，宿主机是你实际使用的电脑，容器是隔离练习空间；二者的文件和管理员权限不能混为一谈。用编辑器记录你自己的理解。',
'命令名和参数之间用半角空格，不要复制提示符 $。Ctrl+C 可以中断前台命令，方向键可以找回历史输入，Tab 可以补全名称。uname 输出的是共享内核信息，不能据此认为容器拥有独立内核。学习笔记只检查是否存在关键概念，解释是否准确仍需要你自己或同伴复核。',
[('whoami\npwd\nuname -s','观察用户、工作位置和内核名称。','student、/workspace、Linux'),('mkdir -p notes\nnano notes/linux.txt','打开文本编辑器；写下 Linux、Shell、/workspace 的含义。Ctrl+O 保存，Enter 确认，Ctrl+X 退出。','笔记文件保存成功。'),('cat notes/linux.txt','读回刚写的文件，确认保存位置。','能看到自己的笔记。')],
'保存一份区分 Linux、Shell 和 /workspace 的笔记。',"mkdir -p notes\nprintf 'Linux 是内核；Shell 解释命令；/workspace 是课程项目目录。\\n' > notes/linux.txt",
[('谁解释 pwd 命令？','Shell','显示器','CSV 文件','电机控制器'),('容器中的 /workspace 是什么？','本课程的实验工作目录','宿主机所有文件的副本','一条网络地址','CPU 型号')],['linux-tools'])
L(1,2,'组织你的实验目录','用目录结构区分原始数据、处理结果和报告。',
'文件系统是一棵树，/ 是根目录，/workspace 是绝对路径；从当前目录开始写的 experiments 是相对路径。点号 . 表示当前目录，.. 表示上一级。Linux 区分大小写，Motor.csv 与 motor.csv 是不同名称。把原始数据单独保存，是后续结果能够追溯的基础。',
'为 motor-01 建立 raw、processed、reports 三个目录。用 cp 复制课程数据到 raw，保留 data/motor.csv。先用 ls 确认源文件，再执行复制，最后比较两个文件。目录中有空格时用引号包住完整路径；本课采用无空格名称，让脚本更容易维护。',
'cp 默认可能覆盖已有文件，操作前看清目标。mv 会移动或改名；rm 删除后通常没有桌面回收站。需要重新开始时优先使用课程的项目重置，并先导出作品。不要为了目录不存在就随意加 sudo，应该检查路径和目录是否已创建。',
[('pwd\nls -la data','确认数据源存在。','看到 motor.csv。'),('mkdir -p experiments/motor-01/{raw,processed,reports}\ncp data/motor.csv experiments/motor-01/raw/','按职责组织实验文件。','创建三个目录并复制原始数据。'),('cmp data/motor.csv experiments/motor-01/raw/motor.csv','逐字节比较文件；没有输出且退出0表示相同。','原始副本完全一致。')],
'创建三个实验目录并保留未经修改的原始数据。','mkdir -p experiments/motor-01/{raw,processed,reports}\ncp data/motor.csv experiments/motor-01/raw/',
[('绝对路径从哪里开始？','根目录 /','当前目录','用户姓名','文件扩展名'),('为什么保留 raw 数据？','让处理结果可以追溯和重算','为了增加文件数量','因为 CSV 不能复制','为了绕过权限')],['linux-tools'])
L(1,3,'编辑一份可复现的实验说明','通过文本文件记录工况、单位和数据来源。',
'工程项目除了程序，还需要说明别人如何运行。Markdown 是带简单标记的纯文本：# 表示标题，列表可以记录步骤。文本文件可以被终端查看、版本管理和自动处理。不要把“我知道怎么做”当作交付；一个陌生同学应该能根据说明找到数据和运行入口。',
'用 nano 编辑 notes/experiment.md，写明项目编号 motor-01、输入电压 12 V、转速单位 rpm，以及原始数据的位置。区分数字和单位：12 是数值，V 是电压单位，rpm 表示每分钟转数。记录环境和条件，避免以后把不同工况的曲线直接比较。',
'用 cat 读回文件，确认中文编码正常。命令中的 > 会覆盖目标文件，>> 会追加；看到内容丢失时先检查是否误用了覆盖。复制参考解只是建立说明的起点，应补上自己的观察。验收只核对必要信息的存在，不替代工程文档的人工作品评价。',
[('nano notes/experiment.md','记录项目、工况、单位和数据路径。','包含 motor-01、12 V、rpm 和原始数据。'),('cat notes/experiment.md','检查已保存内容。','正文与编辑器一致。'),('wc -l notes/experiment.md','统计行数，认识命令选项。','显示实际文本行数。')],
'提交包含项目、工况、单位与原始数据位置的说明。',"printf '# motor-01\\n输入：12 V\\n转速单位：rpm\\n原始数据：data/motor.csv\\n' > notes/experiment.md",
[('> 对已有文件做什么？','覆盖内容','只追加','改变文件权限','改变文件编码'),('rpm 的含义是？','每分钟转数','每秒弧度','电流单位','电压单位')],['linux-tools'])
L(1,4,'权限与第一次软件安装','在专门的管理员实验环境安装工具并运行脚本。',
'每个文件有所有者和权限，r/w/x 分别表示读、写和执行。普通用户只能按权限访问资源；sudo 临时以管理员身份运行命令。APT 安装的是发行版软件包，包含文件和依赖信息。课程仅在第 1、6 周的专用实验配置允许容器内 sudo，不能把这种权限理解为宿主机管理员权限。',
'本课在课程容器安装 tree。镜像准备阶段已缓存软件包，本地仓库不需要互联网。先更新软件索引，再安装 tree，最后运行 tree --version。接着创建 hello.sh，写入 Bash 解释器声明和输出命令，给所有者执行权限，去掉其他用户的写权限。',
'Permission denied 不一定需要 sudo：执行脚本失败可能只是没有 x 权限。APT 报找不到包时，应检查软件索引与课堂镜像是否准备好。绝不使用 chmod 777 作为通用修复。检查器会运行脚本、检查权限和软件包状态，安装过程不能只靠文字记录证明。',
[('sudo apt-get update\nsudo apt-get install -y tree\ntree --version','仅在第1周管理员实验容器中安装和验证 tree。','tree 能报告版本。'),("printf '#!/usr/bin/env bash\\necho motor-lab-ready\\n' > scripts/hello.sh\nchmod u+x,go-w scripts/hello.sh",'创建最小脚本并赋予合适权限。','所有者可执行，其他用户不可写。'),('./scripts/hello.sh\nls -l scripts/hello.sh','真实运行后观察权限。','输出 motor-lab-ready。')],
'安装 tree，并让 hello.sh 以正确权限输出指定信息。',"sudo apt-get update\nsudo apt-get install -y tree\nprintf '#!/usr/bin/env bash\\necho motor-lab-ready\\n' > scripts/hello.sh\nchmod u+x,go-w scripts/hello.sh\n./scripts/hello.sh",
[('脚本缺少执行权限时应先做什么？','检查权限并按需增加 x','给全部文件777','重装系统','删除原始数据'),('apt-get update 的主要作用是？','更新软件包索引','升级全部已安装软件','运行电机仿真','清空用户目录')],['linux-tools'])
L(2,1,'读懂电机测量数据','识别 CSV 表头、单位、采样时间和缺失值。',
'CSV 用分隔符组织记录，但后缀不是数据正确性的保证。本课 data/motor.csv 是人为设计的教学采样日志，不是电机模型的实测标定数据。time_s 是秒，voltage_V 是伏，current_A 是安，speed_rpm 是每分钟转数，load_Nm 是牛米。时间戳间隔为0.1秒，其中一行故意缺少电流值。',
'先读表头和前几行，再查看行数。把原文件复制到 data/raw/motor.csv，保持这一副本不变。建立数据字典，逐列说明含义与单位，并写明缺失电流怎么处理。空值不同于零：零可以是正确测量值，空值表示没有记录，不能直接拿去算平均。',
'head 和 tail 适合快速观察，less 适合较大的文件，按 q 退出。wc -l 包括表头，不能把12行当成12条有效测量。不要从一条异常数据直接推断电机损坏；先确认采样、编码、单位和数据完整性。数据字典是后续同伴复现的重要输入。',
[('head -n 5 data/motor.csv\ntail -n 3 data/motor.csv\nwc -l data/motor.csv','先观察数据，不急于计算。','12行，包含1行表头和11行数据。'),('mkdir -p data/raw\ncp data/motor.csv data/raw/motor.csv','保存原始副本。','字节内容一致。'),('nano notes/data-dictionary.md','记录五列单位和缺失值处理。','逐列说明完整。')],
'保存原始副本和含五个字段、缺失值说明的数据字典。',"mkdir -p data/raw\ncp data/motor.csv data/raw/motor.csv\nprintf 'time_s 秒\\nvoltage_V 伏\\ncurrent_A 安\\nspeed_rpm 每分钟转数\\nload_Nm 牛米\\n缺失值：删除空电流行，不能当作零。\\n' > notes/data-dictionary.md",
[('空电流与0A有什么区别？','空值是缺失记录，0A可能是有效值','完全相同','空值表示无限大','0A一定是设备坏了'),('wc -l 是否包含表头？','包含','不包含','只计算表头','只计算有效数值')],['linux-tools'])
L(2,2,'用管道筛选工况','理解标准输入输出、筛选和重定向。',
'程序通常从标准输入读数据，把正常结果写到标准输出，把错误写到标准错误。管道 | 把前一个程序的标准输出连接给后一个程序，> 把结果写入文件。awk 可按列处理简单 CSV。本课数据没有引号内逗号，因此可用 -F,；真实复杂 CSV 应使用专门的 CSV 解析库。',
'我们要保留表头，筛选 current_A 大于2A的行。awk 中 NR 是行号，$3 是第三列，NR==1 可保留表头。先把输出显示在终端确认，再重定向到 results/high-current.csv。阈值是课程练习条件，不是工业电机的安全电流标准。',
'预期有0.1、0.2、0.4秒三行记录。用wc检查时应再加上表头，共4行。不要把输出写回正在读取的同一个输入文件，否则Shell会先截断它。输出为空时依次核对分隔符、列号和阈值，保留原始数据可以随时重算。',
[("awk -F, 'NR==1 || $3>2' data/motor.csv",'保留表头和电流大于2A的行。','表头及3行记录。'),("awk -F, 'NR==1 || $3>2' data/motor.csv > results/high-current.csv",'确认结果后保存到新文件。','原始文件不变。'),('cat results/high-current.csv\nwc -l results/high-current.csv','对照时间戳与行数。','4行，包括表头。')],
'筛出高电流记录并保留表头和原始文件。',"awk -F, 'NR==1 || $3>2' data/motor.csv > results/high-current.csv",
[('管道传递的通常是什么？','前一程序的标准输出','所有硬盘文件','管理员密码','屏幕像素'),('为何不能把输出重定向回输入文件？','Shell会先截断目标文件','CSV不支持写入','文件会自动加密','只能用root读CSV')],['linux-tools'])
L(2,3,'清洗数据并报告质量','显式处理缺失值，核对清洗前后的记录数量。',
'数据清洗必须有规则和数量记录，不能靠删除看起来“不顺眼”的行。本课只删除电流为空的记录，保留时间戳与其余字段。这样会形成不等间隔时间序列，后续积分或频谱分析不能再默认每两行都相隔0.1秒。保留时间列和处理说明比得到一张漂亮曲线更重要。',
'用 awk 判断第三列是否为空，同时保留表头。清洗后有10条有效记录，缺失1条。把统计写入 quality.txt，并观察0.2秒与0.4秒之间缺少了0.3秒。不要用插值偷偷填补缺失，若选择插值必须另写规则并说明其对结论的影响。',
'验收会解析CSV内容，比较数据行而非只检查文件存在。表头拼错、漏掉有效零值、删除了不同时间戳都会失败。数值格式0.0与0通常不影响物理含义；单位和缺失处理才是需要明确说明的信息。最后核对原始数据仍未修改。',
[("awk -F, 'NR==1 || $3!=\"\"' data/motor.csv > results/clean.csv",'保留所有非空电流记录，包括0A。','表头加10条有效记录。'),("printf 'valid_rows=10\\nmissing_rows=1\\n' > results/quality.txt",'记录清洗统计。','两项数量可核对。'),('cat results/quality.txt\nwc -l results/clean.csv','验证数量。','clean.csv共11行。')],
'生成规则明确的 clean.csv 与 quality.txt。',"awk -F, 'NR==1 || $3!=\"\"' data/motor.csv > results/clean.csv\nprintf 'valid_rows=10\\nmissing_rows=1\\n' > results/quality.txt",
[('清洗后时间间隔一定不变吗？','不一定，删除记录可能造成时间缺口','一定不变','时间戳可以删除','应把时间全部改成0'),('本课为什么保留0A？','0是有效数值，不等于缺失','零值都是异常','为了凑行数','因为awk不能删除0')],['linux-tools'])
L(2,4,'用 Git 保存工程变化','建立本地版本记录并区分源码与生成结果。',
'Git 保存一系列可回看的提交，不是云盘，也不要求先注册在线账户。工作区是文件当前内容，暂存区决定下一次提交包含什么，提交是有说明的快照。应版本管理数据字典、代码和配置，虚拟环境及可重新生成的结果一般不放入仓库。',
'在/workspace初始化仓库，仅为当前仓库设置课程身份。创建README说明数据来源和清洗方法，用.gitignore排除.venv、results、build。git status查看变化，git add明确选择文件，git diff --cached检查将要提交的内容，再写一句有意义的提交说明。',
'没有变化可提交不是错误，可能说明你已经提交过。用户身份是Git元数据，不是Linux登录凭据。不要为了课程覆盖宿主机的全局Git配置。回退前先看差异，避免丢失未提交工作；本课只在隔离项目中练习。后续修复缺陷时，会用提交记录解释改变了什么。',
[('git init\ngit config user.name "Student"\ngit config user.email "student@example.invalid"','仅设置当前实验仓库身份。','生成.git目录。'),("printf '# 电机数据质量实验\\n原始数据：data/raw/motor.csv\\n' > README.md\nprintf '.venv/\\nresults/\\nbuild/\\n' > .gitignore\ngit add README.md notes/data-dictionary.md .gitignore",'选择需要保留的说明文件。','暂存区有三个文件。'),('git diff --cached\ngit commit -m "Document motor data and cleaning rules"\ngit log --oneline -3','检查并提交。','至少一个可解释的提交。')],
'提交 README、数据字典和合理的忽略规则。',"git init\ngit config user.name Student\ngit config user.email student@example.invalid\nprintf '# Motor data\\n' > README.md\nprintf '.venv/\\nresults/\\nbuild/\\n' > .gitignore\ngit add README.md notes/data-dictionary.md .gitignore\ngit commit -m 'Document motor data'",
[('git add 的作用是？','选择下次提交的内容','上传全部文件','删除历史','安装Git'),('为什么不提交.venv？','可根据依赖记录重建且通常体积大','Python不允许版本管理','它是管理员密码','它永远不会变化')],['linux-tools'])
L(3,1,'安装科学计算环境','用独立虚拟环境安装并记录 Python 依赖。',
'系统Python可能被操作系统使用，研究项目应建立自己的venv。激活环境只是调整当前Shell查找程序的路径；最可靠的方法是直接调用.venv/bin/python。NumPy处理数值数组，SciPy提供科学计算，Matplotlib绘图，python-control用于控制系统分析。这些工具无需商业软件授权即可完成本课实验。',
'创建.venv后，使用其pip从课程预缓存的wheels安装锁定依赖。--no-index表示不访问在线索引，--find-links指定本地包目录。在宿主机正常联网安装时可以使用官方安装说明，但不能把sudo pip作为项目环境管理方式。完成后实际导入四个库并记录版本。',
'“No module named”通常是装包与运行用了不同解释器。检查sys.executable和sys.prefix，确认路径位于/workspace/.venv。复制整个venv到另一台电脑不可靠，应保存依赖版本后重建。课堂镜像没有缓存时会明确失败，不能把依赖未安装显示为检查成功。',
[('python3 -m venv .venv\n.venv/bin/python -m pip install --no-index --find-links=/opt/wheels -r /opt/course/science-requirements.txt','创建隔离环境并从本地缓存安装。','安装过程真实完成。'),(".venv/bin/python -c \"import sys,numpy,scipy,matplotlib,control; print(sys.version); print(sys.prefix); print('numpy',numpy.__version__); print('scipy',scipy.__version__); print('matplotlib',matplotlib.__version__); print('control',control.__version__)\" > results/environment.txt",'导入库并记录版本。','文件包含Python和四个库版本。'),('cat results/environment.txt','确认解释器前缀。','/workspace/.venv。')],
'建立可导入四个科学计算库的venv并记录版本。',"python3 -m venv .venv\n.venv/bin/python -m pip install --no-index --find-links=/opt/wheels -r /opt/course/science-requirements.txt\n.venv/bin/python -c \"import sys,numpy,scipy,matplotlib,control; print(sys.version,sys.prefix); print('numpy',numpy.__version__,'scipy',scipy.__version__,'matplotlib',matplotlib.__version__,'control',control.__version__)\" > results/environment.txt",
[('如何确认使用的是项目Python？','查看sys.executable和sys.prefix','只看文件名.py','只看桌面图标','检查电机转速'),('为什么用--no-index？','使用已准备的本地包，不查询在线索引','跳过依赖安装','忽略全部错误','安装到系统目录')],['python'])
L(3,2,'运行第一个电机模型','观察电压、电流、转速和反电动势的关系。',
'虚拟电机采用平均永磁直流电机模型：L·di/dt=u−R·i−Ke·ω，J·dω/dt=Kt·i−b·ω−负载。所有内部状态使用SI单位，显示转速时才换算成rpm。参数是教学值，不是真实设备辨识结果；模型没有PWM开关、电流环和热效应。开环表示直接给电压，不根据转速误差调整控制输入。',
'先读config/motor.json，查看模型参数。运行labtool simulate以12V、无负载计算5秒开环响应。工具将真实求解电气和机械状态，写出CSV。看初始电流和转速为零，启动后电流上升，反电动势随转速增加，最终趋于稳态。用终端看数据，再到网页电机实验台对照曲线。',
'无负载稳态转速应接近2122rpm，它来自参数方程，不是预录制曲线。若电压变化却结果不变，要检查命令参数、文件是否被覆盖以及是否读取旧结果。首版labtool提供标准库RK4求解器，科学计算库用于独立线性对照，二者都需要记录版本与计算条件。',
[('cat config/motor.json','阅读教学参数，核对单位。','R2、L0.002、J0.0002、b0.0001、Kt=Ke0.05。'),('labtool simulate --voltage 12 --output results/openloop.csv','运行真实开环数值计算。','保存5秒CSV和参数记录。'),('head -n 4 results/openloop.csv\ntail -n 3 results/openloop.csv','查看起始与最终状态。','零初值，正向稳态。')],
'生成12V、无负载开环电机结果并验证物理趋势。','labtool simulate --voltage 12 --output results/openloop.csv',
[('开环控制是否使用速度误差反馈？','不使用','始终使用','只在Linux使用','由文件名决定'),('为何记录模型参数？','不同参数会产生不同响应，复现需要同一条件','只为美观','用来替代测试','模型参数不会影响结果')],['python'])
L(3,3,'批量比较多个工况','使用循环与退出码组织参数扫描。',
'Linux适合把重复操作写成脚本：变量保存参数，循环逐一执行工况，退出码判断运行是否成功。0通常表示成功，非0表示程序报告失败。工程批处理不仅要输出结果，还要把每行结果对应的参数保存下来，否则无法解释差异。',
'先用Bash循环分别运行6、9、12V，把结果写到不同文件，避免覆盖。随后运行labtool batch生成同三种电压的汇总CSV，记录电压和最终转速。在同一线性无负载模型中，稳态转速应随电压升高，比较时保持其它参数和仿真时长不变。',
'变量展开时使用双引号，防止空格被拆成多个参数。不要用“文件存在”代替计算成功，错误程序也可能留下半成品。出现非0退出时应该停止汇总并查看日志，而不是把空值写成0。批量运行比手动点击更易复现，但前提是先验证单个工况正确。',
[('for v in 6 9 12; do labtool simulate --voltage "$v" --output "results/open-${v}V.csv"; done','逐一计算并使用不同文件名。','生成三个工况文件。'),('labtool batch --output results/batch.csv','生成标准工况汇总。','包含6、9、12V。'),('cat results/batch.csv','对照同参数下的稳态转速。','转速随电压增加。')],
'交付三种电压工况的批量结果表。','labtool batch --output results/batch.csv',
[('为什么不同工况用不同文件名？','避免后一次覆盖前一次结果','因为CSV只能写一次','提高电机效率','改变采样周期'),('退出码0通常表示什么？','程序成功结束','程序一定物理正确','程序未启动','有0条输出')],['python'])
L(3,4,'让批处理留下可追踪日志','观察进程并保留输出、错误与运行状态。',
'进程是正在运行的程序。前台任务占用终端，&让任务在后台运行，$!是刚启动后台任务的PID。ps查看进程，kill发送信号；Ctrl+C通常发送中断。记录PID有助于追踪，但进程结束后PID会复用，不能拿旧PID随意终止别人的程序。',
'创建run_batch.sh并加入set -euo pipefail：遇到未处理失败、未定义变量和管道失败时尽早停止。脚本进入固定项目目录，运行批量任务并输出batch_complete。把标准输出和错误一起写到日志，记录PID，用wait等待结束。保存退出状态而不是猜测任务是否完成。',
'2>&1表示把标准错误连接到当前标准输出；顺序影响结果。日志出现batch_complete只是脚本结束标志，验收仍会核对生成的CSV内容。后台程序运行很快，ps可能已经看不到它，这是正常现象。重要的是结果、日志和退出状态能够互相印证。',
[("printf '#!/usr/bin/env bash\\nset -euo pipefail\\ncd /workspace\\nlabtool batch --output results/batch.csv\\necho batch_complete\\n' > scripts/run_batch.sh\nchmod u+x scripts/run_batch.sh",'建立可复现的批处理脚本。','脚本可执行。'),('mkdir -p logs\n./scripts/run_batch.sh > logs/batch.log 2>&1 &\npid=$!; echo "$pid" > logs/batch.pid; wait "$pid"','后台运行、记录PID并等待完成。','退出0。'),('cat logs/batch.log\ncat logs/batch.pid','检查日志和进程记录。','包含batch_complete和正整数PID。')],
'提交可运行脚本、批量数据和日志。',"printf '#!/usr/bin/env bash\\nset -euo pipefail\\ncd /workspace\\nlabtool batch --output results/batch.csv\\necho batch_complete\\n' > scripts/run_batch.sh\nchmod u+x scripts/run_batch.sh\nmkdir -p logs\n./scripts/run_batch.sh > logs/batch.log 2>&1 &\npid=$!; echo $pid > logs/batch.pid; wait $pid",
[('2>&1 在这里表示什么？','把标准错误写到同一日志','丢弃全部错误','运行两次程序','给进程两个CPU'),('旧PID为什么不能直接用于kill？','PID可能已被别的进程复用','PID永远是0','PID就是文件路径','kill不会产生作用')],['python'])
L(4,1,'连接一台远程工作站','理解SSH的主机身份与用户身份。',
'远程连接有两个身份问题：你连接的是哪台机器，以及那台机器如何确认你。SSH主机公钥指纹用于核对服务器；用户密钥用于登录。课程在内部网络提供workstation辅助容器，它不是互联网机器，临时账户student的练习口令是linuxlab。临时凭据只用于本课程隔离网络。',
'启动第4周后，先读平台显示的可信主机指纹。创建专用于课堂的ed25519密钥；如果文件已存在，不要覆盖。用ssh-copy-id配置远程公钥，首次询问时核对主机指纹后接受，输入练习口令。随后用BatchMode验证无需口令的连接，hostname应返回workstation。',
'公钥可以放到远程authorized_keys，私钥不能发给别人。私钥权限应为600。主机指纹突然变化时先确认是否重置了课程辅助机，不要直接关闭StrictHostKeyChecking。连接失败按网络、主机身份、用户认证顺序检查，避免连续猜密码或修改不相关文件。',
[('test -f ~/.ssh/id_ed25519 || ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519\nchmod 600 ~/.ssh/id_ed25519','只在课程容器创建练习密钥，不覆盖已有私钥。','得到密钥对。'),('ssh-copy-id student@workstation','先核对平台指纹，再输入练习口令linuxlab。','公钥加入辅助机。'),('ssh -o BatchMode=yes student@workstation hostname','验证密钥登录和主机。','workstation。')],
'建立经指纹核对的SSH密钥连接。','test -f ~/.ssh/id_ed25519 || ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519\nchmod 600 ~/.ssh/id_ed25519\nssh-copy-id student@workstation\nssh -o BatchMode=yes student@workstation hostname',
[('主机指纹用于确认谁？','远程服务器身份','本地文件行数','电机型号','用户名拼写'),('哪个文件不应发给别人？','SSH私钥','公钥','实验README','公开模型参数')],['remote'])
L(4,2,'可靠地同步实验输入','区分源与目标，校验远程配置。',
'rsync通过SSH传输文件，适合重复同步。源目录末尾的/有意义：传输目录本身与传输目录内容不同。本课将本地配置同步到远程jobs/motor/config目录，让计算与交互终端分离。config/motor.json 是固定教学参数的记录，本课运行选项由 labtool 命令指定，编辑这份记录不会自动改变模型。不要在不理解影响时使用--delete，因为它会删除目标多余文件。',
'先在远程创建jobs/motor目录。用rsync -av同步config目录，再分别计算本地与远程motor.json的SHA256。校验和一致说明字节一致，不说明模型物理正确，但可以排除文件传输错误。把远程校验结果保存，作为交付包的一部分。',
'“No such file”通常应检查目标父目录和路径末尾斜杠；认证失败则回到上一课验证密钥。不要把本机路径与远程路径混写。需要批量操作时先用--dry-run观察计划变化，再正式执行。第一次同步后应读回内容，确认没有把旧参数放到错误目录。',
[('ssh student@workstation "mkdir -p jobs/motor"','在远程创建项目目录。','目录存在。'),('rsync -av config student@workstation:jobs/motor/','同步配置目录本身。','远程jobs/motor/config/motor.json存在。'),('sha256sum config/motor.json\nssh student@workstation "sha256sum jobs/motor/config/motor.json" | tee results/remote-config.sha256','比较两边校验和并记录。','哈希一致。')],
'同步并校验远程电机配置。','ssh student@workstation "mkdir -p jobs/motor"\nrsync -av config student@workstation:jobs/motor/\nssh student@workstation "sha256sum jobs/motor/config/motor.json" > results/remote-config.sha256',
[('校验和一致证明什么？','文件字节一致','模型必然正确','计算必然收敛','软件版本相同'),('--delete为什么需要谨慎？','会删除目标多余文件','会增加内存','会修改CPU频率','只用于读取')],['remote'])
L(4,3,'断线后继续运行任务','用tmux保留远程会话并取回结果。',
'SSH断开可能结束依附其终端的进程。tmux在服务器保存终端会话，重新登录后可以再次连接。它不是任务调度器，也不保证服务器重启后程序仍运行。要区分网络断线、SSH退出和远程系统重启，这三种情况对任务的影响不同。',
'在workstation创建名为motor的tmux会话，设置工作目录jobs/motor。向该会话发送仿真命令，结果与日志写在远程目录中。命令结束后交互Shell仍保留，所以tmux会话能被再次查看。使用capture-pane读回屏幕，确认完成，再rsync取回CSV。',
'不要把本地出现一个CSV误认为远程任务完成，验收会读取辅助机文件并计算一致性。仿真通常很快；若结果尚未出现，查看远程日志后重试取回。以后使用真实计算集群时，应使用管理员规定的作业队列，本课tmux方法不替代Slurm等资源调度。',
[('ssh student@workstation "mkdir -p jobs/motor/results; tmux has-session -t motor 2>/dev/null || tmux new-session -d -s motor -c /home/student/jobs/motor"','建立可重新连接的远程会话。','motor会话存在。'),('ssh student@workstation "tmux send-keys -t motor \'labtool simulate --voltage 12 --output results/openloop.csv > results/run.log 2>&1\' Enter"','在远程tmux运行仿真。','远程生成真实数据和日志。'),('ssh student@workstation "tmux capture-pane -pt motor; cat jobs/motor/results/run.log"\nrsync -av student@workstation:jobs/motor/results/openloop.csv results/remote-openloop.csv','检查完成后取回结果；若尚未完成，读日志后重试。','本地与远程文件一致。')],
'在远程保留会话、完成仿真并取回同一结果。','ssh student@workstation "mkdir -p jobs/motor/results; tmux has-session -t motor 2>/dev/null || tmux new-session -d -s motor -c /home/student/jobs/motor"\nssh student@workstation "tmux send-keys -t motor \'labtool simulate --voltage 12 --output results/openloop.csv > results/run.log 2>&1\' Enter"\n# 查看日志，待生成结果后继续\nrsync -av student@workstation:jobs/motor/results/openloop.csv results/remote-openloop.csv',
[('tmux主要保存在哪里？','远程服务器上的会话','浏览器缓存','U盘','Git提交'),('tmux能保证服务器重启后程序继续吗？','不能','总能','只要有CSV就能','只要改文件名就能')],['remote'])
L(4,4,'交付可核查的远程任务','按连接、认证和路径层次记录排障证据。',
'“连不上”不是一个完整的问题描述。连接层关注主机名和端口，认证层关注用户、密钥和主机指纹，路径层关注程序、输入和工作目录。把这些层次分开检查，比重复运行同一条失败命令有效。好的故障记录包含现象、证据、原因、修复与复测。',
'再次用SSH确认hostname，运行远程程序并记录退出码，计算取回结果的SHA256。把hostname=workstation、exit_code=0和实际哈希写入notes/remote-run.md，并分别写出连接、认证、路径三个排查点。可以使用ssh -v查看诊断，但发布日志前应检查是否含个人信息。',
'不要复制参考解中的占位哈希，必须读取本次结果。修复后同时验证命令退出成功和结果符合预期。报告应该让同伴知道实际在哪台机器运行、用了哪份参数、从哪里拿回数据。这样的交付习惯同样适用于实验室服务器和企业设备排障。',
[('ssh -o BatchMode=yes student@workstation hostname\nsha256sum results/remote-openloop.csv','核对运行地点和结果。','主机与文件一致。'),("ssh student@workstation \"cd jobs/motor && labtool simulate --voltage 12 --output results/openloop.csv\" > logs/remote-run.log 2>&1\nrun_exit=$?\n{ echo hostname=workstation; echo exit_code=$run_exit; printf 'sha256='; sha256sum results/remote-openloop.csv | cut -d' ' -f1; echo '连接：检查主机名；认证：检查密钥；路径：检查工作目录。'; } > notes/remote-run.md",'记录实际结果与分层排障。','没有占位哈希。'),('cat notes/remote-run.md','让同伴复核记录。','字段完整。')],
'提交包含真实哈希与分层排障的远程交付记录。',"ssh student@workstation \"cd jobs/motor && labtool simulate --voltage 12 --output results/openloop.csv\" > logs/remote-run.log 2>&1\nrun_exit=$?\n{ echo hostname=workstation; echo exit_code=$run_exit; printf 'sha256='; sha256sum results/remote-openloop.csv | cut -d' ' -f1; echo '连接：主机名；认证：密钥；路径：工作目录。'; } > notes/remote-run.md",
[('Permission denied (publickey)优先检查什么？','用户和密钥认证','电机电感','CSV分隔符','显示器分辨率'),('报告中的哈希应来自哪里？','本次实际结果文件','参考文档的示例值','任意随机字符串','项目名称')],['remote'])
L(5,1,'编译一个传感器工具','从源代码生成程序，理解配置、编译和运行。',
'C++源文件需要经过编译和链接才能运行。CMake描述工程怎样构建，实际编译器是GCC等工具。把生成文件放进build目录，可以将源码和编译产物分开。课程给出一个把rad/s转换成rpm的小工程，其中故意包含错误；能够编译并不意味着计算正确。',
'查看sensor中的CMakeLists.txt、src/main.cpp和include/units.hpp。使用-S指定源码目录、-B指定构建目录，并启用Debug以保留调试符号。编译时用-j1减少内存占用。运行sensor_tool 10，观察当前输出600，先记录现象，不急于直接改代码。',
'找不到cmake或g++属于工具环境问题；语法错误属于编译问题；输出错误属于程序行为问题。把三类问题分开能缩小排查范围。修改代码后必须重新构建，直接运行旧二进制常导致“明明改了却没变化”的误判。',
[('ls sensor\ncat sensor/include/units.hpp','观察最小工程与换算函数。','看到故意遗漏2π的实现。'),('cmake -S sensor -B sensor/build -DCMAKE_BUILD_TYPE=Debug\ncmake --build sensor/build -j1','配置并编译。','生成sensor_tool与test_units。'),('sensor/build/sensor_tool 10','观察错误版本行为。','输出600，而正确值应约95.493。')],
'成功构建并记录错误版本的实际输出。','cmake -S sensor -B sensor/build -DCMAKE_BUILD_TYPE=Debug\ncmake --build sensor/build -j1\nsensor/build/sensor_tool 10',
[('编译成功是否代表结果正确？','不代表，还需要测试','代表全部正确','只要没有日志就正确','由程序大小决定'),('Debug构建的用途之一是什么？','保留调试符号','消除全部缺陷','改变单位','绕过权限')],['cpp'])
L(5,2,'先用测试证明问题','把正确的单位关系写成可重复检查的断言。',
'一圈是2π弧度，一分钟是60秒，所以rpm=rad/s×60/(2π)。测试应该来自这个独立关系，不能直接复制错误实现。课程测试覆盖0、10和-10，既检查零值，也检查正反方向。浮点数比较使用容差，不能要求任意计算都逐位完全相等。',
'阅读tests/test_units.cpp，确认预期值约为0、95.492966和-95.492966。运行CTest，把标准输出和错误保存到sensor/results/test-before.log。当前错误版本应失败，失败不是本课需要掩盖的问题，反而是成功复现缺陷的证据。',
'不要通过删除失败测试来让界面变绿，也不要把预期值改成错误输出600。缺陷修复应同时通过原来的测试。此课验收会重新运行测试，确认失败真实存在；只写一行“test failed”不能替代可执行证据。',
[('cat sensor/tests/test_units.cpp','根据单位换算核对测试预期。','覆盖0、10、-10。'),('mkdir -p sensor/results\nctest --test-dir sensor/build --output-on-failure > sensor/results/test-before.log 2>&1\necho $?','真实运行错误版本测试并记录退出状态。','退出非0。'),('cat sensor/results/test-before.log','读失败原因和预期/实际值。','测试报告指出数值不匹配。')],
'保存真实失败测试，证明单位换算缺陷。','mkdir -p sensor/results\nctest --test-dir sensor/build --output-on-failure > sensor/results/test-before.log 2>&1\ncat sensor/results/test-before.log',
[('测试预期应来自哪里？','独立的单位或物理关系','错误程序当前输出','随机值','文件名'),('本课测试失败说明什么？','成功复现了已知缺陷','应删除测试','Linux坏了','必须重装编译器')],['cpp'])
L(5,3,'用 GDB 观察一次计算','设置断点并核对函数输入与实际输出。',
'调试器允许程序在指定位置停下，检查变量和调用栈。断点不是修改程序的逻辑，而是让你观察执行过程。这里把断点放在rad_s_to_rpm函数，确认输入是否真为10，再检查当前公式。先检查数据进入函数之前是否正确，可避免把上游问题误判为计算公式问题。',
'使用GDB批处理运行已编译的Debug程序，设置函数断点，运行参数10，打印x，然后继续执行。把输出保存到gdb.txt。程序应在换算函数中停下，x=10，继续后输出600。结合单位公式，在diagnosis.md记录缺少除以2*pi。',
'如果GDB提示ptrace不允许，应报告实验环境异常，不能生成一份假日志。只调试本实验自己启动的进程，不应扩大到宿主进程。优化可能内联函数或移除变量，因此初学调试使用Debug构建。证据中应同时保留输入、位置和错误输出。',
[('gdb -q -batch -ex "break rad_s_to_rpm" -ex "run 10" -ex "print x" -ex continue --args sensor/build/sensor_tool 10 > sensor/results/gdb.txt 2>&1','在函数断点观察输入，然后继续。','断点、x=10、输出600。'),('cat sensor/results/gdb.txt','核对真实调试证据。','无ptrace环境错误。'),("mkdir -p sensor/notes\nprintf 'rad/s 转 rpm 缺少除以 2*pi；输入10导致输出600。\\n' > sensor/notes/diagnosis.md",'记录原因与单位关系。','说明具体缺陷。')],
'提交GDB观察记录与单位错误诊断。','gdb -q -batch -ex "break rad_s_to_rpm" -ex "run 10" -ex "print x" -ex continue --args sensor/build/sensor_tool 10 > sensor/results/gdb.txt 2>&1\nmkdir -p sensor/notes\nprintf "rad/s 转 rpm 缺少 2*pi。\\n" > sensor/notes/diagnosis.md',
[('断点的用途是什么？','暂停并观察程序状态','删除错误输入','改变电机参数','自动修复代码'),('ptrace被禁止应怎样处理？','报告环境限制并修复环境','伪造调试日志','删除全部测试','关闭宿主所有防护')],['cpp'])
L(5,4,'修复、复测并提交','用同一套测试证明修复，并保留可审阅差异。',
'修复应尽可能小并能解释原因。把函数改为x×60/(2π)，不要同时重写整个工程。Git diff展示未提交变化，有助于确认只改了预期内容。可审阅的提交说明包含问题和修复方式，优于“update”这类无法说明意图的文字。',
'编辑units.hpp后重新编译，运行CTest，将结果保存为test-after.log。再手动检查0、10、-10的输出。查看sensor仓库差异，把函数和诊断说明提交；编译目录和日志由.gitignore规则处理，避免大量生成文件淹没真正修复。',
'测试通过是证据之一，但不能证明所有输入都正确。本课范围是有限数字的单位换算；复杂设备还需要边界、接口与系统级验证。交付时保留修改前后的证据，说明你如何定位而不是只展示最终绿色结果。',
[("sed -i 's/return x \\* 60.0;/return x * 60.0 \\/ (2.0 * 3.141592653589793);/' sensor/include/units.hpp",'将弧度转换成圈数；也可用nano手动修改。','公式含2π。'),('cmake --build sensor/build -j1\nctest --test-dir sensor/build --output-on-failure > sensor/results/test-after.log 2>&1\ncat sensor/results/test-after.log','重新构建并复测同一测试。','全部通过。'),('git -C sensor diff\ngit -C sensor add include/units.hpp notes/diagnosis.md\ngit -C sensor commit -m "Fix rad/s to rpm conversion"','记录最小修复及原因。','提交包含代码和说明。')],
'交付经复测的修复提交及前后证据。',"sed -i 's/return x \\* 60.0;/return x * 60.0 \\/ (2.0 * 3.141592653589793);/' sensor/include/units.hpp\ncmake --build sensor/build -j1\nctest --test-dir sensor/build --output-on-failure > sensor/results/test-after.log 2>&1\ngit -C sensor add include/units.hpp notes/diagnosis.md\ngit -C sensor commit -m 'Fix rad/s to rpm conversion'",
[('修改源码后为何重新构建？','二进制不会自动随源码变化','为了改变目录','因为Git要求','为了清空测试'),('好的修复提交应包含什么？','具体代码变化及原因','只有截图','只有一行update','所有缓存文件')],['cpp'])
L(6,1,'安装专业机电仿真工具','使用OpenModelica运行独立的机电组件模型。',
'OpenModelica使用Modelica描述方程与组件连接，适合电气和机械耦合系统。omc是命令行编译器，OMEdit是图形编辑器；本课先安装无图形版本，减少环境负担。编译器和Modelica标准库是两项不同依赖，只有omc --version成功还不能证明模型可以加载。',
'先在本机按软件准备页运行prepare-labs.sh --modelica，下载本周专用包缓存，然后启动第6周。容器内从课堂仓库安装omc和omlibrary，加载已缓存标准库4.0.0，再编译提供的Motor.mo。电阻、电感、机电耦合、惯量和阻尼组成独立的开环模型。',
'软件包准备可能占用较多磁盘，先检查空间，不要同时安装全部专业工具。加载失败时分别检查编译器、标准库版本和模型路径。课堂不把未运行的模型显示为验证通过。图形拖拽建模可在后续OMEdit中练习，本课重点是从Linux命令行得到可检查的物理结果。',
[('sudo apt-get update\nsudo apt-get install -y omc omlibrary\nomc --version | tee results/omc-version.txt','只在第6周管理员容器安装已准备的包。','omc报告真实版本。'),('omc scripts/prepare_modelica.mos','将本地缓存中的Modelica库准备好。','loadModel返回true。'),('labtool modelica','编译组件模型并标准化导出CSV。','results/modelica.csv来自真实omc运行。')],
'完成omc与标准库安装并运行独立电机模型。','sudo apt-get update\nsudo apt-get install -y omc omlibrary\nomc --version > results/omc-version.txt\nomc scripts/prepare_modelica.mos\nlabtool modelica',
[('omc和OMEdit的关系是什么？','分别是编译器与图形编辑器','两个电机参数','两种电流单位','两台服务器'),('版本命令成功是否足够验证模型？','不够，还要加载库并运行模型','足够验证全部物理结果','只需要截图','不需要模型文件')],['openmodelica'])
L(6,2,'让两套模型互相校验','对齐参数、初值、激励和时间轴后比较结果。',
'两个工具画出的曲线接近，可以帮助发现实现错误，但不能替代实机验证。对照前必须一致：电机参数、初始电流与转速、输入12V、无负载、仿真5秒。若一边使用rpm而另一边使用rad/s，直接比较数字会得出错误结论。',
'运行Python开环得到openloop.csv，再运行OpenModelica组件模型得到modelica.csv。labtool compare在公共时间轴插值比较电流和转速，记录最大绝对误差、模型参数与版本。课程容差用于该教学基准，不声称是工业认证标准。',
'切换点和零值附近应谨慎使用相对误差，所以本课对照使用明确单位的最大绝对误差。若误差过大，先检查工况与单位，再检查符号、初值和求解容差。先独立确认稳态解析解，避免两个模型共享同一错误仍看起来一致。',
[('labtool simulate --voltage 12 --output results/openloop.csv\nlabtool modelica','用一致工况生成两份真实结果。','两份CSV可读且数据有限。'),('labtool compare','重新计算对照误差。','results/comparison.json记录通过或未通过。'),('cat results/comparison.json','阅读数值与版本证据。','含两模型来源与误差。')],
'提交两套模型的实际对照结果与误差记录。','labtool simulate --voltage 12 --output results/openloop.csv\nlabtool modelica\nlabtool compare',
[('对照前必须先统一什么？','参数、初值、激励、单位与时间','图表颜色','电脑品牌','文件图标'),('两模型一致是否等于实机验证？','不等于，只是数值交叉验证','完全等于','只要截图就等于','由文件大小决定')],['python','openmodelica'])
L(6,3,'调试虚拟电机速度闭环','观察PI、负载扰动与电压饱和。',
'闭环比较目标与反馈，用误差调整输入。P项提供即时纠偏，I项积累误差以消除持续偏差；增益不是越大越好。这里误差使用rad/s，界面显示rpm，Kp单位是V/(rad/s)，Ki单位是V/rad。电压限制为±24V，积分抗饱和避免控制器在不可达指令下持续积累。',
'目标设为900rpm，kp=0.08、ki=0.6，仿真5秒，在2.5秒加入0.03N·m负载。先运行基准，观察速度短暂下降后恢复，再在网页改变Kp或关闭积分项比较。每次只改一个因素，记录与基准相比的差异。电流是模型积分结果，不会被直接裁剪冒充电流保护。',
'默认参考解稳态误差小于1%、超调小于10%、负载后可恢复，但这些指标只针对教学工况。若反馈有偏差，测量曲线可能跟踪目标，而真实转速没有达到目标，因此应同时观察两条曲线。验收检查物理真实速度、输入限幅和场景参数，不只检查界面“达标”。',
[('labtool closed-loop --kp 0.08 --ki 0.6 --output results/closedloop.csv','运行固定基准闭环与负载扰动。','CSV和control-metrics.json生成。'),('cat results/control-metrics.json','查看稳态误差、超调和电流。','指标来自本次数值计算。'),('tail -n 4 results/closedloop.csv','观察扰动后最终真实转速。','接近900rpm。')],
'交付可复现的PI闭环结果和性能指标。','labtool closed-loop --kp 0.08 --ki 0.6 --output results/closedloop.csv',
[('积分抗饱和主要处理什么？','执行输入受限时积分持续积累','CSV行数过多','软件包下载','SSH密钥长度'),('传感器偏差时应同时观察什么？','真实模型速度与测量反馈','只看目标值','只看文件名','只看最后一个命令')],['python'])
L(6,4,'定位故障并交付工程作品','用故障与修复的对照结果说明自己的判断。',
'虚拟调试让你在没有硬件时检查控制逻辑、单位、参数和故障恢复。课程提供反馈反接、rpm误当rad/s、传感器+120rpm偏差。它们修改测量链，不直接修改电机物理状态。由曲线推断问题只是起点，还应通过修复后复测建立证据链。',
'先在网页选择不同故障观察真实速度和反馈。再用labtool diagnose --fault units生成故障与正常对照，查看两种场景的稳态误差。运行labtool report打包参数、CSV、诊断与README，在报告中补上学生姓名、英文摘要、定位过程及局限。课程作者和学生作者应分开记录。',
'请同伴按README重新运行，而不是只看你的截图。作品包括输入、版本、运行步骤、原始结果、检查与解释；没有实际硬件就不宣称验证了驱动器实时性或安全功能。结业目标是可靠地使用Linux完成小型工程任务，并为下一阶段专业项目打好基础。',
[('labtool diagnose --fault units\ncat results/diagnosis.json','计算同一模型在单位故障与修复后的差异。','诊断有两套实际指标。'),('labtool report','生成作品草稿与归档。','reports/report.md和manifest.json。'),('nano reports/report.md\nlabtool report --archive-only','补学生作者、英文摘要与分析后重新归档。','motor-project.tar.gz包含个人说明。')],
'提交可复现的故障诊断作品包，并完成个人复盘。','labtool diagnose --fault units\nlabtool report\n# 编辑 reports/report.md 填学生姓名与英文摘要\nlabtool report --archive-only',
[('虚拟调试能直接证明哪项能力？','模型范围内的逻辑、单位与控制验证','真实驱动器全部安全性','电机实际温升','实机总线实时性'),('同伴复现最需要什么？','输入、版本、命令和原始结果','只有一张曲线截图','只有课程作者名','只有最终分数')],['python','openmodelica'])
tracks=[dict(id='robotics',title='机器人与控制',weeks='07–12',summary='从单个旋转关节出发，逐步控制一台仿真差速机器人。',softwareIds=['ros2'],skills=['ROS 2','Gazebo','ros2_control','日志与测试'],projects=[dict(weeks='7–8',title='单关节虚拟执行器',deliverable='建立关节模型、启动控制器并记录输入输出；区分接口mock与物理仿真。'),dict(weeks='9–10',title='差速机器人任务',deliverable='完成规定路线、记录误差与扰动；提供启动文件和参数。'),dict(weeks='11–12',title='恢复与工程交付',deliverable='注入配置/通信故障，记录诊断、复测和英文演示。')]),dict(id='cae',title='CAE 与仿真计算',weeks='07–12',summary='围绕电机支架和冷却管路建立从模型到验证的工作流。',softwareIds=['freecad','openfoam'],skills=['参数化建模','网格与求解','批量计算','物理验证'],projects=[dict(weeks='7–8',title='支架线性静力分析',deliverable='FreeCAD建模、Gmsh网格、CalculiX求解，与简化梁理论比较。'),dict(weeks='9–10',title='冷却管道流动',deliverable='小网格层流算例，验证压降、质量守恒和网格敏感性。'),dict(weeks='11–12',title='参数扫描发布包',deliverable='脚本管理输入、求解日志和后处理，按README复现。')]),dict(id='industrial',title='工业设备与自动化软件',weeks='07–12',summary='让虚拟电机具备设备通信、状态上报与故障恢复能力。',softwareIds=['industrial','linuxcnc'],skills=['MQTT','Modbus TCP','服务与日志','故障恢复'],projects=[dict(weeks='7–8',title='虚拟设备接口',deliverable='将控制寄存器与电机模型连接，记录单位、字节序及采样周期。'),dict(weeks='9–10',title='通信与告警测试',deliverable='注入超时、断连、非法指令，验证状态转换与恢复。'),dict(weeks='11–12',title='部署与诊断交付',deliverable='形成版本固定、带测试和运行说明的设备软件项目。')])]
sources=[dict(title='博世力士乐 · 控制软件研发岗位',url='https://jobs.smartrecruiters.com/BoschGroup/744000140192621-software-development-engineer-dccs',note='2026-09-12核验：中国招聘主体，要求Linux/C++及控制背景，ROS等为加分；未明确校招。'),dict(title='ASML · 设备软件工程岗位',url='https://www.asml.com/en/careers/find-your-job/de-rd-embeded-software-engineer-metrology-scanner-sw-j00347049',note='2026-09-12核验：韩国、5年以上经验，作为系统排障成长方向，不作为研一入门门槛。'),dict(title='达索 · CFD软件研发岗位',url='https://www.3ds.com/de/careers/jobs/cfd-software-engineer-c-cuda-f-m-547778',note='2026-09-12核验：西班牙，有经验岗位；Linux、科学计算和HPC为相关能力。正文与经验标签有差异。')]
(ROOT/'course').mkdir(exist_ok=True)
(ROOT/'course/curriculum.json').write_text(json.dumps(dict(version='1.0',authors=['Connor He','Astra'],weeks=[dict(id=i+1,title=w[0],subtitle=w[1],project=w[2],outcome=w[2]) for i,w in enumerate(W)],lessons=lessons,tracks=tracks,sources=sources),ensure_ascii=False,indent=2))
print('Saved',len(lessons),'lessons')
