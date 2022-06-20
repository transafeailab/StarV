#!/usr/bin/python3
from re import A
import sys
import copy
from traceback import print_last
import numpy as np

sys.path.insert(0, "engine/set/star/")
sys.path.insert(0, "engine/set/zono/")
sys.path.insert(0, "engine/set/box/")

# ------------- NOTEs: preprocessing library which contains the normalize function to normalize -------------
# ------------- the data. It takes an array in as an input and normalizes its values between 00 -------------
# ------------- and 11. It then returns an output array with the same dimensions as the input. -------------

# from sklearn import preprocessing
# from numba import njit, prange
from zono import Zono


class PosLin:
    # ------------- PosLin class contains method for reachability analysis for Layer with -------------
    # ------------- ReLU activation function (ReLU operator in NN) -------------

    # ------------- evaluate method and reachability analysis with stars -------------
    def evaluate(x):
        """
        evaluate method and reachability analysis with stars

        Args:
            @x = np.arrays

        Returns:
            0, if n <= 0
            n, if 0 <= n
        """

        # n = len(x)
        # if (len(x)[0] != 1):
        #     'error: x is not a vector'
        # y = np.zeros([n, 1])
        # for i in range(1,n):
        #     if x[i][1] < 0:
        #         y[i][1] == 0
        #     else:
        #         y[i][1] = x[i][1]
        # return y
        return np.maximum(x, 0)

    def stepReach(*args):
        """
        stepReach method, compute reachable set for a single step

        Args:
            @I: single star set input
            @index: index of current x[index] of current step (should be the number from matlab - 1)

        Others:
            @xmin: min of x[index]
            @xmax: max of x[index]

        Returns:
            @S: star output set
        """

        len_args = len(args)
        if len_args == 2:  # 2 arguments
            [I, index] = args
            lp_solver = 'gurobi'
        elif len_args == 3:  # 3 arguments
            [I, index, lp_solver] = args
        else:
            'error: Invalid number of input arguments, should be 2 or 3'

        from star import Star
        from zono import Zono

        assert isinstance(I, Star), 'error: input set is not a star set'

        # ------------- TODO: Using getMin and getMax after renew the gurobi license -------------
        xmin = I.getMin(index, lp_solver)
        # [xmin, xmax] = I.estimateRange(index)
        # print("\n xmin ------------------------ \n", xmin)

        if xmin >= 0:
            S = I
            return S
        else:
            # ------------- TODO: Using getMin and getMax after renew the gurobi license -------------
            xmax = I.getMax(index, lp_solver)
            # print("\n xmax ------------------------ \n", xmax)
            if xmax <= 0:
                V1 = copy.deepcopy(I.V)
                # print("\n V1 ------------------------ \n", V1)
                V1[index, :] = 0
                # print("\n V1 ------------------------ \n", V1)
                if isinstance(I.Z, Zono):
                    c = copy.deepcopy(I.Z.c)
                    c[index] = 0
                    # print("\n c ------------------------ \n", c)
                    V = copy.deepcopy(I.Z.V)
                    V[index, :] = 0
                    # print("\n V ------------------------ \n", V)
                    new_Z = Zono(c, V)
                else:
                    new_Z = np.array([])
                S = Star(V1, I.C, I.d, I.predicate_lb, I.predicate_ub, new_Z)
                return S
            else:
                # ------------- S1 = I && x[index] < 0 -------------
                c = copy.deepcopy(I.V[index, 0])
                # print("\n c ------------------------ \n", c)
                V = copy.deepcopy(I.V[index, 1:I.nVar + 1])
                # print("\n V ------------------------ \n", V)
                new_C = np.vstack([I.C, V])
                # print("\n new_C ------------------------ \n", new_C)
                new_d = np.hstack([I.d, -c])
                # print("\n new_d ------------------------ \n", new_d)
                new_V = copy.deepcopy(I.V)
                # print("\n new_V ------------------------ \n", new_V)
                new_V[index, :] = np.zeros([1, I.nVar + 1])
                # print("\n new_V ------------------------ \n", new_V)

                # ------------- update outer-zono -------------
                if isinstance(I.Z, Zono):
                    c1 = copy.deepcopy(I.Z.c)
                    # print("\n c1 ------------------------ \n", c1)
                    c1[index] = 0
                    # print("\n c1 ------------------------ \n", c1)
                    V1 = copy.deepcopy(I.Z.V)
                    # print("\n V1 ------------------------ \n", V1)
                    V1[index, :] = 0
                    # print("\n V1 ------------------------ \n", V1)
                    new_Z = Zono(c1, V1)
                else:
                    new_Z = np.array([])
                S1 = Star(new_V, new_C, new_d, I.predicate_lb, I.predicate_ub,
                          new_Z)
                # print("\n S1 ------------------------ \n", S1)

                # ------------- S2 = I && x[index] >= 0 -------------
                new_C1 = np.vstack([I.C, -V])
                # print("\n new_C1 ------------------------ \n", new_C1)
                new_d1 = np.hstack([I.d, c])
                # print("\n new_d1 ------------------------ \n", new_d1)
                S2 = Star(I.V, new_C1, new_d1, I.predicate_lb, I.predicate_ub,
                          I.Z)
                # print("\n S2 ------------------------ \n", S2)

                # S = np.column_stack([S1, S2])
                S = []
                S.append(S1)
                S.append(S2)
                return S

    def stepReachMultipleInputs(*args):
        """
        stepReach with multiple inputs

        Args:
            @I: an list of stars
            @index: index where stepReach is performed
            @option: = 'parallel' use parallel computing
                     = not declare -> don't use parallel computing

        Returns:
            @S: star output set
        """

        len_args = len(args)
        if len_args == 3:  # 3 arguments
            [I, index, option] = args
            lp_solver = 'gurobi'
        elif len_args == 4:  # 4 arguments
            [I, index, option, lp_solver] = args
        else:
            'error: Invalid number of input arguments'

        from star import Star

        assert isinstance(I, list), 'error: input is not an array star sets'
        assert isinstance(I[0], Star), 'error: input is not a star set'
        # print("\n I[0] ------------------------ \n", I[0])

        p = len(I)
        S = []

        if len(option) == 0:
            for i in range(p):
                S1 = PosLin.stepReach(I[i], index, lp_solver)
                # print("\n S1 ------------------------ \n", S1)
                # S = np.array([S, S1]) if S.size else S1
                S.extend(S1)
                # print("\n S ------------------------ \n", len(S))
                return S
                #  ------------- Dont need to extend the S again  -------------
                # if len(S):
                # temp = len(S)
                # S.extend(S)
                # S.extend(S1)
                # del S[:temp]
                # else:
                # S.extend(S1)

        # ------------- TODO: Fix parallel part -------------
        # elif option == 'parellel':
        #     #@njit(parallel=True)
        #     for i in prange(p):
        #         S = np.column_stack([S, PosLin.stepReach(I[i], index, lp_solver)])
        #     return S
        else:
            "error: Unknown option"

    def reach_star_exact(*args):
        """
        exact reachability analysis using star

        Args:
            @I: star input sets
            @option: = 'parallel' use parallel computing
                     = not declare -> don't use parallel computing
        Returns:
            @S: star output set
        """

        len_args = len(args)
        if len_args == 2:  # 2 arguments
            [I, option] = args
            dis_opt = ""
            lp_solver = 'gurobi'
        elif len_args == 3:  # 3 arguments
            [I, option, dis_opt] = args
            lp_solver = 'gurobi'
        elif len_args == 4:  # 4 arguments
            [I, option, dis_opt, lp_solver] = args
        else:
            "error: Invalid number of input arguments, should be 2, 3 or 4"

        from star import Star
        from zono import Zono

        # ------------- TODO: Fix gurobi license -------------
        # if not Star.isEmptySet(I):
        if isinstance(I, Star):
            [lb, ub] = Star.estimateRanges(I)
            # print("\n lb ------------------------ \n", lb)
            # print("\n ub ------------------------ \n", ub)

            if len(lb) == 0 or len(ub) == 0:
                # S = np.array([])
                S = []
                return S
            else:
                # ------------- Old Flattened Map -------------
                # flatten_ub = np.ndarray.flatten(ub, "F")
                # map = np.argwhere(flatten_ub <= 0)
                # ub_map = np.array([])
                # for i in range(len(map)):
                #     # index = map[i][1] * len(flatten_ub[0]) + map[0][i]
                #     index = map[i][1]
                #     ub_map = np.append(ub_map, index)
                # print("\n ub_map ------------------------ \n", ub_map)
                # ------------- Old Flattened Map -------------

                map = np.argwhere(ub <= 0)  # computation map
                # print("\n map ------------------------ \n", map)
                V = copy.deepcopy(I.V)
                # print("\n V ------------------------ \n", V)
                V[map, :] = 0
                print("\n V ------------------------ \n", V)

                # ------------- update outer-zono -------------
                if isinstance(I.Z, Zono):
                    # ------------- TODO: modify the map -------------
                    c1 = copy.deepcopy(I.Z.c)
                    print("\n c1 ------------------------ \n", c1)
                    c1[map] = 0
                    V1 = copy.deepcopy(I.Z.V)
                    # print("\n V1 ------------------------ \n", V1)
                    V1[map, :] = 0
                    # print("\n V1 ------------------------ \n", V1)
                    # print("\n c1 ------------------------ \n", c1)
                    new_Z = Zono(c1, V1)
                else:
                    new_Z = np.array([])

                In = Star(V, I.C, I.d, I.predicate_lb, I.predicate_ub, new_Z)
                # print("\n In ------------------------ \n", In)

                lb_map = np.argwhere(lb < 0)
                # print("\n lb_map ------------------------ \n", lb_map)
                ub_map = np.argwhere(ub > 0)
                # print("\n ub_map ------------------------ \n", ub_map)
                map_float = np.intersect1d([lb_map], [ub_map])
                map = np.array(map_float, dtype=np.int)
                map_to_list = map.tolist()
                # print("\n map_to_list ------------------------ \n", map_to_list)
                m = len(map_to_list)
                # print("\n m ------------------------ \n", m)

                # ------------- Old Flattened Map -------------
                # flatten_lb = np.ndarray.flatten(lb, "F")
                # map = np.argwhere(flatten_lb < 0)
                # lb_map = np.array([])
                # for i in range(len(map)):
                #     # index = map[i][1] * len(flatten_lb[0]) + map[0][i]
                #     index = map[i][1]
                #     lb_map = np.append(lb_map, index)

                # map = np.argwhere(flatten_ub > 0)
                # ub_map = np.array([])
                # for i in range(len(map)):
                #     # index = map[i][1] * len(flatten_ub[0]) + map[0][i]
                #     index = map[i][1]
                #     ub_map = np.append(ub_map, index)

                # lu_map_float = np.intersect1d([lb_map], [ub_map])
                # lu_map = np.array(lu_map_float, dtype=np.int)
                # listed_lu_map = lu_map.tolist()
                # m = len(listed_lu_map)
                # ------------- Old Flattened Map -------------

                # In = np.array([In])
                In_list = []
                In_list.append(In)
                for i in range(m):
                    if dis_opt == 'display':
                        print(
                            "\n Performing exact PosLin_%d operation using Star",
                            map_to_list[i])
                    # print("\n In_list ------------------------ \n", In_list)
                    In_list = PosLin.stepReachMultipleInputs(
                        In_list, map_to_list[i], option, lp_solver)
                S = In_list
                return S
        else:
            S = []
            return S

    def reach_star_exact_multipleInputs(*args):
        """
        exact reachability analysis using star

        Args:
            @I: star input sets
            @option: = 'parallel' use parallel computing
                     = not declare -> don't use parallel computing
        Returns:
            @S: star output set
        """

        len_args = len(args)
        if len_args == 2:  # 2 args
            [In, option] = args
            dis_opt = ''
            lp_solver = 'gurobi'
        elif len_args == 3:  # 3 args
            [In, option, dis_opt] = args
            lp_solver = 'gurobi'
        elif len_args == 4:  # 4 args
            [In, option, dis_opt, lp_solver] = args
        else:
            'error: Invalid number of input arguments, should be 2, 3, or 4'

        #print("\n In: ------------------------ \n ", In)
        n = len(In)
        # S = np.array([])
        S = []
        if len(option) == 0 or option == 'single':
            #print("\n option: ------------------------ \n", option)
            for i in range(n):
                S1 = PosLin.reach_star_exact(In[i], [], dis_opt, lp_solver)
                S.extend(S1)

                #  ------------- Dont need to extend the S again  -------------
                # if len(S):
                # temp = len(S)
                # S.extend(S)
                # S.extend(S1)
                # del S[:temp]
                # else:
                # S.extend(S1)
                # S = np.vstack([S, PosLin.reach_star_exact(In[i], [], dis_opt, lp_solver)])
                return S
        # elif option == 'parallel':
        #     for i in prange (n):
        #         S = np.vstack([S, PosLin.reach_star_exact(In[i], [], dis_opt, lp_solver)])
        #     return S
        else:
            'error: unknown computation option'

    def stepReachStarApprox(I, index):
        """
        step reach approximation using star

        Args:
            @I: Star set input
            @index: index of the neuron performing stepReach

        Returns:
            @S: star output
        """

        from star import Star
        from zono import Zono

        assert isinstance(I, Star), 'error: input set is not a star set'

        # [lb, ub] = I.estimateRange(index)
        # ------------- TODO: Call get Mins Maxs -------------
        lb = I.getMin(index)
        # print("\n lb ------------------------ \n", lb)

        if lb > 0:
            S = I
            return S
        else:
            ub = I.getMax(index)
            # print("\n ub ------------------------ \n", ub)
            if ub <= 0:
                V = copy.deepcopy(I.V)
                V[index, :] = 0
                # print("\n V ------------------------ \n", V)
                if isinstance(I.Z, Zono):
                    c1 = copy.deepcopy(I.Z.c)
                    # print("\n c1 ------------------------ \n", c1)
                    c1[index] = 0
                    # print("\n c1 ------------------------ \n", c1)
                    V1 = copy.deepcopy(I.Z.V)
                    # print("\n V1 ------------------------ \n", V1)
                    V1[index, :] = 0
                    # print("\n V1 ------------------------ \n", V1)
                    new_Z = Zono(c1, V1)
                else:
                    new_Z = np.array([])
                S = Star(V, I.C, I.d, I.predicate_lb, I.predicate_ub, new_Z)
                return S
            else:
                print("\n Add a new predicate variables at index = %d", index)
                n = I.nVar + 1
                # print("\n n ------------------------ \n", n)
                # ------------- over-approximation constraints -------------
                # ------------- constraint 1: y[index] = ReLU(x[index]) >= 0 -------------
                C1 = np.zeros([1, n])
                C1[0, n - 1] = -1
                # print("\n C1 ------------------------ \n", C1)
                d1 = 0
                # ------------- constraint 2: y[index] >= x[index] -------------
                C2 = np.hstack([I.V[index, 1:n], -1])
                # print("\n C2 ------------------------ \n", C2)
                d2 = copy.deepcopy(-I.V[index, 0])
                # print("\n d2 ------------------------ \n", d2)
                # ------------- constraint 3: y[index] <= ub(x[index] - lb)/(ub - lb) -------------
                C3 = np.hstack([-(ub / (ub - lb)) * I.V[index, 1:n], 1])
                # print("\n C3 ------------------------ \n", C3)
                d3 = -ub * lb / (ub - lb) + ub * I.V[index, 0] / (ub - lb)
                # print("\n d3 ------------------------ \n", d3)

                m = I.C.shape[0]
                # print("\n m ------------------------ \n", m)
                C0 = np.hstack([I.C, np.zeros([m, 1])])
                # print("\n C0 ------------------------ \n", C0)
                d0 = copy.deepcopy(I.d)
                # print("\n d0 ------------------------ \n", d0)
                new_C = np.vstack([C0, C1, C2, C3])
                # print("\n new_C ------------------------ \n", new_C)
                new_d = np.hstack([d0, d1, d2, d3])
                # print("\n new_d ------------------------ \n", new_d)
                new_V = np.hstack([I.V, np.zeros([I.dim, 1])])
                # print("\n new_V ------------------------ \n", new_V)
                new_V[index, :] = np.zeros([1, n + 1])
                new_V[index, n] = 1
                # print("\n new_V ------------------------ \n", new_V)
                new_predicate_lb = np.hstack([I.predicate_lb, 0])
                # print("\n predicate_lb ------------------------ \n", I.predicate_lb)
                # print("\n new_predicate_lb ------------------------ \n", new_predicate_lb)
                new_predicate_ub = np.hstack([I.predicate_ub, ub])
                # print("\n predicate_ub ------------------------ \n", I.predicate_ub)
                # print("\n new_predicate_ub ------------------------ \n", new_predicate_ub)

                # ------------- update outer-zono -------------
                lamda = ub / (ub - lb)
                # print("\n lamda ------------------------ \n", lamda)
                mu = -0.5 * ub * lb / (ub - lb)
                # print("\n mu ------------------------ \n", mu)
                if isinstance(I.Z, Zono):
                    c = copy.deepcopy(I.Z.c)
                    # print("\n c ------------------------ \n", c)
                    c[index] = lamda * c[index] + mu
                    # print("\n c ------------------------ \n", c)
                    V = copy.deepcopy(I.Z.V)
                    # print("\n V ------------------------ \n", V)
                    V[index, :] = lamda * V[index, :]
                    # print("\n V ------------------------ \n", V)
                    I1 = np.zeros([I.dim, 1])
                    # print("\n I1 ------------------------ \n", I1)
                    I1[index] = mu
                    # print("\n I1 ------------------------ \n", I1)
                    V = np.hstack([V, I1])
                    # print("\n V ------------------------ \n", V)
                    new_Z = Zono(c, V)
                else:
                    new_Z = np.array([])

                S = Star(new_V, new_C, new_d, new_predicate_lb,
                         new_predicate_ub, new_Z)
                return S

    def reach_star_approx(I):
        """
        over-approximate reachability analysis using Star

        Args:
            @I: star input set

        Returns:
            @S: star output set
        """

        from star import Star
        from zono import Zono

        assert isinstance(I, Star), 'error: input set is not a star set'

        # ------------- TODO: Fix gurobi license -------------
        # if Star.isEmptySet(I):
        if I.V.shape[0] == 0:
            # S = np.array([])
            S = []
            return S
        else:
            [lb, ub] = Star.estimateRanges(I)
            # print("\n lb ------------------------ \n", lb)
            # print("\n ub ------------------------ \n", ub)
            if len(lb) == 0 or len(ub) == 0:
                # S = np.array([])
                S = []
                return S
            else:
                # ------------- Old Flattened Map -------------
                # flatten_ub = np.ndarray.flatten(ub, "F")
                # map = np.argwhere(flatten_ub <= 0)
                # ub_map = np.array([])
                # for i in range(len(map)):
                #     # index = map[i][1] * len(flatten_ub[0]) + map[0][i]
                #     index = map[i][1]
                #     print(index)
                #     ub_map = np.append(ub_map, index)
                # ------------- Old Flattened Map -------------

                map = np.argwhere(ub <= 0)
                # print("\n ub_map ------------------------ \n", ub_map)
                V = copy.deepcopy(I.V)
                V[map, :] = 0
                # print("\n V ------------------------ \n", V)

                if isinstance(I.Z, Zono):
                    c1 = copy.deepcopy(I.Z.c)
                    c1[map] = 0
                    # print("\n c1 ------------------------ \n", c1)
                    V1 = copy.deepcopy(I.Z.V)
                    V1[map, :] = 0
                    # print("\n V1 ------------------------ \n", V1)
                    new_Z = Zono(c1, V1)
                else:
                    new_Z = np.array([])

                In = Star(V, I.C, I.d, I.predicate_lb, I.predicate_ub, new_Z)
                # print("\n In ------------------------ \n", In)

                lb_map = np.argwhere(lb < 0)
                # print("\n lb_map ------------------------ \n", lb_map)
                ub_map = np.argwhere(ub > 0)
                # print("\n ub_map ------------------------ \n", ub_map)
                map_float = np.intersect1d([lb_map], [ub_map])
                map = np.array(map_float, dtype=np.int)
                map_to_list = map.tolist()
                # print("\n map_to_list ------------------------ \n", map_to_list)
                m = len(map_to_list)
                # print("\n m ------------------------ \n", m)

                # ------------- Old Flattened Map -------------
                # flatten_lb = np.ndarray.flatten(lb, "F")
                # map = np.argwhere(flatten_lb < 0)
                # lb_map = np.array([])
                # for i in range(len(map)):
                #     # index = map[i][1] * len(flatten_lb[0]) + map[0][i]
                #     index = map[i][1]
                #     lb_map = np.append(lb_map, index)

                # map = np.argwhere(flatten_ub > 0)
                # ub_map = np.array([])
                # for i in range(len(map)):
                #     # index = map[i][1] * len(flatten_ub[0]) + map[0][i]
                #     index = map[i][1]
                #     ub_map = np.append(ub_map, index)

                # lu_map_float = np.intersect1d([lb_map], [ub_map])
                # lu_map = np.array(lu_map_float, dtype=np.int)
                # listed_lu_map = lu_map.tolist()
                # m = len(listed_lu_map)
                # ------------- Old Flattened Map -------------

                for i in range(m):
                    print(
                        "\n Performing approximate PosLin_%d operation using Star"
                        % map_to_list[i])
                    In = PosLin.stepReachStarApprox(In, map_to_list[i])
                    # print("\n In ------------------------ \n", In.__repr__())
                S = In
                return S

    # ------------- over-approximate reachability analysis use zonotope -------------
    def stepReachZonoApprox(I, index, lb, ub):
        """
        step over-approximate reachability analysis using zonotope
        reference: Fast and Effective Robustness Ceritification,
        Gagandeep Singh, NIPS 2018

        Args:
            @I: zonotope input set
            @index: index of the neuron we want to perform stepReach
            @lb: lower bound of input at specific neuron i
            @ub: lower bound of input at specfic neuron i

        Returns:
            @Z: zonotope output set
        """

        from zono import Zono
        assert isinstance(I, Zono), "error: input set is not a Zonotope"

        if lb >= 0:
            Z = Zono(I.c, I.V)
        elif ub <= 0:
            c = copy.deepcopy(I.c)
            # print("\n c ------------------------ \n", c)
            c[index] = 0
            # print("\n c ------------------------ \n", c)
            V = copy.deepcopy(I.V)
            # print("\n V ------------------------ \n", V)
            V[index, :] = np.zeros([1, I.V.shape[1]])
            # print("\n V ------------------------ \n", V)
            Z = Zono(c, V)
        elif lb < 0 and ub > 0:
            lamda = ub / (ub - lb)
            # print("\n lamda ------------------------ \n", lamda)
            mu = -0.5 * ub * lb / (ub - lb)
            # print("\n mu ------------------------ \n", mu)
            c = copy.deepcopy(I.c)
            # print("\n c ------------------------ \n", c)
            c[index] = lamda * c[index] + mu
            # print("\n c ------------------------ \n", c)
            V = copy.deepcopy(I.V)
            # print("\n V ------------------------ \n", V)
            V[index, :] = lamda * V[index, :]
            # print("\n V ------------------------ \n", V)
            I1 = np.zeros([I.dim, 1])
            # print("\n I1 ------------------------ \n", I1)
            I1[index] = mu
            # print("\n I1 ------------------------ \n", I1)
            V = np.hstack([V, I1])
            # print("\n V ------------------------ \n", V)
            Z = Zono(c, V)
            # print("\n Z ------------------------ \n", Z)

        return Z

    def reach_zono_approx(*args):
        """
        Over-approximate reachability analysis use zonotope
        reference: Fast and Effective Robustness Ceritification,
        Gagandeep Singh, NIPS 2018
        
        Args:
            @I: zonotope input

        Returns:
            @Z: zonotope output
        """
        from zono import Zono

        if len(args) == 1:
            I = args[0]
            dis_opt = ""
        elif len(args) == 2:
            [I, dis_opt] = args
        else:
            'error: Invalid number of input arguments, should be 1 or 2'

        assert isinstance(I, Zono), 'error: input set is not a Zonotope'
        In = I
        # print("\n In ------------------------ \n", In.__repr__())
        [lb, ub] = I.getBounds()
        # print("\n lb ------------------------ \n", lb)
        # print("\n ub ------------------------ \n", ub)
        for i in range(I.dim):
            # print("\ni ------------------------ \n", i)
            if dis_opt == 'display':
                print(
                    "\n Performing approximate PosLin_%d operation using Zonotope"
                    % i)
            In = PosLin.stepReachZonoApprox(In, i, lb[i], ub[i])
            # print("\n In ------------------------ \n", In.__repr__())

        Z = In

        return Z

    def reach(*args):
        """
        main function for reachability analysis

        Returns:
            reachability analysis result
        """

        if len(args) == 6:  # 6 arguments
            [I, method, option, relaxFactor, dis_opt, lp_solver] = args
        elif len(args) == 5:  # 5 arguments
            [I, method, option, relaxFactor, dis_opt] = args
            lp_solver = 'gurobi'
        elif len(args) == 4:  # 4 arguments
            [I, method, option, relaxFactor] = args
            dis_opt = ""  # display option
            lp_solver = 'gurobi'
        elif len(args) == 3:  # 3 arguments
            [I, method, option] = args
            relaxFactor = 0  # used for aprx-star only
            dis_opt = ""  # display option
            lp_solver = 'gurobi'
        elif len(args) == 2:  # 2 arguments
            [I, method] = args
            option = 'parallel'
            relaxFactor = 0  # used for aprx-star only
            dis_opt = ""  # display option
            lp_solver = 'gurobi'
        elif len(args) == 1:  # 1 arguments
            I = args[0]
            method = 'exact-star'
            option = 'parallel'
            relaxFactor = 0  # used for aprx-star only
            dis_opt = ""  # display option
            lp_solver = "gurobi"
        else:
            'error: Invalid number of input arguments (should be 1, 2, 3, 4, or 5)'

        # ------------- TODO: Fix parallel -------------
        option = ''
        if method == 'exact-star':  # exact analysis using star
            R = PosLin.reach_star_exact_multipleInputs(I, option, dis_opt,
                                                       lp_solver)
            # R = PosLin.reach_star_exact(I, np.array([]))
            return R
        # elif method == 'exact-polyhedron': # exact analysis using polyhedron
        #     R = PosLin.reach_polyhedron_exact(I, option, dis_opt)
        elif method == 'approx-star':  # over-approximate analysis using star
            # R = PosLin.reach_star_approx(I, option, dis_opt, lp_solver)
            R = PosLin.reach_star_approx(I)
            return R
        elif method == 'approx-zono':  # over-approximate analysis using zonotope
            R = PosLin.reach_zono_approx(I, dis_opt)
            return R


