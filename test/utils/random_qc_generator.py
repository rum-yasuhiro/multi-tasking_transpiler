from typing import List, Tuple, Union, Optional
import random
from qiskit.circuit.random import random_circuit


class RandomCircuitGenerator:
    def __init__(self, seed=0):
        self.seed = seed

    def generate(
        self,
        num_multi_circ: int,
        num_circ: Union[int, List[int]],
        circ_size: Optional[
            Union[Tuple[int], List[Tuple[int]], List[List[Tuple[int]]]]
        ] = None,
        seed: Optional[Union[int, List[int], List[List[int]]]] = None,
    ):
        """
        Args:
            num_multi_circ : number of multi-tasking circuit you want to make
            num_circ       : The number of circuits containd in the multi-tasking circuit
            circ_size      : width and depth of random circuit [w, d]
            random_seed    : seed to make random circuit
        Return:
            The list of multi-circuit set or just single multi-circuit set
            multi-circuit set: the list of qc to make multi-tasking circuit
        """
        multi_circuits_list = []
        num_circ_list = self.parse_num_circ(num_circ)
        circ_size = self.parse_circ_size(circ_size, num_circ_list)
        seed_list_list = self.parse_seed(seed, num_circ_list)

        for mqc_id, num_circ in enumerate(num_circ_list):
            rand_qc_list = []
            for qc_id in range(num_circ):
                width = circ_size[mqc_id][qc_id][0]
                depth = circ_size[mqc_id][qc_id][1]
                seed = seed_list_list[mqc_id][qc_id]
                rand_qc = random_circuit(width, depth, measure=True, seed=seed)
                rand_qc_list.append(rand_qc)
            multi_circuits_list.append(rand_qc_list)

        if num_multi_circ == 1:
            return multi_circuits_list[0]

        return multi_circuits_list

    def parse_num_circ(self, num_circ):
        if isinstance(num_circ, int):
            return [num_circ]
        elif isinstance(num_circ[0], int):
            return num_circ
        raise NumCircTypeError("type of num_circ is wrong: Only int or List[int]")

    def parse_circ_size(self, circ_size, num_circ_list):
        if circ_size is None:
            random.seed(self.seed)
            circ_size_list_list = []
            for num_circ in num_circ_list:
                circ_size_list = []
                for qc_id in range(num_circ):
                    circ_size = (random.randint(2, 5), random.randint(1, 15))
                    circ_size_list.append(circ_size)
                circ_size_list_list.append(circ_size_list)
            return circ_size_list_list

        if isinstance(circ_size, tuple):
            return [[circ_size]]
        elif isinstance(circ_size[0], tuple):
            return [circ_size]
        elif isinstance(circ_size[0][0], tuple):
            return circ_size
        raise NumCircTypeError(
            "type of circ_size is wrong: Only Tuple[int],List[Tuple[int]], or List[List[Tuple[int]]]"
        )

    def parse_seed(self, seed, num_circ_list):
        if seed is None:
            return [
                [self.seed for qc_id in range(num_circ)] for num_circ in num_circ_list
            ]

        if isinstance(seed, int):
            return [[seed]]
        elif isinstance(seed[0], int):
            return [seed]
        elif isinstance(seed[0][0], int):
            return seed
        raise SeedTypeError(
            "type of seed is wrong: Only int or List[int] or List[List[int]]"
        )


class NumCircTypeError(Exception):
    pass


class SizeCircTypeError(Exception):
    pass


class SeedTypeError(Exception):
    pass