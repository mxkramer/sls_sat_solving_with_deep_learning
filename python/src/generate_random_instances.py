import numpy as np
import cnfgen
from pysat.formula import CNF
from pysat.solvers import Glucose3
import pickle
import random
import glob
from os.path import join


def get_cnf_from_file(path):
    if path[-2:] == "gz":
        cnf = CNF()
        cnf.from_file(path, compressed_with="gzip")
    else:
        cnf = CNF(from_file=path)
    return cnf


def create_candidates_with_sol(data_dir, sample_size, threshold):
    solved_instances = glob.glob(join(data_dir, "*_sol.pkl"))
    for g in solved_instances:
        with open(g, "rb") as f:
            p = pickle.load(f)
        n = np.array(list(p), dtype=bool)
        samples = sample_candidates(n, sample_size - 1, threshold)
        samples = np.concatenate((np.reshape(n, (1, len(n))), samples), axis=0)
        name = g.split("_sol.pkl")[0]
        with open(name + "_samples_sol.npy", "wb") as f:
            np.save(f, samples)


def sample_candidates(original, sample_size, threshold):
    np.random.seed(sum(original))
    condition = np.random.random((sample_size, original.shape[0])) < threshold
    return np.where(condition, np.invert(original), original)


def generate_random_KCNF(k, n, m, path, TIMEOUT=100):
    """generate a single random_KCNF formula

    Args:
        k (int): locality of instance
        n (int): number of variables of instance
        m (int): number of clauses contained in instance
        path (str): path and name how instance should be saved
        TIMEOUT (int, optional): how often we try to generate a satisfying formula until we return no instance. Defaults to 100.
    """
    t = 0
    sol = False
    while t <= TIMEOUT and sol == False:
        t += 1
        # print(t)
        cnf = cnfgen.RandomKCNF(k, n, m)
        cnf = cnf.to_dimacs()
        cnf = CNF(from_string=cnf)
        g = Glucose3(cnf)
        if g.solve() == True:
            sol = g.get_model()
            cnf.to_file(path + ".cnf")
            with open(path + "_sol.pkl", "wb") as f:
                pickle.dump(sol, f)
    if sol == False:
        print(
            "no satisfiable random_KCNF problem found for (n,k,m)=("
            + n
            + ","
            + k
            + ","
            + m
            + ")"
        )


def generate_dataset_random_KCNF(
    n_list, alpha, num_samples, path, vary_percent=0, TIMEOUT=100
):
    """This function generates a random_KCNF dataset.

    Args:
        n_list (list): list of number of variables that should be used for generating
        alpha (float): float describing the desired density of KCNF
        num_samples (int): number of samples generated per value in n_list
        path (str): path of where dataset should be saved
        vary_percent (float, optional): describes by how much we vary m at maximum
        TIMEOUT (int, optional): how often we try to generate a satisfying formula until we return no instance. Defaults to 100.
    """
    for n in n_list:
        for _ in range(num_samples):
            vary = 2 * (1 / 2 - random.random()) * vary_percent
            m = int((1 + vary) * alpha * n)
            index = str(random.randint(0, 10000000))
            params = str(k) + "_" + str(n) + "_" + str(m) + "_"
            generate_random_KCNF(
                k, n, m, path=path + "random_KCNF" + params + index, TIMEOUT=TIMEOUT
            )


def generate_Ramsey(s, k, N, path, TIMEOUT=100):
    """generate a single Ramsey formula

    Ramsey number r(s,k) > N
    This formula, given s, k, and N, claims that there is some graph with N vertices which has neither
    independent sets of size s nor cliques of size k.
    It turns out that there is a number r(s,k) so that every graph with at least r(s,k) vertices must
    contain either one or the other. Hence the generated formula is satisfiable if and only if r(s,k)>N

    Args:
        s (int): independent set size
        k (int): clique size
        N (int): number of vertices
        path (str): path and name how instance should be saved
        TIMEOUT (int, optional): how often we try to generate a satisfying formula until we return no instance. Defaults to 100.
    """
    t = 0
    sol = False
    while t <= TIMEOUT and sol == False:
        t += 1
        # print(t)
        cnf = cnfgen.RamseyNumber(s, k, N)
        cnf = cnf.to_dimacs()
        cnf = CNF(from_string=cnf)
        g = Glucose3(cnf)
        if g.solve() == True:
            sol = g.get_model()
            cnf.to_file(path + ".cnf")
            with open(path + "_sol.pkl", "wb") as f:
                pickle.dump(sol, f)
    if sol == False:
        print(
            "no satisfiable Ramsey problem found for (s,k,N)=("
            + s
            + ","
            + k
            + ","
            + N
            + ")"
        )


