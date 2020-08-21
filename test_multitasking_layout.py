from datetime import datetime
from pprint import pprint

from qiskit.compiler import transpile
from qiskit.circuit.random import random_circuit
from qiskit import QuantumCircuit, IBMQ
from qiskit.providers.models import BackendProperties
from qiskit.providers.models.backendproperties import Nduv, Gate

from docs.multi_tasking import multitasking_compose, _parse_combine_args, _parse_backend_properties, _compose_multicircuits
from docs.passes.crosstalk_adaptive_layout import CrosstalkAdaptiveMultiLayout


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


def test_parse_backend_properties():
    # Make random circuits
    circuits = [random_circuit(2, 2, measure=True) for _ in range(10)]

    # get ibmq backend
    IBMQ.load_account()
    provider = IBMQ.get_provider(
        hub='ibm-q-keio', group='keio-internal', project='keio-students')
    backend = provider.backends.ibmq_toronto

    # combine circuits
    backend_properties = _parse_backend_properties(
        backend_properties=None, backend=backend, num_circuits=1)

    return backend_properties


def test_parse_combine_args():
    # Make random circuits
    circuits = [random_circuit(2, 2, measure=True) for _ in range(10)]

    # get ibmq backend
    IBMQ.load_account()
    provider = IBMQ.get_provider(
        hub='ibm-q-keio', group='keio-internal', project='keio-students')
    backend = provider.backends.ibmq_toronto

    # combine circuits
    args = _parse_combine_args(
        multi_circuits=circuits, backend=backend, backend_propaerties=None,  output_names="test1")

    return args


def test_compose_multicircuits():
    circuits = [random_circuit(2, 2, measure=True) for _ in range(10)]
    config = {'num_qubit': 20, 'output_name': None}
    circuit_config_tuple = (circuits, config)
    multitask_circuit = _compose_multicircuits(circuit_config_tuple)

    return multitask_circuit


def test_simple_multicircuits():
    # Make random circuits
    circuits = [random_circuit(2, 2, measure=True) for _ in range(10)]

    # get ibmq backend
    IBMQ.load_account()
    provider = IBMQ.get_provider(
        hub='ibm-q-keio', group='keio-internal', project='keio-students')
    backend = provider.backends.ibmq_toronto

    # combine circuits
    multi_programming_circuit = multitasking_compose(
        multi_circuits=circuits, backend=backend, output_names="test1")

    if isinstance(multi_programming_circuit, list):
        for circ in multi_programming_circuit:
            print("################## "+circ.name+" ##################")
            print(circ)
    else:
        print("################## " +
              multi_programming_circuit.name+" ##################")
        print(multi_programming_circuit)


def test_noiseadaptive_multitask_layout():
    IBMQ.load_account()
    provider = IBMQ.get_provider(
        hub='ibm-q-keio', group='keio-internal', project='keio-students')
    backend = provider.backends.ibmq_toronto

    calib_time = datetime(year=2020, month=8, day=1,
                          hour=0, minute=0, second=0)
    # qubit_list = []
    # ro_errors = [0.01]*6
    # for ro_error in ro_errors:
    #     qubit_list.append(make_qubit_with_error(ro_error))
    # p01 = [Nduv(date=calib_time, name='gate_error', unit='', value=0.3)]
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

    # bprop = BackendProperties(
    #     last_update_date=calib_time, backend_name="test_backend",
    #     qubits=qubit_list, backend_version="1.0.0", gates=gate_list,
    #     general=[])

    bprop = backend.properties(datetime=calib_time)

    layout_pass = CrosstalkAdaptiveMultiLayout(bprop)

    circ_list = [
        random_circuit(1, 2, measure=True),
        random_circuit(3, 5, measure=True),
        random_circuit(2, 3, measure=True),
    ]
    circ_list = decompose_to_base_gates(circ_list)

    # combine circuits
    multi_programming_circuit = multitasking_compose(
        multi_circuits=circ_list, layout_method=layout_pass)

    if isinstance(multi_programming_circuit, list):
        for circ in multi_programming_circuit:
            print("################## "+circ.name+" ##################")
            print(circ)
    else:
        print("################## " +
              multi_programming_circuit.name+" ##################")
        print(multi_programming_circuit)
        pprint(layout_pass.property_set['layout'])


if __name__ == "__main__":

    # test_simple_multicircuits()
    test_noiseadaptive_multitask_layout()
