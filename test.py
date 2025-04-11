

import numpy as np
import matplotlib.pyplot as plt
import sympy as sp
from ipywidgets import interact
import ipywidgets as widgets
 

dx = 0.001
L = 10
x = np.arange(dx, L+dx, dx)
def define_fx(x):
    return np.where(x <= 5, x, np.sin(np.pi * x))

def calculate_Fourie(k):

    fx = define_fx(x)
    A0 = np.sum(fx) * dx/L
    FS = np.ones(len(x)) * A0

    Ak = np.zeros(k)
    Bk = np.zeros(k)
    for i in range(k):
        Ak[i] = np.sum(fx * np.cos(2 * np.pi * x * (i+1)/L)) * dx *2/L
        Bk[i] = np.sum(fx * np.sin(2 * np.pi * x * (i+1)/L)) * dx * 2/L
        FS = FS + Ak[i] * np.cos(2 * np.pi * x * (i+1)/L) + Bk[i] * np.sin(2 * np.pi * x * (i+1)/L)

    plt.figure(figsize=(12,6))
    plt.plot(x, FS, marker='', linestyle='--', color = "blue")
    plt.plot(x, fx, marker='', linestyle='-', color = "red")
    plt.grid(True)
    plt.show()

interact(calculate_Fourie, k=widgets.IntSlider(value = 1,min=1, max=100, step = 1))

#for i in range(k):
#    if i != 0: plt.pause(0.5)
#    calculate_Fourie(i)
#    plt.show()