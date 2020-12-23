from qiskit.circuit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.converters import circuit_to_dag
from palloq.transpiler.passes.layout.crosstalk_adaptive_layout import CrosstalkAdaptiveMultiLayout

def test_single_xtalk(fake_machine): 
    qr0 = QuantumRegister(2, 'qr0')
    qr1 = QuantumRegister(2, 'qr1')
    qc = QuantumCircuit(qr0, qr1)

    qc.cx(qr0[0], qr0[1])
    qc.cx(qr0[1], qr0[0])
    qc.cx(qr1[0], qr1[1])
    xtalk_prop = {(0, 1): {(2, 3): 2}}
    

    dag = circuit_to_dag(qc)
    pass_ = CrosstalkAdaptiveMultiLayout(fake_machine, xtalk_prop)
    pass_.run(dag)

    layout = pass_.property_set['layout']
    assert layout[qr0[0]] == 0
    assert layout[qr0[1]] == 1
    assert layout[qr1[0]] == 3
    assert layout[qr1[1]] == 4


def test_single_xtalk_rev(fake_machine): 
    qr0 = QuantumRegister(2, 'qr0')
    qr1 = QuantumRegister(2, 'qr1')
    qc = QuantumCircuit(qr0, qr1)

    qc.cx(qr0[0], qr0[1])
    qc.cx(qr0[1], qr0[0])
    qc.cx(qr1[0], qr1[1])
    xtalk_prop = {(1, 0): {(3, 2): 2}}
    
    
    dag = circuit_to_dag(qc)
    pass_ = CrosstalkAdaptiveMultiLayout(fake_machine, xtalk_prop)
    pass_.run(dag)

    layout = pass_.property_set['layout']
    assert layout[qr0[0]] == 0
    assert layout[qr0[1]] == 1
    assert layout[qr1[0]] == 3
    assert layout[qr1[1]] == 4


def test_twos_xtalk(fake_machine): 
    qr0 = QuantumRegister(2, 'qr0')
    qr1 = QuantumRegister(2, 'qr1')
    qc = QuantumCircuit(qr0, qr1)

    qc.cx(qr0[0], qr0[1])
    qc.cx(qr0[1], qr0[0])
    qc.cx(qr1[0], qr1[1])
    xtalk_prop = {
        (0, 1): {(2, 3): 2}, 
        (2, 3): {(4, 5): 2}
        }
    
    dag = circuit_to_dag(qc)
    pass_ = CrosstalkAdaptiveMultiLayout(fake_machine, xtalk_prop)
    pass_.run(dag)

    layout = pass_.property_set['layout']
    assert layout[qr0[0]] == 0
    assert layout[qr0[1]] == 1
    assert layout[qr1[0]] == 3
    assert layout[qr1[1]] == 4

def test_three_xtalk(fake_machine): 
    qr0 = QuantumRegister(2, 'qr0')
    qr1 = QuantumRegister(2, 'qr1')
    qc = QuantumCircuit(qr0, qr1)

    qc.cx(qr0[0], qr0[1])
    qc.cx(qr0[1], qr0[0])
    qc.cx(qr1[0], qr1[1])
    xtalk_prop = {
        (0, 1): {(2, 3): 2}, 
        (1, 2): {(3, 4): 2},
        (2, 3): {(4, 5): 2}
        }
    
    dag = circuit_to_dag(qc)
    pass_ = CrosstalkAdaptiveMultiLayout(fake_machine, xtalk_prop)
    pass_.run(dag)

    layout = pass_.property_set['layout']
    assert layout[qr0[0]] == 0
    assert layout[qr0[1]] == 1
    assert layout[qr1[0]] == 3
    assert layout[qr1[1]] == 4