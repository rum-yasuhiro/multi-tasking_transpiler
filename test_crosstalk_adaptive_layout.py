from docs.passes.layout.crosstalk_adaptive_layout import CrosstalkAdaptiveMultiLayout

from datetime import datetime
import unittest
from qiskit.transpiler.passes import NoiseAdaptiveLayout
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit import QuantumRegister, QuantumCircuit, ClassicalRegister
from qiskit.test import QiskitTestCase
from qiskit.providers.models import BackendProperties
from qiskit.providers.models.backendproperties import Nduv, Gate
from qiskit.circuit.random import random_circuit

from pprint import pprint


def make_qubit_with_error(readout_error):
    """Create a qubit for BackendProperties"""
    calib_time = datetime(year=2019, month=2, day=1,
                          hour=0, minute=0, second=0)
    return [Nduv(name="T1", date=calib_time, unit="µs", value=100.0),
            Nduv(name="T2", date=calib_time, unit="µs", value=100.0),
            Nduv(name="frequency", date=calib_time, unit="GHz", value=5.0),
            Nduv(name="readout_error", date=calib_time, unit="", value=readout_error)]


def test_initialize_backend_prop():

    circ_list = [random_circuit(2, 2) for _ in range(10)]
    dag_list = [circuit_to_dag(circ) for circ in circ_list]

    calib_time = datetime(year=2019, month=2, day=1,
                          hour=0, minute=0, second=0)
    qubit_list = []
    ro_errors = [0.01, 0.01, 0.01]
    for ro_error in ro_errors:
        qubit_list.append(make_qubit_with_error(ro_error))
    p01 = [Nduv(date=calib_time, name='gate_error', unit='', value=0.9)]
    g01 = Gate(name="CX0_1", gate="cx", parameters=p01, qubits=[0, 1])
    p12 = [Nduv(date=calib_time, name='gate_error', unit='', value=0.1)]
    g12 = Gate(name="CX1_2", gate="cx", parameters=p12, qubits=[1, 2])
    gate_list = [g01, g12]

    bprop = BackendProperties(last_update_date=calib_time, backend_name="test_backend",
                              qubits=qubit_list, backend_version="1.0.0", gates=gate_list,
                              general=[])

    caml = CrosstalkAdaptiveMultiLayout(bprop)
    caml._initialize_backend_prop()


"""""""""""""""""""""""""""
def test_crosstalk_backend_prop():

    circ_list = [random_circuit(2, 2) for _ in range(10)]
    dag_list = [circuit_to_dag(circ) for circ in circ_list]

    calib_time = datetime(year=2019, month=2, day=1,
                          hour=0, minute=0, second=0)
    qubit_list = []
    ro_errors = [0.01, 0.01, 0.01]
    for ro_error in ro_errors:
        qubit_list.append(make_qubit_with_error(ro_error))
    p01 = [Nduv(date=calib_time, name='gate_error', unit='', value=0.9)]
    g01 = Gate(name="CX0_1", gate="cx", parameters=p01, qubits=[0, 1])
    p12 = [Nduv(date=calib_time, name='gate_error', unit='', value=0.1)]
    g12 = Gate(name="CX1_2", gate="cx", parameters=p12, qubits=[1, 2])
    gate_list = [g01, g12]

    bprop = BackendProperties(last_update_date=calib_time, backend_name="test_backend",
                              qubits=qubit_list, backend_version="1.0.0", gates=gate_list,
                              general=[])
    xtalk_prop = {(0, 1): {(1, 2): 3}, (3, 4): {(2, 3): 3}}
    caml = CrosstalkAdaptiveMultiLayout(bprop, crosstalk_prop=xtalk_prop)
    caml._initialize_backend_prop()
    gate_reliab, crosstalk = caml._crosstalk_backend_prop()
    pprint(gate_reliab)
    pprint(crosstalk)
"""""""""""""""""""""""""""""""""


