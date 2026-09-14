"""State-based learning checks. Not an anti-cheating or certification system."""
import contextlib,csv,hashlib,io,json,math,os,re,shutil,stat,subprocess,sys,tarfile
from pathlib import Path
from motor import simulate,analytic_steady_state
from seed import DATA
ROOT=Path(os.environ.get('COURSE_WORKSPACE','/workspace'))
def require(ok,message):
 if not ok:raise AssertionError(message)
def text(path):return (ROOT/path).read_text()
def has(path,*words):
 value=text(path);require(all(w in value for w in words),f'{path} 缺少必要内容：'+', '.join(words))
def run(*args,cwd=None,timeout=20):
 return subprocess.run(args,cwd=cwd or ROOT,capture_output=True,text=True,timeout=timeout)
def rows(path):return list(csv.DictReader((ROOT/path).open()))
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def physical(path,closed=False):
 data=rows(path);require(len(data)>=100,'结果行数不足，请真实运行完整仿真。')
 fields=['time_s','voltage_V','current_A','speed_rpm','load_Nm']
 nums=[{k:float(r[k]) for k in fields} for r in data]
 require(all(math.isfinite(x) for r in nums for x in r.values()),'数据含非有限数值。')
 times=[r['time_s'] for r in nums]
 require(times[0]==0 and 4.99<=times[-1]<=5.01,'仿真应从0秒运行到5秒。')
 require(all(b>=a for a,b in zip(times,times[1:])),'时间戳必须有序。')
 require(abs(nums[0]['current_A'])<1e-7 and abs(nums[0]['speed_rpm'])<1e-7,'初始电流与速度应为零。')
 require(max(abs(r['voltage_V']) for r in nums)<=24.00001,'电压超过±24V限制。')
 if closed:
  require(any(abs(r['load_Nm']-.03)<1e-8 and r['time_s']>=2.5 for r in nums),'缺少指定负载阶跃。')
  tail=[r['speed_rpm'] for r in nums if r['time_s']>=4.5]
  require(abs(sum(tail)/len(tail)-900)/900<.01,'负载后的真实速度稳态误差应小于1%。')
 else:
  require(all(abs(r['voltage_V']-12)<1e-5 for r in nums),'开环电压必须为12V。')
  require(all(abs(r['load_Nm'])<1e-8 for r in nums),'本对照算例应无负载。')
  steady=analytic_steady_state(12)
  require(abs(nums[-1]['speed_rpm']-steady['rpm'])/steady['rpm']<.01,'最终转速未满足该模型解析稳态。')
  require(abs(nums[-1]['current_A']-steady['current'])<.01,'最终电流未满足解析稳态。')
 return nums

def remote(*args):
 p=run('ssh','-o','BatchMode=yes','-o','ConnectTimeout=5','student@workstation',*args)
 require(p.returncode==0,'远程操作失败：请检查连接、认证与路径。'+p.stderr[-200:]);return p.stdout

def batch():
 data=rows('results/batch.csv');d={float(r['voltage_V']):float(r['final_speed_rpm']) for r in data}
 for v in [6,9,12]:
  require(v in d and math.isfinite(d[v]),'batch.csv缺少6/9/12V有效结果。')
  require(abs(d[v]-analytic_steady_state(v)['rpm'])<2,'批量稳态转速不符合模型。')