# ------------- Unused Functions -------------

# # New stepReach method, compute reachable set for a single step
# # minimize the number of LP using simulation
# def stepReach2(I, index):
#     # @I: single star set input
#     # @index: index of the neuron performing stepPosLin
#     # @xmin: minimum of x[index]
#     # @xmax: maximum mof x[index]
#     # @S: star output set
#
#     from star import Star
#     from zono import Zono
#
#     assert isinstance(I, Star), 'error: input is not a star set'
#
#     x1 = I.V[index, 0] + I.V[index, 1:I.nVar + 1] * I.predicate_lb
#     x2 = I.V[index, 0] + I.V[index, 1:I.nVar + 1] * I.predicate_ub
#
#     if x1*x2 < 0:
#         # S1 = I && x[index] < 0
#         c = copy.deepcopy(I.V[index, 0])
#         V = copy.deepcopy(I.V[index, 1:I.nVar + 1])
#         new_C = np.vstack([I.C, V])
#         new_d = np.vstack([I.d, -c])
#         new_V = copy.deepcopy(I.V)
#         new_V[index, :] = np.zeros([1, I.nVar + 1])
#
#         # update outer-zono
#         if not isinstance(I.Z, Zono):
#             c1 = copy.deepcopy(I.Z.c)
#             c1[index] = 0
#             V1 = copy.deepcopy(I.Z.V)
#             V1[index, :] = 0;
#             new_Z = Zono(c1, V1)
#         else:
#             new_Z = np.array([])
#         S1 = Star(new_V, new_C, new_d, I.predicate_lb, I.predicate_ub, new_Z)
#
#         # S2 = I && x[index] >= 0
#         new_C = np.vstack([I.C, -V])
#         new_d = np.vstack([I.d, c])
#         S2 = Star(I.V, new_C, new_d, I.predicate_lb, I.predicate_ub, I.Z)
#
#         S = np.column_stack([S1, S2])
#         return S
#
#     else:
#         if (x1 < 0 and x2 < 0):
#             xmax = I.getMax(index)
#             if xmax <= 0:
#                 V1 = copy.deepcopy(I.V)
#                 V1[index, :] = 0
#                 if not isinstance(I.Z, Zono):
#                     c = copy.deepcopy(I.Z.c)
#                     c[index] = 0
#                     V = copy.deepcopy(I.Z.V)
#                     V[index, :] = 0
#                     new_Z = Zono(c, V) # update outer-zono
#                 else:
#                     new_Z = np.array([])
#                 S = Star(V1, I.C, I.d, I.predicate_lb, I.predicate_ub, new_Z)
#                 return S
#             else:
#                 # S1 = I && x[index] < 0
#                 c = copy.deepcopy(I.V[index, 0])
#                 V = copy.deepcopy(I.V[index, 1:I.nVar + 1])
#                 new_C = np.vstack([I.C, V])
#                 new_d = np.vstack([I.d, -c])
#                 new_V = copy.deepcopy(I.V)
#                 new_V[index, :] = np.zeros([1, I.nVar + 1])
#
#                 # update outer-zono
#                 if not isinstance(I.Z, Zono):
#                     c1 = copy.deepcopy(I.Z.c)
#                     c1[index] = 0
#                     V1 = copy.deepcopy(I.Z.V)
#                     V1[index, :] = 0
#                     new_Z = Zono(c1, V1)
#                 else:
#                     new_Z = np.array([])
#                 S1 = Star(new_V, new_C, new_d, I.predicate_lb, I.predicate_ub, new_Z)
#
#                 # S2 = I && x[index] >= 0
#                 new_C = np.vstack([I.C, -V])
#                 new_d = np.vstack([I.d, c])
#
#                 S2 = Star(I.V, new_C, new_d, I.predicate_lb, I.predicate_ub, I.Z)
#
#                 S = np.column_stack([S1, S2])
#                 return S
#         else:
#             xmin = I.getMin(index)
#             if xmin >= 0:
#                 S = I
#                 return S
#             else:
#                 # S1 = I && x[index] < 0
#                 c = copy.deepcopy(I.V[index, 0])
#                 V = copy.deepcopy(I.V[index, 1:I.nVar + 1])
#                 new_C = np.vstack([I.C, V])
#                 new_d = np.vstack([I.d, -c])
#                 new_V = copy.deepcopy(I.V)
#                 new_V[index, :] = np.zeros([1, I.nVar + 1])
#
#                 # update outer-zono
#                 if not isinstance(I.Z, Zono):
#                     c1 = copy.deepcopy(I.Z.c)
#                     c1[index] = 0
#                     V1 = copy.deepcopy(I.Z.V)
#                     V1[index, :] = 0
#                     new_Z = Zono(c1, V1)
#                 else:
#                     new_Z = np.array([])
#                 S1 = Star(new_V, new_C, new_d, I.predicate_lb, I.predicate_ub, new_Z)
#
#                 # S2 = I && x[index] >= 0
#                 new_C = np.vstack([I.C, -V])
#                 new_d = np.vstack([I.d, c])
#                 S2 = Star(I.V, new_C, new_d, I.predicate_lb, I.predicate_ub, I.Z)
#
#                 S = np.column_stack([S1, S2])
#                 return S

