from typing import List, Tuple, Dict, Union, Optional
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.tools.parallel import parallel_map
from qiskit.transpiler.passes import ApplyLayout
from qiskit.dagcircuit import DAGCircuit
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit.compiler import transpile

from docs.multi_pm import multi_tasking_pass_manager


def multitasking_transpile(multi_circuits: Union[QuantumCircuit, List[QuantumCircuit]],
                           backend=None,
                           backend_properties=None,
                           output_names=None,
                           layout_method: Optional[str] = None,
                           pass_manager=None,
                           ) -> Union[QuantumCircuit, List[QuantumCircuit]]:
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

    if layout_method == 'crosstalk':
        if output_names is not None:
            output_names = _perse_output_names(
                output_names, len(multi_circuits))
        circuits = []
        for i, circuit in enumerate(multi_programming_circuit):
            pass_manager = multi_tasking_pass_manager(transpile_a)
            dag = circuit_to_dag(circuit)
            new_dag = pass_manager.run(dag)
            circuits.append(dag_to_circuit(new_dag))

        # transpiled_circuits = list(map())
        if len(circuits) == 1:
            return circuits[0]
        return circuits

    transpiled_circuit = transpile(
        circuits=multi_programming_circuit,
        backend=backend,
        backend_properties=backend_properties,
        optimization_level=3
    )
    if len(transpiled_circuit) == 1:
        return transpiled_circuit[0]
    return transpiled_circuit


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
    name_list = []
    bit_counter = 0
    dag_list = [circuit_to_dag(circuit) for circuit in circuits]
    return dag_to_circuit(_compose_dag(dag_list))


def _compose_dag(dag_list):
    """Compose each dag and return new multitask dag"""

    """FIXME 下記と同様
    # name_list = []
    """
    bit_counter = 0
    composed_multidag = DAGCircuit()
    for i, dag in enumerate(dag_list):
        register_size = dag.num_qubits()
        """FIXME
        Problem:
            register_name: register nameを定義すると、outputの `new_dag` に対して `dag_to_circuit()`
            を実行した時、
            qiskit.circuit.exceptions.CircuitError: 'register name "定義した名前" already exists'
            が発生するため、任意のレジスター名をつけることができない

        Code:
            reg_name_tmp = dag.qubits[0].register.name
            register_name = reg_name_tmp if (reg_name_tmp not in name_list) and (
                not reg_name_tmp == 'q') else None
            name_list.append(register_name)
        """
        # 上記FIXME部分はNoneで対応中: 2020 / 08 / 16
        register_name = None
        ########################

        qr = QuantumRegister(size=register_size, name=register_name)
        cr = ClassicalRegister(size=register_size, name=register_name)
        composed_multidag.add_qreg(qr)
        composed_multidag.add_creg(cr)
        qubits = composed_multidag.qubits[bit_counter:bit_counter+register_size]
        clbits = composed_multidag.clbits[bit_counter:bit_counter+register_size]
        composed_multidag.compose(dag, qubits=qubits, clbits=clbits)

        bit_counter += register_size
    return composed_multidag


def _parse_combine_args(multi_circuits, backend, backend_propaerties, output_names) -> List[Dict]:
    #
    # number of circuits. If single, duplicate to create a list of that size.
    num_circuits = len(multi_circuits)

    backend_properties = _parse_backend_properties(
        backend_propaerties, backend, num_circuits)
    output_names = _perse_output_names(output_names, num_circuits)

    list_combine_args = []
    for args in zip(backend_properties, output_names):
        combine_args = {'output_name': args[1],
                        }
        """これから増やす
            'coupling_map': args[?],
            'initial_layout': args[?],
        ...
        """
        list_combine_args.append(combine_args)

    return list_combine_args


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
        if num_circuits != 1 and not isinstance(output_names, None):
            output_names = [str(output_names)+"_" +
                            str(i) for i in range(num_circuits)]
        else:
            output_names = [None] * num_circuits
    return output_names


def _split_inputcircuits(multi_circuits):
    """
    """
    multi_circuits = multi_circuits
    return multi_circuits
