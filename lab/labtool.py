#!/usr/bin/env python3
"""Small reproducible CLI used inside course containers."""
import argparse,csv,json,math,subprocess,sys,tarfile,hashlib,shutil,os
from pathlib import Path
from motor import simulate,analytic_steady_state
ROOT=Path.cwd()
FIELDS={'t':'time_s','voltage':'voltage_V','current':'current_A','rpm':'speed_rpm','load':'load_Nm','target_rpm':'target_rpm','measured_rpm':'measured_rpm'}
def save_sim(config,output):
 r=simulate(config);path=Path(output);path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(FIELDS.values()));w.writeheader();w.writerows({v:p[k] for k,v in FIELDS.items()} for p in r['series'])
 path.with_suffix('.json').write_text(json.dumps({k:v for k,v in r.items() if k!='series'},ensure_ascii=False,indent=2))
 print('simulation_complete',path)
 return r

def modelica():
 if not shutil.which('omc'):raise RuntimeError('omc未安装。请先按第6周安装指南准备环境。')
 if not Path('models/Motor.mo').exists():raise RuntimeError('缺少models/Motor.mo。')
 # Each output directory is private to the current project. No arbitrary host calls.
 Path('results').mkdir(exist_ok=True)
 script='''loadModel(Modelica, {"4.0.0"});
loadFile("models/Motor.mo");
simulate(Motor, stopTime=5, numberOfIntervals=1000, tolerance=1e-8, outputFormat="csv", fileNamePrefix="results/modelica_raw", simflags="-override=loadNm=0");
getErrorString();
'''
 Path('results/run.mos').write_text(script)
 proc=subprocess.run(['omc','results/run.mos'],capture_output=True,text=True,timeout=120)
 Path('results/modelica.log').write_text(proc.stdout+proc.stderr)
 raw=Path('results/modelica_raw_res.csv')
 if proc.returncode or not raw.exists():raise RuntimeError('OpenModelica未生成结果。请查看results/modelica.log。')
 rows=list(csv.DictReader(raw.open()))
 with Path('results/modelica.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(FIELDS.values()));w.writeheader()
  for r in rows:w.writerow({'time_s':r['time'],'voltage_V':r['applied_voltage'],'current_A':r['current'],'speed_rpm':r['rpm'],'load_Nm':r['load'],'target_rpm':0,'measured_rpm':r['rpm']})
 version=subprocess.check_output(['omc','--version'],text=True).strip()
 Path('results/modelica-version.json').write_text(json.dumps({'omc':version,'library':'4.0.0','voltage':12,'load_Nm':0,'duration':5}))
 print('modelica_complete',version)

def compare():
 a=list(csv.DictReader(Path('results/openloop.csv').open()));b=list(csv.DictReader(Path('results/modelica.csv').open()))
 if len(a)<10 or len(b)<10:raise RuntimeError('结果行数不足。')
 # Keep last value at duplicate event times; linearly interpolate independent grids.
 bb={float(r['time_s']):r for r in b};times=sorted(bb);index=0;maxw=maxi=0
 for r in a:
  t=float(r['time_s'])
  if t<times[0]-1e-8 or t>times[-1]+1e-8:raise RuntimeError('两模型时间范围不一致。')
  while index+1<len(times) and times[index+1]<t:index+=1
  lo=times[index];hi=times[min(index+1,len(times)-1)];f=0 if hi==lo else (t-lo)/(hi-lo)
  for key in ('speed_rpm','current_A'):
   value=float(bb[lo][key])*(1-f)+float(bb[hi][key])*f
   error=abs(float(r[key])-value)
   if not math.isfinite(error):raise RuntimeError('结果含非有限数值。')
   if key=='speed_rpm':maxw=max(maxw,error)
   else:maxi=max(maxi,error)
 passed=maxw<1 and maxi<.02
 out={'passed':passed,'max_speed_error_rpm':maxw,'max_current_error_A':maxi,'tolerance':{'rpm':1,'A':.02},'python':sys.version.split()[0],'modelica':json.loads(Path('results/modelica-version.json').read_text()),'model_parameters':json.loads(Path('config/motor.json').read_text())}
 Path('results/comparison.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False));return out

def diagnose(fault):
 bad=save_sim({'fault':fault},'results/fault.csv');good=save_sim({'fault':'none'},'results/fixed.csv')
 out={'fault':fault,'fault_metrics':bad['metrics'],'fixed_metrics':good['metrics'],'passed':bad['metrics']['steady_error_pct']>5 and good['metrics']['steady_error_pct']<1}
 Path('results/diagnosis.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))

def report(archive_only=False):
 folder=Path('reports');folder.mkdir(exist_ok=True)
 if not archive_only:
  if not (folder/'report.md').exists():(folder/'report.md').write_text('# 虚拟电机调试作品\n\n学生作者：待填写\n\n课程作者：Connor He 和 Astra\n\n## English abstract\nPlease describe your own experiment, diagnosis, evidence and limitations.\n\n## 现象与分析\n请填写定位过程和复测结果。\n\n## Reproduce\nlabtool closed-loop --kp 0.08 --ki 0.6 --output results/closedloop.csv\nlabtool diagnose --fault units\n\n## 局限\n教学参数，无硬件辨识；不含PWM、真实驱动器和实时性验证。\n')
 files=[]
 for directory in ('config','results','notes','reports'):
  files += [p for p in Path(directory).rglob('*') if p.is_file() and not p.is_symlink() and p.suffix not in ('.gz',) and p.name!='manifest.json' and p.stat().st_size<5_000_000]
 manifest={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
 (folder/'manifest.json').write_text(json.dumps({'course_authors':['Connor He','Astra'],'files':manifest},ensure_ascii=False,indent=2))
 with tarfile.open(folder/'motor-project.tar.gz','w:gz') as t:
  for p in files+[folder/'manifest.json']:t.add(p,arcname=str(p),recursive=False)
 print('report_complete reports/motor-project.tar.gz')

def main():
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='action',required=True)
 s=sub.add_parser('simulate');s.add_argument('--voltage',type=float,default=12);s.add_argument('--output',default='results/openloop.csv')
 s=sub.add_parser('batch');s.add_argument('--output',default='results/batch.csv')
 s=sub.add_parser('closed-loop');s.add_argument('--kp',type=float,default=.08);s.add_argument('--ki',type=float,default=.6);s.add_argument('--output',default='results/closedloop.csv')
 s=sub.add_parser('diagnose');s.add_argument('--fault',choices=['units','bias','reversed'],default='units')
 s=sub.add_parser('report');s.add_argument('--archive-only',action='store_true')
 sub.add_parser('compare');sub.add_parser('modelica');args=p.parse_args()
 if args.action=='simulate':save_sim({'mode':'open','voltage':args.voltage,'load_Nm':0},args.output)
 elif args.action=='closed-loop':
  r=save_sim({'kp':args.kp,'ki':args.ki},args.output);Path('results/control-metrics.json').write_text(json.dumps({'config':r['config'],'metrics':r['metrics']},indent=2))
 elif args.action=='batch':
  path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
  with path.open('w') as f:
   w=csv.writer(f);w.writerow(['voltage_V','final_speed_rpm'])
   for v in [6,9,12]:w.writerow([v,simulate({'mode':'open','voltage':v,'load_Nm':0})['metrics']['final_rpm']])
  print('batch_complete',path)
 elif args.action=='modelica':modelica()
 elif args.action=='compare':
  if not compare()['passed']:return 1
 elif args.action=='diagnose':diagnose(args.fault)
 elif args.action=='report':report(args.archive_only)
 return 0
if __name__=='__main__':
 try:sys.exit(main())
 except (RuntimeError,FileNotFoundError,ValueError,subprocess.SubprocessError) as e: print(str(e),file=sys.stderr);sys.exit(1)
