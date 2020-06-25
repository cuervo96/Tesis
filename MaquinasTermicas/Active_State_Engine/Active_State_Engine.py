#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt
from numpy import linalg as LA
from scipy.linalg import sqrtm
from tqdm import tqdm

N_cycles = 1
t_hot= 10
t_cold = 10
tf = (t_cold + t_hot) * N_cycles
td = 0.85
dt = 0.001
N_hot = int(t_hot/dt)
N_cold = int(t_cold/dt)
N_cycle = N_hot + N_cold
N = N_cycle * N_cycles
Nd = int(td / dt)
h = 1.5
Id = [[1,0],[0,1]]
sz = [[1,0],[0,-1]]
sx = [[0,1],[1,0]]
su = [[0,0],[1,0]]
sd = [[0,1],[0,0]]
H = [[h/2.0,0],[0,-h/2.0]]
t = np.linspace(0,tf,N)
H_driven = np.zeros([N,2,2])
tau = 20*td

H_driven[0] = H
for i in range(N_hot,N_hot + 2*Nd, 2):
    H_driven[i] = (h/2)*(np.dot((1-np.exp(-t[i]/tau))*np.eye(2),sz) + np.dot(np.exp(-t[i]/tau)*np.eye(2),sx))
for i in range(N_hot + 1, N_hot + 2*Nd,2):
    H_driven[i] = H_driven[i-1]
for i in range(N_hot + 2*Nd, N):
    H_driven[i] = H
for i in range(N_hot):
    H_driven[i] = [[h/2,0],[0,-h/2]]


eps=  np.sqrt(5)
V = eps*(np.kron(su,su) + np.kron(sd,sd))

class reservoir():
    def __init__(self, hamiltonian, beta):
        self.hamiltonian = hamiltonian
        self.beta = beta
        self.state = self.Thermal_state()
    def Thermal_state(self):        
        return np.diag(np.diag(np.exp(np.dot(np.eye(2)*(-self.beta), self.hamiltonian))/np.sum(np.diag(np.diag(np.exp(np.dot(np.eye(2) * (-self.beta), self.hamiltonian)))))))
    def Active_state(self):        
        return np.diag(np.diag(np.exp(np.dot(np.eye(2) * self.beta, self.hamiltonian))/np.sum(np.diag(np.diag(np.exp(np.dot(np.eye(2) * self.beta, self.hamiltonian)))))))
cold_bath = reservoir(H, 5)
hot_bath = reservoir(H,1)

print(f"Energía del Active state frio = {np.trace(np.dot(cold_bath.Active_state(), H))}")
print(f"Energía del Active state caliente = {np.trace(np.dot(hot_bath.Active_state(), H))}")
print(f"Energía del Thermal state frio = {np.trace(np.dot(cold_bath.Thermal_state(), H))}")
print(f"Energía del Thermal state caliente = {np.trace(np.dot(hot_bath.Thermal_state(), H))}")

class system():
    def __init__(self):
        self.hamiltonian = H_driven
        self.state = np.zeros([N,2,2],dtype=np.complex)
        self.energy = np.zeros(N)
        self.work = np.zeros(N)
        self.heat = np.zeros(N)
s = system()   
s.state[0] = cold_bath.Active_state() 
s.heat[0] = 0

def D(x, y):
        rho = np.kron(x,y)
        Conmutator = np.dot(V,np.dot(V,rho))-np.dot(V,np.dot(rho,V))-np.dot(V,np.dot(rho,V))+np.dot(rho,np.dot(V,V))
        return (-0.5*np.trace(np.reshape(Conmutator,[2,2,2,2]), axis1 = 1, axis2 = 3))

def L(x, y):
    return -1j*(np.dot(s.hamiltonian[i],x) - np.dot(x,s.hamiltonian[i])) + D(x, y)
def L_Driven(x, y):
        return -1j*(np.dot(s.hamiltonian[i],x) - np.dot(x,s.hamiltonian[i]))
def K1(L, x, y):
    return dt * L(x, y)
def K2(L, x, y):
    return dt * (L(x + 0.5 * K1(L, x, y),y))
