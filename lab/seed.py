import json,os,subprocess,shutil
from pathlib import Path
DATA='''time_s,voltage_V,current_A,speed_rpm,load_Nm
0.0,12,0,0,0
0.1,12,4.0,80,0
0.2,12,3.2,160,0
0.3,12,,230,0
0.4,12,2.4,285,0
0.5,12,1.8,315,0
0.6,12,1.2,332,0
0.7,12,1.0,340,0
0.8,12,0.9,345,0
0.9,12,0.8,348,0
1.0,12,0.8,350,0
'''
def seed(root,week):
 root=Path(root);root.mkdir(exist_ok=True,parents=True)
 if (root/'.course-seeded').exists():return
 for d in ['notes','results','scripts','config','data','logs','reports']: (root/d).mkdir(exist_ok=True)
 (root/'data/motor.csv').write_text(DATA)
 (root/'config/motor.json').write_text(json.dumps({'R':2,'L':.002,'J':.0002,'b':.0001,'Kt':.05,'Ke':.05,'voltage_limit':24,'target_rpm':900,'duration':5,'load_time':2.5,'load_Nm':.03,'units':'SI; display rpm','source':'teaching parameters, not identified hardware'},indent=2))
 if week==5:
  for d in ['src','include','tests','results','notes']: (root/'sensor'/d).mkdir(parents=True,exist_ok=True)
  (root/'sensor/include/units.hpp').write_text('#pragma once\ninline double rad_s_to_rpm(double x) { return x * 60.0; }\n')
  (root/'sensor/src/main.cpp').write_text('#include <iostream>\n#include <iomanip>\n#include <cstdlib>\n#include "units.hpp"\nint main(int argc,char**argv){ if(argc!=2) return 2; std::cout << std::setprecision(12) << rad_s_to_rpm(std::stod(argv[1])) << "\\n"; }\n')
  (root/'sensor/tests/test_units.cpp').write_text('#include <cmath>\n#include <iostream>\n#include "units.hpp"\nint main(){for(double x : {0.0,10.0,-10.0}){double expected=x*60.0/(2*3.141592653589793); double actual=rad_s_to_rpm(x); if(std::abs(expected-actual)>1e-6){std::cerr<<"expected="<<expected<<" actual="<<actual<<"\\n";return 1;}}return 0;}\n')
  (root/'sensor/CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.16)\nproject(sensor_units LANGUAGES CXX)\nset(CMAKE_CXX_STANDARD 17)\ninclude_directories(include)\nadd_executable(sensor_tool src/main.cpp)\nadd_executable(test_units tests/test_units.cpp)\nenable_testing()\nadd_test(NAME units COMMAND test_units)\n')
  (root/'sensor/.gitignore').write_text('build/\nresults/\n')
  def git(*args):subprocess.run(['git','-C',str(root/'sensor'),*args],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  git('init');git('config','user.name','Student');git('config','user.email','student@example.invalid');git('add','.');git('commit','-m','Initial sensor unit conversion exercise')
 if week==6:
  src=Path('/opt/course/models')
  if src.exists():shutil.copytree(src,root/'models',dirs_exist_ok=True)
  (root/'scripts/prepare_modelica.mos').write_text('loadModel(Modelica, {"4.0.0"});\ngetErrorString();\n')
 (root/'.course-seeded').write_text(str(week))
if __name__=='__main__': seed('/workspace',int(os.environ.get('COURSE_WEEK','1')))