def test_create_program_graphs():

    circ_list = [random_circuit(2, 2), random_circuit(
        4, 4), random_circuit(3, 3), random_circuit(5, 5)]
    dag_list = [circuit_to_dag(circ) for circ in circ_list]

    calib_time = datetime(year=2019, month=2, day=1,
                          hour=0, minute=0, second=0)
    qubit_list = []
    ro_errors = [0.01, 0.01, 0.01]
    for ro_error in ro_errors:
        qubit_list.append(make_qubit_with_error(ro_error))
    p01 = [Nduv(date=calib_time, name='gate_error', unit='', value=0.9)]
    g01 = Gate(name="CX0_1", gate="cx", parameters=p01, qubits=[0, 1])
    p12 = [Nduv(date=calib_time, name='gate_error', unit='', value=0.1)]
    g12 = Gate(name="CX1_2", gate="cx", parameters=p12, qubits=[1, 2])
    gate_list = [g01, g12]

    bprop = BackendProperties(last_update_date=calib_time, backend_name="test_backend",
                              qubits=qubit_list, backend_version="1.0.0", gates=gate_list,
                              general=[])

    caml = CrosstalkAdaptiveMultiLayout(bprop)
    num_q, prog_list, new_dag_list = caml._create_program_graphs(dag_list)
    print(num_q)
    print(prog_list)
    for dag in new_dag_list:
        new_circ = dag_to_circuit(dag)
        print(new_circ)


def test_compose_dag():

    circ_list = [random_circuit(2, 2, measure=True), random_circuit(
        4, 4, measure=True), random_circuit(3, 3, measure=True), random_circuit(5, 5, measure=True)]
    dag_list = [circuit_to_dag(circ) for circ in circ_list]

    calib_time = datetime(year=2019, month=2, day=1,
                          hour=0, minute=0, second=0)
    qubit_list = []
    ro_errors = [0.01, 0.01, 0.01]
    for ro_error in ro_errors:
        qubit_list.append(make_qubit_with_error(ro_error))
    p01 = [Nduv(date=calib_time, name='gate_error', unit='', value=0.9)]
    g01 = Gate(name="CX0_1", gate="cx", parameters=p01, qubits=[0, 1])
    p12 = [Nduv(date=calib_time, name='gate_error', unit='', value=0.1)]
    g12 = Gate(name="CX1_2", gate="cx", parameters=p12, qubits=[1, 2])
    gate_list = [g01, g12]

    bprop = BackendProperties(last_update_date=calib_time, backend_name="test_backend",
                              qubits=qubit_list, backend_version="1.0.0", gates=gate_list,
                              general=[])

    caml = CrosstalkAdaptiveMultiLayout(bprop)
    new_dag = caml._compose_dag(dag_list)
    print(new_dag.qubits)
    # new_dag.draw()
    new_circ = dag_to_circuit(new_dag)
    print(new_circ)


def test_run():

    circ_list = [random_circuit(2, 2), random_circuit(
        4, 4), random_circuit(3, 3), random_circuit(5, 5)]
    dag_list = [circuit_to_dag(circ) for circ in circ_list]

    calib_time = datetime(year=2019, month=2, day=1,
                          hour=0, minute=0, second=0)
    qubit_list = []
    ro_errors = [0.01, 0.01, 0.01]
    for ro_error in ro_errors:
        qubit_list.append(make_qubit_with_error(ro_error))
    p01 = [Nduv(date=calib_time, name='gate_error', unit='', value=0.9)]
    g01 = Gate(name="CX0_1", gate="cx", parameters=p01, qubits=[0, 1])
    p12 = [Nduv(date=calib_time, name='gate_error', unit='', value=0.1)]
    g12 = Gate(name="CX1_2", gate="cx", parameters=p12, qubits=[1, 2])
    gate_list = [g01, g12]

    bprop = BackendProperties(last_update_date=calib_time, backend_name="test_backend",
                              qubits=qubit_list, backend_version="1.0.0", gates=gate_list,
                              general=[])

    caml = CrosstalkAdaptiveMultiLayout(bprop)
    # xtalk_prop = {(0, 1): {(1, 2): 3}, (3, 4): {(2, 3): 3}}
    # caml = CrosstalkAdaptiveMultiLayout(bprop, crosstalk_prop=xtalk_prop)
    new_dag_list = caml.run(dag_list)

    for dag in new_dag_list:
        new_circ = dag_to_circuit(dag)
        print(new_circ)


if __name__ == "__main__":
    # test_initialize_backend_prop()
    """
    test_crosstalk_backend_prop()
    """
    # test_create_program_graphs()
    test_compose_dag()
    # test_run()
