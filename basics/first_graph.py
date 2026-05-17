import numpy as np
import matplotlib.pyplot as plt

x = np.linspace(0, 20, 500)
y = np.sin(x)

plt.plot(x, y)

plt.title("First Astrophysics Graph")
plt.xlabel("x")
plt.ylabel("sin(x)")
plt.grid()

plt.show()