# # step reach approximation using star
# def multipleStepReachStarApprox_at_one(I, index, lb, ub):
#     # @I: star set input
#     # @index: index of the neurons performing stepReach
#     # @lb: lower bound of x[index]
#     # @ub: upper bound of x[index]
#
#     from star import Star
#     assert isinstance(I, Star), 'error: input set is not a star set'
#
#     N = I.dim
#     m = len(index) # number of neurons involved (number of new predicate variables introduced)
#
#     # construct new basis array
#     V1 = copy.deepcopy(I.V) # originaial basis array
#     V1[index, :] = 0
#     V2 = np.zeros([N, m]) # basis array for new predicates
#     for i in range (m):
#         V2[index[i], i] = 1
#     new_V = np.column_stack([V1, V2]) # new basis for over-approximate star set
#
#     # construct new constraints on new predicate variables
#     # case 0: keep the old constraints on the old predicate variable
#     n = I.nVar # number of old predicate variables
#     C0 = np.column_stack([I.C, np.zeros([I.C.shape[0], m])])
#     d0 = copy.deepcopy(I.d)
#
#     # case 1: y[index] >= 0
#     C1 = np.column_stack([np.zeros([m, n]), -np.identity([m])])
#     d1 = np.zeros([m ,1])
#
#     # case 2: y[index] >= x[index]
#     C2 = np.column_stack([I.V[index, 1:n+1], -V2[index, 0:m]])
#     d2 = copy.deepcopy(-I.V[index, 0])
#
#     # case 3: y[index] <= (ub/(ub - lb))*(x-lb)
#     # add....
#     a = ub/(ub-lb) # devide element-wise
#     b = np.multiply(a, lb) # multiply element-wise
#     C3 = np.column_stack([np.multiply(-a, I.V[index, 1:n+1]), V2[index, 0:m]])
#     d3 = np.multiply(a, I.V[index, 0]) - b
#
#     new_C = np.vstack([C0, C1, C2, C3])
#     new_d = np.vstack([d0, d1, d2, d3])
#
#     new_pred_lb = np.vstack([I.predicate_lb, np.zeros([m, 1])])
#     new_pred_ub = np.vstack([I.predicate_ub, ub])
#
#     S = Star(V=new_V, C=new_C, d=new_d, pred_lb=new_pred_lb, pred_ub=new_pred_ub)
#     return S

