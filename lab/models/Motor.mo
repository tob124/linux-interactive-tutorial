model Motor
  "Independent open-loop component model; teaching parameters, not identified hardware"
  parameter Modelica.Units.SI.Voltage voltage = 12;
  parameter Modelica.Units.SI.Torque loadNm = 0.03
    "Positive value is an external torque in the negative shaft direction";
  parameter Modelica.Units.SI.Time loadTime = 2.5;

  Modelica.Blocks.Sources.Constant voltageCommand(k=voltage);
  Modelica.Electrical.Analog.Sources.SignalVoltage source;
  Modelica.Electrical.Analog.Basic.Ground ground;
  Modelica.Electrical.Analog.Basic.Resistor resistor(R=2);
  Modelica.Electrical.Analog.Basic.Inductor inductor(
    L=0.002, i(start=0, fixed=true));
  Modelica.Electrical.Analog.Basic.RotationalEMF emf(k=0.05);
  Modelica.Mechanics.Rotational.Components.Inertia rotor(
    J=0.0002, phi(start=0, fixed=true), w(start=0, fixed=true));
  Modelica.Mechanics.Rotational.Components.Damper damper(d=0.0001);
  Modelica.Mechanics.Rotational.Components.Fixed fixed;
  Modelica.Mechanics.Rotational.Sources.Torque externalLoad(useSupport=false);
  Modelica.Blocks.Sources.Step loadCommand(
    height=-loadNm, offset=0, startTime=loadTime);

  output Real rpm(unit="1/min") = rotor.w * 60 / (2 * Modelica.Constants.pi);
  output Modelica.Units.SI.Current current = resistor.i;
  output Modelica.Units.SI.Voltage applied_voltage = source.v;
  output Modelica.Units.SI.Torque electromagnetic_torque = 0.05 * resistor.i;
  output Modelica.Units.SI.Torque load = -loadCommand.y;

equation
  connect(voltageCommand.y, source.v);
  connect(source.p, resistor.p);
  connect(resistor.n, inductor.p);
  connect(inductor.n, emf.p);
  connect(emf.n, ground.p);
  connect(source.n, ground.p);
  connect(emf.flange, rotor.flange_a);
  connect(rotor.flange_b, damper.flange_a);
  connect(damper.flange_b, fixed.flange);
  connect(externalLoad.flange, rotor.flange_b);
  connect(loadCommand.y, externalLoad.tau);

  annotation(
    uses(Modelica(version="4.0.0")),
    experiment(StartTime=0, StopTime=5, Interval=0.005, Tolerance=1e-8),
    Documentation(info="<html><p>This averaged permanent-magnet DC motor is an
    independent acausal component counterpart to the Python open-loop plant.
    R=2 ohm, L=0.002 H, J=0.0002 kg.m2, b=0.0001 N.m.s/rad,
    Kt=Ke=0.05 in SI. It excludes PWM, thermal effects, current control,
    Coulomb friction, encoder quantization and real-time hardware.</p>
    <p>Positive loadNm applies negative torque. It is an external disturbance,
    not a brake that always opposes the shaft direction. Use voltage=12,
    loadNm=0.03, loadTime=2.5 to match the Python open-loop defaults.
    Initial inductor current, angle and speed are zero.</p></html>"));
end Motor;
