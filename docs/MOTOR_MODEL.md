# 虚拟直流电机数值资产

课程作者：Connor He 和 Astra。

server/motor.py 使用 Python 标准库实时计算每次请求的轨迹，
不包含预先存好的曲线。lab/models/Motor.mo 是独立的 Modelica 标准库组件模型。

## 运行

在项目根目录执行：

    python3 -m unittest discover -s tests -p test_motor.py -v
    python3 -m server.motor '{"mode":"closed"}'
    python3 -m server.motor '{"mode":"open","voltage":12}'

作为模块：

    from server.motor import simulate, validate_config, crosscheck
    result = simulate({"mode": "closed", "fault": "bias"})
    config = validate_config({"target_rpm": 900, "anti_windup": True})
    reference = crosscheck({"mode": "open"}, backend="scipy")

无需 NumPy、SciPy 或 python-control 即可完成基础仿真和所有必需测试。
可选 crosscheck 只验证开环植物，支持 auto、scipy、control；
没有相应依赖会如实返回 available: false，不会尝试自行安装。

## 单位与运行约定

- 物理状态为电流 A 与角速度 rad/s，初值都是零。
- PI 使用 rad/s 误差；kp 单位为 V/(rad/s)，ki 单位为 V/rad。
- PI 周期固定 1 ms、输出电压零阶保持；基础 RK4 子步 0.1 ms。
- dt 可在 0.025–0.1 ms 内改变，只影响植物积分，不能改控制周期。
- 负载跳变在积分中精确分段；load_Nm 正数表示沿负方向施加外转矩，
  不表示无论转向如何始终阻碍旋转的摩擦制动器。
- 输出每 5 ms 一行，额外保留不落在网格上的精确终止时刻；peak_current
  从所有 RK4 子步统计，不受输出抽样影响。
- 电压限定 ±24 V。电流是积分结果，没有电流裁剪、限流或保护模型。
- 只允许已登记字段。数字必须有限、不能是字符串或布尔值；时长 <=10 s。

## 故障语义

none：正常反馈。units：把传感器给出的 rpm 数字误当成 rad/s。
reversed：测量角速度取反。bias：速度反馈固定增加 120 rpm。
三种故障仅修改反馈；开环不使用反馈，因此其物理轨迹与正常开环完全相同。

measured_rpm 表示“控制器理解的反馈”再换算成 rpm，不是物理真实转速。
rpm 一直来自物理状态。两条曲线应同时展示，避免把反馈看似达标当作设备达标。

## 指标语义

- 闭环参照 target_rpm；开环参照给定电压和末段负载的解析平衡转速，
  见 model.reference_rpm。开环的 target_rpm 不参与控制。
- steady_error_pct：最后至多 0.25 s 物理速度均值的绝对相对误差。
  它不保证实验真的进入稳态；短时间/末端扰动会提供警告。参照为零时返回 null。
- overshoot_pct：全程在参照方向的最大速度超过参照的比例。
  含负载突变的开环结果会把突变前较高速度计入此项，不能只据此判断控制品质。
- settling_time：从最后一次已应用的负载阶跃起算（没有阶跃则从 0 起算），
  此后一直进入 ±2% 或至少 ±1 rpm 误差带的时间；尾部至少要保持 0.1 s，
  否则返回 null。
- peak_current：全程电流绝对值峰值，A。
- saturation_pct：电压恰位于任一电源限制的仿真时长比例。

## OpenModelica 对照

安装 OpenModelica 与 Modelica Standard Library 4.0.0 后，在 lab/models 目录执行独立带负载算例：

    omc run.mos

默认生成 Motor_open_res.csv，对照 simulate({"mode":"open"})。
课堂第 6 周另使用 `labtool modelica` 运行无负载工况，与 `labtool simulate` 对照，结果在项目 results 目录。不要混用两种工况。
Modelica 参数 voltage / loadNm / loadTime 分别对应 Python
voltage / load_Nm / load_time。输出 rpm、current、
applied_voltage、electromagnetic_torque、load。

Modelica CSV 可能包含事件前后重复时刻，比较物理状态时先统一输出时刻；
电压和负载按右连续输入解释。状态在理想负载阶跃时保持连续。

本次只完成 Python 实际测试。当前环境未找到 omc、SciPy 或 python-control；
不应将这些对照资产说成已通过第三方求解器或 OpenModelica 验证。

## 教学边界

参数为公开教学设定，未经实际电机辨识。未模拟 PWM 开关、热效应、磁饱和、
库仑摩擦、编码器量化、实际电流环、真实驱动器、时间抖动或工业实时总线。
此资产支持软件模型上的闭环与故障学习，不能代替硬件验证或功能安全验证。
