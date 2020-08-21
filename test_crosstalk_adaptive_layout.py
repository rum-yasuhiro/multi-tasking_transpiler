from docs.passes.crosstalk_adaptive_layout import CrosstalkAdaptiveMultiLayout

from datetime import datetime
import unittest
from qiskit.compiler import transpile
from qiskit.transpiler.layout import Layout
from qiskit.transpiler.passes import NoiseAdaptiveLayout
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit import QuantumRegister, QuantumCircuit, ClassicalRegister, IBMQ
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


def decompose_to_base_gates(circ, initial_layout=None):
    basis_gates = ['u1', 'u2', 'u3', 'cx']
    IBMQ.load_account()
    provider = IBMQ.get_provider(
        hub='ibm-q-keio', group='keio-internal', project='keio-students')
    backend = provider.get_backend('ibmq_qasm_simulator')
    # backend = provider.get_backend('ibmq_toronto')
    transpiled_circ = transpile(
        circ, backend=backend, basis_gates=basis_gates, initial_layout=initial_layout, optimization_level=3)
    return transpiled_circ


def test_transpile():
    qcircuit = QuantumCircuit()
    qr0 = QuantumRegister(3)
    qr1 = QuantumRegister(2)
    qcircuit.add_register(qr0, qr1)
    qcircuit.ccx(qr0[0], qr0[1], qr0[2])
    qcircuit.cz(qr1[0], qr1[1])
    qcircuit = decompose_to_base_gates(qcircuit)
    print(qcircuit)


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

    circ_list = [random_circuit(2, 10, measure=True), random_circuit(
        4, 10, measure=True), random_circuit(3, 10, measure=True), random_circuit(5, 10, measure=True)]
    dag_list = [circuit_to_dag(circ) for circ in circ_list]

    caml = CrosstalkAdaptiveMultiLayout(bprop)
    num_q = caml._create_program_graphs(dag_list)
    print(num_q)
    heights = []
    for dag in caml.dag_list:
        height = dag.num_qubits()
        heights.append(height)
    print(heights)


def test_compose_dag():
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

    circ_list = [
        random_circuit(2, 2, measure=True),
        random_circuit(4, 4, measure=True),
        random_circuit(3, 3, measure=True),
        random_circuit(5, 5, measure=True),
    ]
    dag_list = [circuit_to_dag(circ) for circ in circ_list]

    caml = CrosstalkAdaptiveMultiLayout(bprop)
    new_dag = caml._compose_dag(dag_list)

    print("##################################")
    for dag in dag_list:
        for q in dag.qubits:
            qid = caml._qarg_to_id(q)
            print(qid)
    print("##################################")
    for new_q in new_dag.qubits:
        qid = caml._qarg_to_id(q)
        print(qid)

    new_circ = dag_to_circuit(new_dag)
    print(new_circ)


def test_run():

    # calib_time = datetime(year=2019, month=2, day=1,
    #                       hour=0, minute=0, second=0)
    # qubit_list = []
    # ro_errors = [0.01]*6
    # for ro_error in ro_errors:
    #     qubit_list.append(make_qubit_with_error(ro_error))
    # p01 = [Nduv(date=calib_time, name='gate_error', unit='', value=0.1)]
    # p03 = [Nduv(date=calib_time, name='gate_error', unit='', value=0.3)]
    # p12 = [Nduv(date=calib_time, name='gate_error', unit='', value=0.3)]
    # p14 = [Nduv(date=calib_time, name='gate_error', unit='', value=0.1)]
    # p34 = [Nduv(date=calib_time, name='gate_error', unit='', value=0.1)]
    # p45 = [Nduv(date=calib_time, name='gate_error', unit='', value=0.1)]
    # p25 = [Nduv(date=calib_time, name='gate_error', unit='', value=0.3)]
    # g01 = Gate(name="CX0_1", gate="cx", parameters=p01, qubits=[0, 1])
    # g03 = Gate(name="CX0_3", gate="cx", parameters=p03, qubits=[0, 3])
    # g12 = Gate(name="CX1_2", gate="cx", parameters=p12, qubits=[1, 2])
    # g14 = Gate(name="CX1_4", gate="cx", parameters=p14, qubits=[1, 4])
    # g34 = Gate(name="CX3_4", gate="cx", parameters=p34, qubits=[3, 4])
    # g45 = Gate(name="CX4_5", gate="cx", parameters=p45, qubits=[4, 5])
    # g25 = Gate(name="CX2_5", gate="cx", parameters=p25, qubits=[2, 5])
    # gate_list = [g01, g03, g12, g14, g34, g45, g25]
    # bprop = BackendProperties(
    #     last_update_date=calib_time, backend_name="test_backend",
    #     qubits=qubit_list, backend_version="1.0.0", gates=gate_list,
    #     general=[])

    IBMQ.load_account()
    provider = IBMQ.get_provider(
        hub='ibm-q-keio', group='keio-internal', project='keio-students')
    backend = provider.get_backend("ibmq_toronto")
    calib_time = datetime(year=2020, month=8, day=1,
                          hour=0, minute=0, second=0)
    bprop = backend.properties(datetime=calib_time)

    circ_list = [
        # random_circuit(1, 2, measure=True),
        random_circuit(3, 3, measure=True, seed=1),
        random_circuit(2, 3, measure=True, seed=1),
    ]
    circ_list = decompose_to_base_gates(circ_list)
    dag_list = [circuit_to_dag(circ) for circ in circ_list]

    caml = CrosstalkAdaptiveMultiLayout(bprop)
    new_dag = caml.run(dag_list)
    pprint(caml.property_set['layout'])
    new_circ = dag_to_circuit(new_dag)
    print(new_circ)