def check(key):
 if key=='w1-1':has('notes/linux.txt','Linux','Shell','/workspace')
 elif key=='w1-2':
  require(all((ROOT/'experiments/motor-01'/p).is_dir() for p in ['raw','processed','reports']),'三个实验目录不完整。')
  require(text('experiments/motor-01/raw/motor.csv')==DATA,'原始副本被修改。')
 elif key=='w1-3':has('notes/experiment.md','motor-01','12 V','rpm','原始数据')
 elif key=='w1-4':
  p=ROOT/'scripts/hello.sh';mode=p.stat().st_mode
  require(p.stat().st_uid==os.getuid() and mode&stat.S_IXUSR and not mode&(stat.S_IWGRP|stat.S_IWOTH),'脚本所有者或执行/写权限不正确。')
  result=run(str(p));require(result.returncode==0 and result.stdout.strip()=='motor-lab-ready','脚本实际输出不正确。')
  result=run('dpkg-query','-W','-f=${Status}','tree');require(result.returncode==0 and 'install ok installed' in result.stdout,'tree尚未安装。')
 elif key=='w2-1':
  require(text('data/raw/motor.csv')==DATA,'原始副本不一致。');has('notes/data-dictionary.md','time_s','voltage_V','current_A','speed_rpm','load_Nm','缺失')
 elif key=='w2-2':
  data=rows('results/high-current.csv')
  expected=[r for r in csv.DictReader(DATA.splitlines()) if r['current_A'] and float(r['current_A'])>2]
  require(data==expected,'高电流结果应保留0.1、0.2、0.4秒三条的完整原始记录。');require(text('data/motor.csv')==DATA,'原始文件被修改。')
 elif key=='w2-3':
  data=rows('results/clean.csv');require(len(data)==10 and all(r['current_A']!='' for r in data),'清洗后应有10条有效记录。')
  expected=[r for r in csv.DictReader(DATA.splitlines()) if r['current_A']!=''];require(data==expected,'清洗改变了其它有效数据。');has('results/quality.txt','valid_rows=10','missing_rows=1')
 elif key=='w2-4':
  result=run('git','ls-tree','-r','--name-only','HEAD');require(result.returncode==0,'还没有Git提交。')
  require(all(p in result.stdout.splitlines() for p in ['README.md','notes/data-dictionary.md','.gitignore']),'提交缺少说明、数据字典或忽略文件。');has('.gitignore','.venv/','results/','build/')
 elif key=='w3-1':
  result=run(str(ROOT/'.venv/bin/python'),'-c','import sys,numpy,scipy,matplotlib,control; print(sys.prefix)');require(result.returncode==0 and str(ROOT/'.venv') in result.stdout,'科学计算虚拟环境未就绪。');has('results/environment.txt','numpy','scipy','matplotlib','control')
 elif key=='w3-2':physical('results/openloop.csv')
 elif key=='w3-3':batch()
 elif key=='w3-4':
  has('scripts/run_batch.sh','set -euo pipefail');p=run(str(ROOT/'scripts/run_batch.sh'));require(p.returncode==0,'批处理脚本实际运行失败。');batch();has('logs/batch.log','batch_complete');require(int(text('logs/batch.pid').strip())>0,'PID记录无效。')
 elif key=='w4-1':
  private=Path.home()/'.ssh/id_ed25519';require(stat.S_IMODE(private.stat().st_mode)==0o600,'练习私钥权限应为600。');require((Path.home()/'.ssh/id_ed25519.pub').read_text().startswith('ssh-ed25519 '),'公钥格式不符。');require(remote('hostname').strip()=='workstation','远程主机名不符。')
 elif key=='w4-2':
  output=remote('sha256sum','jobs/motor/config/motor.json');h=digest(ROOT/'config/motor.json');require(output.split()[0]==h,'远程参数与本地不同。');has('results/remote-config.sha256',h)
 elif key in ('w4-3','w4-4'):
  remote('tmux','has-session','-t','motor');output=remote('sha256sum','jobs/motor/results/openloop.csv');h=digest(ROOT/'results/remote-openloop.csv');require(output.split()[0]==h,'取回文件与远程不一致。');physical('results/remote-openloop.csv')
  if key=='w4-4':has('notes/remote-run.md','hostname=workstation','exit_code=0','sha256='+h,'连接','认证','路径')
 elif key=='w5-1':
  p=run(str(ROOT/'sensor/build/sensor_tool'),'10');require(p.returncode==0 and abs(float(p.stdout)-600)<1e-6,'本课先保留错误版本，输入10应观察到600。')
 elif key=='w5-2':
  p=run('ctest','--test-dir','sensor/build','--output-on-failure');require(p.returncode!=0 and 'Failed' in p.stdout,'错误版本测试应真实失败。');has('sensor/results/test-before.log','Failed','expected=')
 elif key=='w5-3':
  has('sensor/results/gdb.txt','rad_s_to_rpm','10','600');has('sensor/notes/diagnosis.md','rad/s','rpm','2*pi')
  p=run('gdb','-q','-batch','-ex','break rad_s_to_rpm','-ex','run 10','-ex','print x','-ex','continue','--args','sensor/build/sensor_tool','10')
  require('ptrace' not in p.stderr.lower() and '600' in p.stdout and 'Breakpoint' in p.stdout,'无法实际重现GDB观察，请核对调试环境。')
 elif key=='w5-4':
  for v in [0,10,-10]:
   p=run(str(ROOT/'sensor/build/sensor_tool'),str(v));require(p.returncode==0 and abs(float(p.stdout)-v*60/(2*math.pi))<1e-6,'修复后的换算仍不正确。')
  require(run('ctest','--test-dir','sensor/build','--output-on-failure').returncode==0,'修复后测试仍失败。');has('sensor/results/test-after.log','100% tests passed')
  p=run('git','-C','sensor','show','HEAD:include/units.hpp');require('/' in p.stdout,'修复尚未提交。');require(run('git','-C','sensor','cat-file','-e','HEAD:notes/diagnosis.md').returncode==0,'提交缺少诊断说明。')
 elif key=='w6-1':
  require(run('omc','--version').returncode==0,'omc尚未安装。');has('results/omc-version.txt','OpenModelica');p=run('omc','scripts/prepare_modelica.mos');require('true' in p.stdout,'Modelica标准库尚未加载。');physical('results/modelica.csv')
 elif key=='w6-2':
  import labtool
  old=Path.cwd();os.chdir(ROOT)
  try:
   with contextlib.redirect_stdout(io.StringIO()):r=labtool.compare()
  finally:os.chdir(old)
  require(r['passed'],'模型对照误差超过课程容差。')
 elif key=='w6-3':
  physical('results/closedloop.csv',True);r=json.loads(text('results/control-metrics.json'));c=r['config'];require(abs(c['kp']-.08)<1e-8 and abs(c['ki']-.6)<1e-8 and c['anti_windup'] is True,'参考工况参数不符。')
  actual=simulate(c);require(actual['metrics']['steady_error_pct']<1,'参考工况未达稳态要求。')
 elif key=='w6-4':
  d=json.loads(text('results/diagnosis.json'));require(d['fault']=='units','本课要求单位错误诊断。');bad=simulate({'fault':'units'});good=simulate({'fault':'none'});require(abs(d['fault_metrics']['final_rpm']-bad['metrics']['final_rpm'])<1 and abs(d['fixed_metrics']['final_rpm']-good['metrics']['final_rpm'])<1,'故障/修复指标与实际模型不一致。')
  has('reports/report.md','学生作者','English abstract','Connor He','Astra');require('学生作者：待填写' not in text('reports/report.md'),'请填写学生作者和自己的分析。')
  manifest=json.loads(text('reports/manifest.json'));require('config/motor.json' in manifest['files'],'归档清单缺少参数。')
  with tarfile.open(ROOT/'reports/motor-project.tar.gz') as t:require('reports/report.md' in t.getnames() and 'config/motor.json' in t.getnames(),'归档内容不完整。')
 else:raise ValueError('未知检查项。')

if __name__=='__main__':
 try:
  require(len(sys.argv)==2 and re.fullmatch(r'w[1-6]-[1-4]',sys.argv[1]),'未知课程编号。')
  check(sys.argv[1]);result={'status':'passed','items':[{'message':'必要的文件、数值或程序状态检查通过。请继续解释原因并保留你的工程记录。'}]}
 except (FileNotFoundError,subprocess.TimeoutExpired) as e:result={'status':'environment_error','items':[{'message':'缺少文件/程序或执行超时：'+str(e)[:250]}]}
 except (AssertionError,RuntimeError,ValueError,KeyError,TypeError,OSError,tarfile.TarError) as e:result={'status':'failed','items':[{'message':str(e)[:400]}]}
 print(json.dumps(result,ensure_ascii=False))