# # more efficient method by doing multiple stepReach at one time
# # over-approximate reachability analysis using Star
# def reach_star_approx2(*args):
#     # @I: star input set
#     # @option: 'parallel' or single
#     # @S: star output set
#
#     if len(args) == 1:
#         I = args[0]
#         option = 'single'
#         dis_opt = ''
#         lp_solver = 'glpk'
#     elif len(args) == 2:
#         I = args[0]
#         option = args[1]
#         dis_opt = ''
#         lp_solver = 'glpk'
#     elif len(args) == 3:
#         I = args[0]
#         option = args[1]
#         dis_opt = args[2]
#         lp_solver = 'glpk'
#     elif len(args) == 4:
#         I = args[0]
#         option = args[1]
#         dis_opt = args[2]
#         lp_solver = args[3]
#     else:
#         'error: Invalid number of input arguments, should be 1, 2, 3, or 4'
#
#     from star import Star
#     assert isinstance(I, Star), 'error: input set is not a star set'
#
#     if Star.isEmptySet(I):
#         S = np.array([])
#         return S
#     else:
#         [lb, ub] = I.estimateRanges;
#         if len(lb) == 0 or len(ub) == 0:
#             S = np.array([])
#             return S
#         else:
#             # find all indexes having ub <= 0, then reset the
#             # values of the elements corresponding to these indexes to 0
#             flatten_ub = np.ndarray.flatten(ub, 'F')
#             flatten_lb = np.ndarray.flatten(lb, 'F')
#
#             if dis_opt == 'display':
#                 print('\nFinding all neurons (in %d neurons) with ub <= 0...', len(ub))
#
#             map = np.argwhere(flatten_ub <= 0)
#             map1 = np.array([])
#             for i in range(len(map)):
# index = map[i][1] * len(flatten_ub[0]) + map[0][i]
#                 index = map[i][1]
#                 map1 = np.append(map1, index)
#
#             if dis_opt == 'display':
#                 print('\n%d neurons with ub <= 0 are found by estimating ranges', len(map1))
#
#             map = np.argwhere(flatten_lb < 0)
#             lb_map = np.array([])
#             for i in range(len(map)):
# index = map[i][1] * len(flatten_lb[0]) + map[0][i]
#                 index = map[i][1]
#                 lb_map = np.append(lb_map, index)
#
#             map = np.argwhere(flatten_ub > 0)
#             ub_map = np.array([])
#             for i in range(len(map)):
# index = map[i][1] * len(flatten_ub[0]) + map[0][i]
#                 index = map[i][1]
#                 ub_map = np.append(ub_map, index)
#
#             map2 = np.intersect1d([lb_map], [ub_map])
#
#             if dis_opt == 'display':
#                 print('\nFinding neurons (in %d neurons) with ub <= 0 by optimizing ranges: ', len(map2))
#
#             xmax = I.getMaxs(map2, option, dis_opt, lp_solver)
#             flatten_xmax = np.ndarray.flatten(xmax, 'F')
#             map = np.argwhere(flatten_xmax <= 0)
#             map3 = np.array([])
#             for i in range(len(map)):
# index = map[i][1] * len(flatten_xmax[0]) + map[0][i]
#                 index = map[i][1]
#                 map3 = np.append(map3, index)
#
#             if dis_opt == 'display':
#                 print('\n%d neurons (in %d neurons) with ub <= 0 are found by optimizing ranges', len(map3), len(map2))
#
#             n = len(map3)
#             map4 = np.zeros([n, 1])
#             for i in range (n):
#                 map4[i] = map2[map3[i]]
#
#             map11 = np.vstack([map1, map4])
#             In = I.resetRow(map11) # reset to zero at the element having ub <= 0, need to add resetRow func in star
#             if dis_opt == 'display':
#                 print('\n(%d+%d =%d)/%d neurons have ub <= 0', len(map1), len(map3), len(map11), len(ub))
#
#             # find all indexes that have lb < 0 & ub > 0, then
#             # apply the over-approximation rule for ReLU
#
#             if dis_opt == 'display':
#                 print("\nFinding all neurons (in %d neurons) with lb < 0 & ub >0: ", len(ub))
#
#             map = np.argwhere(flatten_xmax > 0)
#             map5 = np.array([])
#             for i in range(len(map)):
# index = map[i][1] * len(flatten_xmax[0]) + map[0][i]
#                 index = map[i][1]
#                 map5 = np.append(map5, index)
#
#             map6 = map2[map5[:]] # all indexes having ub > 0
#             xmax1 = xmax[map5[:]] # upper bound of all neurons having ub > 0
#
#             xmin = I.getMins(map6, option, dis_opt, lp_solver)
#             flatten_xmin = np.ndarray.flatten(xmin, 'F')
#             map = np.argwhere(flatten_xmin < 0)
#             map7 = np.array([])
#             for i in range(len(map)):
# index = map[i][1] * len(flatten_xmin[0]) + map[0][i]
#                 index = map[i][1]
#                 map7 = np.append(map7, index)
#
#             map8 = map6[map7[:]] # all indexes habing lb < 0 & ub > 0
#             lb1 = xmin[map7[:]] # lower bound of all indexes having lb < 0 & ub > 0
#             ub1 = xmax1[map7[:]] # upper bound of all neurons having lb < 0 & ub > 0
#
#             if dis_opt == 'display':
#                 print('\n%d/%d neurons have lb < 0 & ub > 0', len(map8), len(ub))
#                 print('\nConstruct new star set, %d new predicate variables are introduced', len(map8))
#
#             S = PosLin.multipleStepReachStarApprox_at_one(In, map8, lb1, ub1) # one-shot approximation
#             return S
