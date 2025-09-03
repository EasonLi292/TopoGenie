import numpy as np

data = np.load("Dataset/4/Sequence_total4.npy", allow_pickle=True)
with open("Dataset/4/Sequence_total4.txt", "w") as f:
    for path in data:
        f.write(",".join(path) + "\n")