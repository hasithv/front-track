import numpy as np
import matplotlib.pyplot as plt
import reimann as rm
import linearization as lin

import types
from copy import deepcopy

def front_track(f, u, xlims, h, N=10, M=100):
    if N < 2:
        raise ValueError("N must be greater than 1")
    
    if isinstance(u, types.FunctionType):
        u_const = lin.pointwise_constant_evaluation(u, xlims, N)
        interface_positions = u_const[0][1:-1]
        interface_values = [(u_const[1][i], u_const[1][i+1]) for i in range(N-1)]
    elif isinstance(u, tuple):
        if xlims[0] != u[0][0] or xlims[1] != u[0][-1]:
            raise ValueError("lims must be the same as the bounds of u")
        u_const = u
        interface_positions = u_const[0][1:-1]
        interface_values = [(u_const[1][i], u_const[1][i+1]) for i in range(len(u_const[1])-1)]

    # fxlims = (np.min(u_const[1]), np.max(u_const[1]))
    # f_linear = lin.pointwise_linear_evaluation(f, fxlims, M)
    
    waves = []
    speeds = []
    for i in range(len(interface_values)):
        uL, uR = interface_values[i]
        # w, s = rm.reimann(f_linear, uL, uR, h, M)
        w, s = rm.reimann(f, uL, uR, h, M)
        waves.append(w)
        speeds.append(s)

    return waves, speeds, interface_positions

def plot_front_track(front_track_sol, xlims, T, N=100, t_offset=0, show=False):
    waves, speeds, interface_positions = front_track_sol
    
    for i in range(len(interface_positions)):
        rm.plot_reimann((waves[i], speeds[i]), xlims, T, N, x_offset=interface_positions[i], t_offset=t_offset, show=False)
    
    if show:
        plt.xlim(xlims)
        plt.ylim([t_offset, T+t_offset])
        plt.show()

def propagate_t(speeds, interface_positions, t, tol=1e-6):  
    wave_positions = []
    for i in range(len(interface_positions)):
        for s in speeds[i]:
            wp = interface_positions[i] + s*t
            if len(wave_positions) != 0 and np.abs(wp-wave_positions[-1]) > tol:
                wave_positions.append(wp)
            elif len(wave_positions) == 0:
                wave_positions.append(wp)
    
    return wave_positions

def collision_time(speeds, interface_positions, tol=1e-6):
    if len(speeds) != 2:
        raise IndexError("collision_time(speeds, interface_positions) only takes two sets of speeds and positions")
    if interface_positions[0] > interface_positions[1]:
        interface_positions = interface_positions[::-1]
        speeds = speeds[::-1]
    
    s1 = np.max(speeds[0])
    s2 = np.min(speeds[1])
    m1 = 1/s1
    m2 = 1/s2
    if np.abs(m1-m2) <= tol:
        return np.inf
    
    t=m1*m2*(interface_positions[1]-interface_positions[0])/(m2-m1)
    if t < 0:
        return np.inf
    return t

def collide(front_track, xlims, tol=1e-6):
    waves, speeds, interface_positions = deepcopy(front_track)
    collision_indices = []
    min_time = np.inf
    for i in range(len(interface_positions)-1):
        t = collision_time((speeds[i],speeds[i+1]), (interface_positions[i], interface_positions[i+1]))
        if t < min_time:
            min_time = t
            collision_indices = [i]
        elif t == min_time and t != np.inf:
            collision_indices.append(i)
        
    for i in collision_indices:
        waves[i] = waves[i][:-1]
        waves[i+1] = waves[i+1][1:]
    
    new_positions = propagate_t(speeds, interface_positions, min_time, tol=tol)
    new_positions = [xlims[0]] + [i for i in new_positions] + [xlims[1]]

    return rm.waves_to_const(waves, new_positions), min_time

def clean_front(front, tol=1e-6):
    waves, speeds, positions = front
    waves = [waves[i] for i in range(len(waves)) if len(speeds[i]) != 0]
    speeds = [s for s in speeds if len(s) != 0]

    removal = []
    for i in range(len(positions)-1):
        if np.abs(positions[i]-positions[i+1]) <= tol:
            removal.append(i)
    positions = [positions[i] for i in range(len(positions)) if i not in removal]

    return waves, speeds, positions

def plot_track_forward(f, u, xlims, h, N=10, M=100, itr=1, show=False):
    front = front_track(f, u, xlims, h, N, M)
    c = collide(front, xlims)
    c_time = c[1]
    if c[1] == np.inf:
        return front, c[1]
    
    plot_front_track(front, xlims, c[1], N=100, show=False)
    for i in range(itr):
        u_ = lin.constant_linspace(c[0])
        front = clean_front(front_track(f, u_, xlims, h, N=N, M=M))
        c = collide(front, xlims)
        
        if c[1] == np.inf:
            break
        
        plot_front_track(front, xlims, c[1], N=100, t_offset=c_time, show=False)
        c_time += c[1]
    
    if show:
        plt.xlim(xlims)
        plt.ylim([0, c_time])
        plt.show()

    return front, c_time

def f(x):
    # return x**2/2
    return -.5*x**4-x**3+6*x**2

def u(x):
    return 3*x**2

# make the plot bigger
fig = plt.gcf()
fig.set_size_inches(12, 5)

plt.subplot(1,3,1)
front, t = plot_track_forward(f, u, [-2, 1], 0.2, N=4, M=100, itr=0, show=True)
plt.show()
