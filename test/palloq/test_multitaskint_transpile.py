from typing import List, Union

from qiskit import BasicAer
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.test import QiskitTestCase
from palloq.compiler import multitasking_transpile


def qc_list_gen(num_multi_circ, num_circ: Union[int, List[int], random_seed=None]):
    for _ in num_multi_circ:
        for _ in num_circ:

    return multi_circuits_list


def fake_backend():

    return backend_properties


class TestMultiTranspile(QiskitTestCase):
    """test multitasking_transpile function"""

    def test_qiskit_pass_manager():
        multi_qc_list = qc_list_gen()
        backend = BasicAer.get_backend("qasm_simulator")
        multi_circuit = multitasking_transpile(
            multi_qc_list, backend, optimization_level=3
        )


if __name__ == "__main__":

    TestMultiTranspile.test_qiskit_pass_manager()
