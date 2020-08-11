from qiskit.circuit.random import random_circuit
from qiskit import QuantumCircuit, IBMQ
from docs.passes.multi_tasking import multitasking_compose, _parse_combine_args, _parse_backend_properties, _compose_multicircuits


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
    config = {'num_qubit': 27, 'output_name': None}
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

    return multi_programming_circuit


if __name__ == "__main__":

    circuits = test_simple_multicircuits()
    print(circuits)
    print(circuits.name)
