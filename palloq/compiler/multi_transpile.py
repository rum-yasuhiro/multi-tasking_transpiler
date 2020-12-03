# 2020/12/3
# qiskit version: 0.23.1
# 

"""Multi Circuits transpile function"""
import logging
import warnings
from time import time
from typing import List, Union, Dict, Callable, Any, Optional, Tuple

from qiskit import user_config
from qiskit.circuit.quantumcircuit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.circuit.quantumregister import Qubit
from qiskit.converters import isinstanceint, isinstancelist, dag_to_circuit, circuit_to_dag
from qiskit.dagcircuit import DAGCircuit
from qiskit.providers import BaseBackend
from qiskit.providers.backend import Backend
from qiskit.providers.models import BackendProperties
from qiskit.providers.models.backendproperties import Gate
from qiskit.pulse import Schedule
from qiskit.tools.parallel import parallel_map
from qiskit.transpiler import Layout, CouplingMap, PropertySet, PassManager
from qiskit.transpiler.basepasses import BasePass
from qiskit.transpiler.exceptions import TranspilerError
from qiskit.transpiler.instruction_durations import InstructionDurations, InstructionDurationsType
from qiskit.transpiler.passes import ApplyLayout
from qiskit.transpiler.passmanager_config import PassManagerConfig
from qiskit.transpiler.preset_passmanagers import (level_0_pass_manager,
                                                   level_1_pass_manager,
                                                   level_2_pass_manager,
                                                   level_3_pass_manager)

from qiskit.compiler import transpile
# from palloq.transpiler.preset_passmanagers.multi_pm import multi_tasking_pass_manager
from palloq import multi_pass_manager

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def multi_transpile(circuits: Union[List[QuantumCircuit], List[List[QuantumCircuit]]],
              backend: Optional[Union[Backend, BaseBackend]] = None,
              basis_gates: Optional[List[str]] = None,
              coupling_map: Optional[Union[CouplingMap, List[List[int]]]] = None,
              backend_properties: Optional[BackendProperties] = None,
              initial_layout: Optional[Union[Layout, Dict, List]] = None,
              layout_method: Optional[str] = None,
              routing_method: Optional[str] = None,
              translation_method: Optional[str] = None,
              scheduling_method: Optional[str] = None,
              instruction_durations: Optional[InstructionDurationsType] = None,
              dt: Optional[float] = None,
              seed_transpiler: Optional[int] = None,
              optimization_level: Optional[int] = None,
              pass_manager: Optional[PassManager] = None,
              callback: Optional[Callable[[BasePass, DAGCircuit, float,
                                           PropertySet, int], Any]] = None,
              output_name: Optional[Union[str, List[str]]] = None, 
              crosstalk_prop: Optional[Dict[Tuple[int], Dict[Tuple[int], int]]] = None) -> Union[QuantumCircuit,
                                                                            List[QuantumCircuit]]:
    """Mapping several circuits to single circuit based on calibration for the backend

    Args:
        circuits: Small circuits to compose one big circuit(s)
        backend:
        backend_properties:
        output_name: the name of output circuit. str or List[str]

    Returns:
        composed multitasking circuit(s)..
    """
    circuits = circuits if isinstance(circuits[0], list) else [circuits]
    output_name = output_name if isinstance(output_name, list) else [output_name] * len(circuits)

    # combine circuits in parallel
    multi_circuit_list = list(
        map(_compose_multicircuits, circuits, output_name)
    )

    pass_manager_config = PassManagerConfig(basis_gates,
                                            coupling_map,
                                            backend_properties,
                                            initial_layout,
                                            layout_method,
                                            routing_method,
                                            translation_method,
                                            scheduling_method,
                                            instruction_durations,
                                            seed_transpiler)

    # define pass manager
    if pass_manager: 
        pass
    elif crosstalk_prop:
        pass_manager = multi_pass_manager(pass_manager_config, crosstalk_prop)
        logger.info("############## xtalk-adaptive multi transpile ##############")
    elif optimization_level:
        if optimization_level==0: 
            pass_manager = level_0_pass_manager(pass_manager_config)
        elif optimization_level==1: 
            pass_manager = level_1_pass_manager(pass_manager_config)
        elif optimization_level==2: 
            pass_manager = level_2_pass_manager(pass_manager_config)
        elif optimization_level==3: 
            pass_manager = level_3_pass_manager(pass_manager_config)
        logger.info("############## qiskit transpile optimization level "+str(optimization_level)+" ##############")
    else:
        pass_manager = multi_pass_manager(pass_manager_config)
        logger.info("############## multi transpile ##############")

    # transpile multi_circuit(s)
    multi_programming_circuit = transpile(
                                multi_circuit_list, backend, basis_gates, coupling_map, backend_properties, 
                                initial_layout, layout_method, routing_method, translation_method, 
                                scheduling_method, instruction_durations, dt, seed_transpiler, 
                                optimization_level, pass_manager, callback, output_name, 
                                )

    if len(multi_programming_circuit) == 1:
        return multi_programming_circuit[0]
    return multi_programming_circuit


def _compose_multicircuits(circuits: List[QuantumCircuit], output_name) -> QuantumCircuit:

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
    qubit_counter = 0
    clbit_counter = 0
    composed_multidag = DAGCircuit()
    for i, dag in enumerate(dag_list):
        num_qubits = dag.num_qubits()
        num_clbits = dag.num_clbits()
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

        qr = QuantumRegister(size=num_qubits, name=register_name)
        composed_multidag.add_qreg(qr)
        qubits = composed_multidag.qubits[qubit_counter : qubit_counter + num_qubits]

        if num_clbits > 0: 
            cr = ClassicalRegister(size=num_clbits, name=register_name)
            composed_multidag.add_creg(cr)
            clbits = composed_multidag.clbits[clbit_counter : clbit_counter + num_clbits]

            composed_multidag.compose(dag, qubits=qubits, clbits=clbits)
        else: 
            composed_multidag.compose(dag, qubits=qubits)

        qubit_counter += num_qubits
        clbit_counter += num_clbits
    return composed_multidag

if __name__ == "__main__": 
    pass