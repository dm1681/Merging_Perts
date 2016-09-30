import numpy as np
import matplotlib.pyplot as plt

data = np.random.randint(1000) #replace this with the ecc data

np.histogram(data,range=(0,0.05)) # histogram w/ bin width 0.05
