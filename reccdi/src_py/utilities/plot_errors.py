#! /usr/bin/env python

import matplotlib.pyplot as plt
import numpy as np
import sys
import os

current_dir = sys.path[0]
print('plotting errors')
errs = np.load(os.path.join(current_dir, 'errors.npy')).tolist()
errs.pop(0)
plt.plot(errs)
plt.ylabel('errors')
plt.show()

