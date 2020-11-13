from typing import List, Tuple, Union, Optional

from qiskit import BasicAer
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.test import QiskitTestCase

from test.utils.random_qc_generator import RandomCircuitGenerator
from palloq.compiler import multitasking_transpile

"""TODO
def fake_backend():

    return backend_properties
"""


class TestMultiTranspile(QiskitTestCase):
    """test multitasking_transpile function"""

    def test_qiskit_pass_manager(self):
        randqc = RandomCircuitGenerator()
        multi_qc_list = randqc.generate(num_multi_circ=1, num_circ=3)
        backend = BasicAer.get_backend("qasm_simulator")

        multi_circuit = multitasking_transpile(
            multi_qc_list, backend, optimization_level=3
        )
    
    def test_xtalkpass_with_non_xtalk:
        randqc = RandomCircuitGenerator()
        multi_qc_list = randqc.generate(num_multi_circ=1, num_circ=3)
        backend = BasicAer.get_backend("qasm_simulator")
        




if __name__ == "__main__":

    TestMultiTranspile.test_qiskit_pass_manager()
