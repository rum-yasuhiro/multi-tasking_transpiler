from qiskit.circuit import QuantumCircuit, QuantumRegister
from qiskit.compiler import transpile
from qiskit.transpiler import Layout, InstructionDurations
from qiskit.converters import circuit_to_dag, dag_to_circuit

from palloq.transpiler.passes import MultiALAPSchedule

import logging
logger = logging.getLogger(__name__)

def test_multi_alap(): 
    qr0 = QuantumRegister(2)
    qr1 = QuantumRegister(2)
    qc = QuantumCircuit(qr0, qr1)

    qc.cx(qr0[0], qr0[1])

    qc.cx(qr1[0], qr1[1])
    qc.cx(qr1[1], qr1[0])
    qc.cx(qr1[0], qr1[1])

    qc.measure_all()


    layout = Layout({
                    qr0[0]: 0,
                    qr0[1]: 1,
                    qr1[0]: 2,
                    qr1[1]: 3,
                    })
    durations = InstructionDurations([('cx', None, 1000), ('measure', None, 1000)])

    transpiled_qc = transpile(qc, initial_layout=layout)
    dag = circuit_to_dag(transpiled_qc)
    
    malap_dag = MultiALAPSchedule(durations).run(dag, time_unit="dt")

    print(dag_to_circuit(malap_dag))
    assert(malap_dag.duration == 4000)