def generate_dataset_Ramsey(s_list, k_list, N_list, num_samples, path, TIMEOUT=100):
    """This function generates a random_KCNF dataset.

    Ramsey number r(s,k) > N
    This formula, given s, k, and N, claims that there is some graph with N vertices which has neither
    independent sets of size s nor cliques of size k.
    It turns out that there is a number r(s,k) so that every graph with at least r(s,k) vertices must
    contain either one or the other. Hence the generated formula is satisfiable if and only if r(s,k)>N

    Args:
        s (int): independent set size
        k (int): clique size
        N (int): number of vertices
        num_samples (int): number of samples generated per set of parameters
        path (str): path and name how instance should be saved
        TIMEOUT (int, optional): how often we try to generate a satisfying formula until we return no instance. Defaults to 100.
    """
    for s in s_list:
        for k in k_list:
            for N in N_list:
                for _ in range(num_samples):
                    index = str(random.randint(0, 10000000))
                    params = str(s) + "_" + str(k) + "_" + str(N) + "_"
                    generate_Ramsey(
                        s, k, N, path + "ramsey" + params + index, TIMEOUT=100
                    )


def generate_VanDerWaerden(N, k1, k2, path, TIMEOUT=100):
    """generate a single VanDerWaerden formula

    NOTE: tbf with details

    Args:
        N (int): size of interval
        k1 (int): length of arithmetic progressions of color 1
        k2 (int): length of arithmetic progressions of color 2
        path (str): path and name how instance should be saved
        TIMEOUT (int, optional): how often we try to generate a satisfying formula until we return no instance. Defaults to 100.
    """
    t = 0
    sol = False
    while t <= TIMEOUT and sol == False:
        t += 1
        # print(t)
        cnf = cnfgen.VanDerWaerden(N, k1, k2)
        cnf = cnf.to_dimacs()
        cnf = CNF(from_string=cnf)
        g = Glucose3(cnf)
        if g.solve() == True:
            sol = g.get_model()
            cnf.to_file(path + ".cnf")
            with open(path + "_sol.pkl", "wb") as f:
                pickle.dump(sol, f)
    if sol == False:
        print(
            "no satisfiable VanDerWaerden problem found for (N, k1, k2)=("
            + N
            + ","
            + k1
            + ","
            + k2
            + ")"
        )


def generate_dataset_VanDerWaerden(
    N_list, k1_list, k2_list, num_samples, path, TIMEOUT=100
):
    """This function generates a sa dataset containing VanDerWaerden formulas

    NOTE: tbf with details

    Args:
        N_list (list): list of size of interval
        k1 (list): list of length of arithmetic progressions of color 1
        k2 (list): list of length of arithmetic progressions of color 2
        num_samples (int): number of samples generated per set of parameters
        path (str): path and name how instance should be saved
        TIMEOUT (int, optional): how often we try to generate a satisfying formula until we return no instance. Defaults to 100.
    """
    for N in N_list:
        for k1 in k1_list:
            for k2 in k2_list:
                for _ in range(num_samples):
                    index = str(random.randint(0, 10000000))
                    params = str(N) + "_" + str(k1) + "_" + str(k2) + "_"
                    generate_VanDerWaerden(
                        N,
                        k1,
                        k2,
                        path + "VanDerWaerden" + params + index,
                        TIMEOUT=TIMEOUT,
                    )


path = "/Users/p403830/Library/CloudStorage/OneDrive-PorscheDigitalGmbH/programming/generateSAT/samples_medium/"

k = 3
alpha_3 = 4.17 * 0.8
num_samples = 30
n_list = [30, 40, 50]
vary_percent = 0.1
generate_dataset_random_KCNF(
    n_list, alpha_3, num_samples, path, vary_percent=vary_percent, TIMEOUT=100
)
"""
s_list = [10]
k_list = [5]
N_list = [12]
num_samples = 1

generate_dataset_Ramsey(s_list, k_list, N_list, num_samples, path, TIMEOUT = 100)

N_list = [5]
k1_list = [3]
k2_list = [2]
num_samples = 1
generate_dataset_VanDerWaerden(N_list, k1_list, k2_list, num_samples, path, TIMEOUT = 100)
"""

sample_size = 10
threshold = 0.03
create_candidates_with_sol(path, sample_size, threshold)