def K3(L, x, y):
    return dt * (L(x + 0.5 * K2(L, x, y),y))
def K4(L, x, y):
    return dt * (L(x + K3(L, x, y),y))

def RK4(L, x, y):
    return x + (1.0/6) * (K1(L, x, y)+2*K2(L, x, y)+2*K2(L, x, y)+K4(L, x, y))

for i in tqdm(range(0, N_hot)):
    s.state[i+1] = RK4(L, s.state[i],hot_bath.state)
    rhop = np.kron(s.state[i],hot_bath.state)
    Conmutator = np.dot(V,np.dot(V,np.kron(np.eye(2),hot_bath.hamiltonian)))-np.dot(V,np.dot(np.kron(np.eye(2),hot_bath.hamiltonian),V))-np.dot(V,np.dot(np.kron(np.eye(2),hot_bath.hamiltonian),V))+np.dot(np.kron(np.eye(2),hot_bath.hamiltonian),np.dot(V,V))
    s.heat[i+1] = s.heat[i] + dt * np.trace(np.dot(rhop, Conmutator)) * 0.5
for i in tqdm(range(N_hot, N_hot + 2 * Nd -1, 2)):
    s.state[i+1] = RK4(L, s.state[i],hot_bath.state)
    s.state[i+2] = RK4(L, s.state[i+1],hot_bath.state)
    rhop = np.kron(s.state[i],hot_bath.state)
    Conmutator = np.dot(V,np.dot(V,np.kron(np.eye(2),hot_bath.hamiltonian)))-np.dot(V,np.dot(np.kron(np.eye(2),hot_bath.hamiltonian),V))-np.dot(V,np.dot(np.kron(np.eye(2),hot_bath.hamiltonian),V))+np.dot(np.kron(np.eye(2),hot_bath.hamiltonian),np.dot(V,V))
    s.heat[i+1] = s.heat[i] + dt * np.trace(np.dot(rhop, Conmutator)) * 0.5
for i in tqdm(range(N_hot + 2 * Nd, N - 1)):
    s.state[i+1] = RK4(L, s.state[i], cold_bath.state)
    rhop = np.kron(s.state[i],cold_bath.state)
    Conmutator = np.dot(V,np.dot(V,np.kron(np.eye(2),cold_bath.hamiltonian)))-np.dot(V,np.dot(np.kron(np.eye(2),cold_bath.hamiltonian),V))-np.dot(V,np.dot(np.kron(np.eye(2),cold_bath.hamiltonian),V))+np.dot(np.kron(np.eye(2),cold_bath.hamiltonian),np.dot(V,V))
    s.heat[i+1] = s.heat[i] + dt * np.trace(np.dot(rhop, Conmutator)) * 0.5


s.energy[0] = np.trace(np.dot(H,s.state[0]))
for i in tqdm(range(1,N)):
    s.energy[i] = np.trace(np.dot(s.hamiltonian[i],s.state[i]))
for i in tqdm(range(N)):
    s.work[i] = s.heat[i] - s.energy[i]
for i in tqdm(range(1,N)):
    s.work[i] -= s.work[0]
s.work[0] = 0
rho_max = np.ones(N) * s.state[0,0,0]    
rho_min = np.ones(N) * s.state[0,1,1]    

print(f"Eficiencia = { s.work[-1] / s.heat[-N_cold]}")

plt.figure()
plt.plot(t,s.state[:,0,0], linewidth = 2)
plt.plot(t,s.state[:,0,1], linewidth = 2)
plt.plot(t,s.state[:,1,0], linewidth = 2)
plt.plot(t,s.state[:,1,1], linewidth = 2)
plt.legend(["rho_00","rho_01","rho_10","rho_11"])
plt.show()

plt.figure()
plt.plot(t,s.energy, linewidth = 2)
plt.plot(t,s.work,'r--', linewidth = 2)
plt.plot(t,s.heat,'C7-.', linewidth=2)
plt.ylabel("Energy", fontsize = 12)
plt.xlabel("Time", fontsize = 12)
plt.xticks(fontsize = 12)
plt.yticks(fontsize = 12)
plt.legend(["Energy", "Work", "Heat"])
plt.show()

