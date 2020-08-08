from typing import List, Tuple, Dict, Union, Optional
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.tools.parallel import parallel_map


def multitasking_layout(multi_circuits: Union[QuantumCircuit, List[QuantumCircuit]],
                        backend=None,
                        backend_properties=None,
                        output_names=None,
                        ):
    """Mapping several circuits to single circuit based on calibration for the backend

    Args:
        multi_circuits: Small circuits to compose one big circuit(s)
        backend: 
        backend_properties: 
        output_names: the name of output circuit. str or List[str]

    Returns:
        composed multitasking circuit(s).
    """
    multi_circuits = multi_circuits if isinstance(
        multi_circuits[0], list) else [multi_circuits]

    # Get combine_args(mp_args) to configure the circuit combine job(s)
    combine_args = _parse_combine_args(
        multi_circuits, backend, backend_properties, output_names)

    # combine circuits in parallel
    multi_programming_circuit = list(map(
        _compose_multicircuits, list(zip(multi_circuits, combine_args))))

    if len(multi_programming_circuit) == 1:
        return multi_programming_circuit[0]
    return multi_programming_circuit


def _compose_multicircuits(circuit_config_tuple: Tuple[List[QuantumCircuit], Dict]) -> QuantumCircuit:
    circuits, combine_args = circuit_config_tuple

    # num_qubit = combine_args['num_qubit']
    output_name = combine_args['output_name']

    """FIXME!
    入力の量子回路の量子ビット数合計がbackendの量子ビット数を超える場合のErrorを作る
    
        if sum([circuit.num_qubit for circuit in circuits]) > num_qubit:
            raise
    """

    composed_multicircuit = QuantumCircuit(name=output_name)
    qubit_counter = 0
    for circuit in circuits:
        circuit.remove_final_measurements()
        register_size = circuit.num_qubits
        register_name = None
        """FIXME!
        量子回路の名前が同一だと、エラーを吐くので、
        同一の場合のexecptionを作る

            register_name = circuit.qubits[0].register.name    
        """
        qr = QuantumRegister(size=register_size, name=register_name)
        # add register and combine circuit
        composed_multicircuit.add_register(qr)
        qubits = composed_multicircuit.qubits[qubit_counter:qubit_counter+register_size]
        composed_multicircuit = composed_multicircuit.compose(
            circuit, qubits=qubits)
        # add classical bits and measurement
        cr = ClassicalRegister(size=register_size, name=register_name)
        composed_multicircuit.add_register(cr)
        composed_multicircuit.measure(qr, cr)

        qubit_counter += register_size

    return composed_multicircuit


def _parse_combine_args(multi_circuits, backend, backend_propaerties, output_names) -> List[Dict]:
    #
    # number of circuits. If single, duplicate to create a list of that size.
    num_circuits = len(multi_circuits)

    backend_properties = _parse_backend_properties(
        backend_propaerties, backend, num_circuits)
    output_names = _perse_output_names(output_names, num_circuits)

    combine_args = []
    for args in zip(backend_properties, output_names):
        arg_dict = {'num_qubit': len(args[0]['qubits']),
                    'output_name': args[1],
                    }
        """これから増やす
            'coupling_map': args[?],
            'initial_layout': args[?],
        ... 
        """
        combine_args.append(arg_dict)

    return combine_args


def _parse_backend_properties(backend_properties, backend, num_circuits):
    # try getting backend_properties from user, else backend
    if backend_properties is None:
        if getattr(backend, 'properties', None):
            backend_properties = backend.properties().to_dict()
    if not isinstance(backend_properties, list):
        backend_properties = [backend_properties] * num_circuits
    return backend_properties


def _perse_output_names(output_names, num_circuits):
    # try getting backend_properties from user, else return None
    if output_names is None:
        output_names = [None] * num_circuits
    if output_names is not list:
        output_names = [output_names+"_"+str(i) for i in range(num_circuits)]
    return output_names


def _split_inputcircuits(multi_circuits):
    """
    """
    multi_circuits = multi_circuits
    return multi_circuits
