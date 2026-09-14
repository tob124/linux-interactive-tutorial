import numpy as np
from scipy.integrate import solve_ivp
import control
from motor import simulate,analytic_steady_state
A=np.array([[-2/.002,-.05/.002],[.05/.0002,-.0001/.0002]])
B=np.array([[1/.002],[0]])
t=np.linspace(0,5,1001)
x=solve_ivp(lambda t,x:A@x+B[:,0]*12,[0,5],[0,0],t_eval=t,rtol=1e-9,atol=1e-11).y
sys=control.ss(A,B,np.eye(2),np.zeros((2,1)))
r=control.forced_response(sys,t,np.full_like(t,12)).outputs
assert np.max(np.abs(x-r))<1e-6
reference=simulate({'mode':'open','voltage':12,'load_Nm':0})
assert abs(reference['metrics']['final_rpm']-x[1,-1]*60/(2*np.pi))<.01
print('SciPy / python-control / RK4 independent cross-check passed')