def test_run_with_Xtalk():

    calib_time = datetime(year=2019, month=2, day=1,
                          hour=0, minute=0, second=0)
    qubit_list = []
    ro_errors = [0.01]*6
    for ro_error in ro_errors:
        qubit_list.append(make_qubit_with_error(ro_error))
    p01 = [Nduv(date=calib_time, name='gate_error', unit='', value=0.1)]
    p03 = [Nduv(date=calib_time, name='gate_error', unit='', value=0.3)]
    p12 = [Nduv(date=calib_time, name='gate_error', unit='', value=0.3)]
    p14 = [Nduv(date=calib_time, name='gate_error', unit='', value=0.2)]
    p35 = [Nduv(date=calib_time, name='gate_error', unit='', value=0.3)]
    p45 = [Nduv(date=calib_time, name='gate_error', unit='', value=0.1)]
    p25 = [Nduv(date=calib_time, name='gate_error', unit='', value=0.1)]
    g01 = Gate(name="CX0_1", gate="cx", parameters=p01, qubits=[0, 1])
    g03 = Gate(name="CX0_3", gate="cx", parameters=p03, qubits=[0, 3])
    g12 = Gate(name="CX1_2", gate="cx", parameters=p12, qubits=[1, 2])
    g14 = Gate(name="CX1_4", gate="cx", parameters=p14, qubits=[1, 4])
    g35 = Gate(name="CX3_5", gate="cx", parameters=p35, qubits=[3, 5])
    g45 = Gate(name="CX4_5", gate="cx", parameters=p45, qubits=[4, 5])
    g25 = Gate(name="CX2_5", gate="cx", parameters=p25, qubits=[2, 5])
    gate_list = [g01, g03, g12, g14, g35, g45, g25]
    bprop = BackendProperties(
        last_update_date=calib_time, backend_name="test_backend",
        qubits=qubit_list, backend_version="1.0.0", gates=gate_list,
        general=[])
    xtalk_prop = {(2, 5): {(0, 1): 5},
                  (1, 0): {(2, 5): 5},
                  }

    circ_list = [
        # random_circuit(1, 2, measure=True),
        random_circuit(3, 3, measure=True, seed=1),
        random_circuit(2, 3, measure=True, seed=1),
    ]
    circ_list = decompose_to_base_gates(circ_list)
    dag_list = [circuit_to_dag(circ) for circ in circ_list]

    caml_noXtalk = CrosstalkAdaptiveMultiLayout(bprop)
    dag_noXtalk = caml_noXtalk.run(dag_list)
    # pprint(caml_noXtalk.property_set['layout'])
    circ_noXtalk = dag_to_circuit(dag_noXtalk)
    print(circ_noXtalk)

    caml_Xtalk = CrosstalkAdaptiveMultiLayout(bprop, crosstalk_prop=xtalk_prop)
    dag_Xtalk = caml_Xtalk.run(dag_list)
    # pprint(caml_Xtalk.property_set['layout'])
    circ_Xtalk = dag_to_circuit(dag_Xtalk)
    print(circ_Xtalk)


def layout_test():
    q0 = QuantumRegister(1, name='x')
    q1 = QuantumRegister(1, name='y')
    q2 = QuantumRegister(1, name='z')
    q3 = QuantumRegister(1, name='h')
    cr = ClassicalRegister(4)
    qc = QuantumCircuit(q0, q1, q2, q3, cr)
    qc.x(q0[0])
    qc.y(q1[0])
    qc.z(q2[0])
    qc.h(q3[0])
    qc.measure(q0, cr[0])
    # qc = random_circuit(4, 1, measure=True)
    print(qc)
    q = qc.qubits
    print(q)
    input_dict = {}
    input_dict[q0[0]] = 3
    input_dict[q1[0]] = 2
    input_dict[q2[0]] = 1
    input_dict[q3[0]] = 0
    # input_dict[q[0]] = 3
    # input_dict[q[1]] = 2
    # input_dict[q[2]] = 1
    # input_dict[q[3]] = 0
    layout = Layout(input_dict=input_dict)
    print(layout)
    qc._layout = layout
    print(qc)
    print(qc._layout)


if __name__ == "__main__":
    # test_initialize_backend_prop()
    """
    test_crosstalk_backend_prop()
    """
    # test_create_program_graphs()
    # test_compose_dag()
    test_run()
    # test_run_with_Xtalk()
    # layout_test()
    # test_transpile()
