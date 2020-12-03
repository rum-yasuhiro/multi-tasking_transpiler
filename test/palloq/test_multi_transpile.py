from qiskit import QuantumCircuit
from qiskit.circuit.random import random_circuit
from palloq.compiler.multi_transpile import multi_transpile

def test_multi_transpile(small_circuits):
    circuit_list = small_circuits[:2]
    qc = multi_transpile(circuit_list)

    assert isinstance(qc, QuantumCircuit)