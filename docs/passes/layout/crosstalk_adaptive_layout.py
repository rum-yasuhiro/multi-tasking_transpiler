import math
import networkx as nx
from qiskit.transpiler.layout import Layout
# from qiskit.transpiler.basepasses import AnalysisPass
#################################################
from qiskit.transpiler.basepasses import BasePass
#################################################
from qiskit.transpiler.exceptions import TranspilerError
from qiskit import QuantumRegister, ClassicalRegister
from qiskit.dagcircuit import DAGCircuit


class CrosstalkAdaptiveMultiLayout(BasePass):
    def __init__(self, backend_prop, crosstalk_prop=None, output_name=None):

        super().__init__()
        self.backend_prop = backend_prop
        self.crosstalk_prop = crosstalk_prop
        self.crosstalk_edges = []
        self.prog_graphs = []
        self.dag_list = []
        self.output_name = output_name
        self.composed_multidag = DAGCircuit()

        self.swap_graph = nx.DiGraph()
        self.cx_reliability = {}
        self.readout_reliability = {}
        self.available_hw_qubits = []
        self.gate_list = []
        self.swap_paths = {}
        self.swap_reliabs = {}
        self.gate_reliability = {}
        self.qarg_to_id = {}
        self.pending_program_edges = []
        self.prog2hw = {}

    def _initialize_backend_prop(self):
        """Extract readout and CNOT errors and compute swap costs."""
        backend_prop = self.backend_prop
        for ginfo in backend_prop.gates:
            if ginfo.gate == 'cx':
                for item in ginfo.parameters:
                    if item.name == 'gate_error':
                        g_reliab = 1.0 - item.value
                        break
                    g_reliab = 1.0
                swap_reliab = pow(g_reliab, 3)
                # convert swap reliability to edge weight
                # for the Floyd-Warshall shortest weighted paths algorithm
                swap_cost = - \
                    math.log(swap_reliab) if swap_reliab != 0 else math.inf
                self.swap_graph.add_edge(
                    ginfo.qubits[0], ginfo.qubits[1], weight=swap_cost)
                self.swap_graph.add_edge(
                    ginfo.qubits[1], ginfo.qubits[0], weight=swap_cost)
                self.cx_reliability[(
                    ginfo.qubits[0], ginfo.qubits[1])] = g_reliab
                self.gate_list.append((ginfo.qubits[0], ginfo.qubits[1]))
        idx = 0
        for q in backend_prop.qubits:
            for nduv in q:
                if nduv.name == 'readout_error':
                    self.readout_reliability[idx] = 1.0 - nduv.value
                    self.available_hw_qubits.append(idx)
            idx += 1
        self._update_edge_prop()

    def _update_edge_prop(self):
        for edge in self.cx_reliability:
            self.gate_reliability[edge] = self.cx_reliability[edge] * \
                self.readout_reliability[edge[0]] * \
                self.readout_reliability[edge[1]]
        self.swap_paths, swap_reliabs_temp = nx.algorithms.shortest_paths.dense.\
            floyd_warshall_predecessor_and_distance(
                self.swap_graph, weight='weight')
        for i in swap_reliabs_temp:
            self.swap_reliabs[i] = {}
            for j in swap_reliabs_temp[i]:
                if (i, j) in self.cx_reliability:
                    self.swap_reliabs[i][j] = self.cx_reliability[(i, j)]
                elif (j, i) in self.cx_reliability:
                    self.swap_reliabs[i][j] = self.cx_reliability[(j, i)]
                else:
                    best_reliab = 0.0
                    for n in self.swap_graph.neighbors(j):
                        if (n, j) in self.cx_reliability:
                            reliab = math.exp(-swap_reliabs_temp[i][n]) * \
                                self.cx_reliability[(n, j)]
                        else:
                            reliab = math.exp(-swap_reliabs_temp[i][n]) * \
                                self.cx_reliability[(j, n)]
                        if reliab > best_reliab:
                            best_reliab = reliab
                    self.swap_reliabs[i][j] = best_reliab

    def _crosstalk_backend_prop(self):
        if self.crosstalk_prop is not None:
            for edge in self.crosstalk_prop:
                if edge in self.prog2hw:
                    for xtalk_edge in self.crosstalk_prop[edge]:
                        cx_error = (1 - self.cx_reliability[xtalk_edge])
                        cx_error *= self.crosstalk_prop[edge][xtalk_edge]
                        self.cx_reliability[xtalk_edge] = 1 - cx_error
                    self.crosstalk_edges.append(edge)
            for edge in self.crosstalk_edges:
                if edge in self.crosstalk_prop:
                    self.crosstalk_prop.pop(edge)
            self._update_edge_prop()

    def _create_program_graphs(self, dag_list):
        idx = 0
        prog_kqs = {}
        dags = {}
        for i, dag in enumerate(dag_list):
            dag_q_id = 0
            for q in dag.qubits:
                self.qarg_to_id[q.register.name + str(q.index)] = dag_q_id
                dag_q_id += 1
            idx += dag_q_id
            _prog_graph = nx.Graph()
            prog_depth = 0
            for gate in dag.two_qubit_ops():
                qid1 = self._qarg_to_id(gate.qargs[0])
                qid2 = self._qarg_to_id(gate.qargs[1])
                min_q = min(qid1, qid2)
                max_q = max(qid1, qid2)
                edge_weight = 1
                if _prog_graph.has_edge(min_q, max_q):
                    edge_weight = _prog_graph[min_q][max_q]['weight'] + 1
                _prog_graph.add_edge(min_q, max_q, weight=edge_weight)
                prog_depth += edge_weight
            # calculate KQ of dag (height * depth)
            dag_kq = dag_q_id * prog_depth
            prog_kqs[i] = dag_kq
            dags[i] = dag

        self.dag_list = [dags[dag_kq[0]] for dag_kq in sorted(
            prog_kqs.items(), key=lambda x: x[1], reverse=True)]

        """FIXME
        # self.prog_graphs = [prog_graphs[dag_kq[0]] for dag_kq in sorted(
        #     prog_kqs.items(), key=lambda x: x[1], reverse=True)]
        """
        ###############
        depths = []
        ###############
        reg_counter = 0
        for dag in self.dag_list:
            prog_graph = nx.Graph()
            for gate in dag.two_qubit_ops():
                qid1 = self._qarg_to_id(gate.qargs[0])+reg_counter
                qid2 = self._qarg_to_id(gate.qargs[1])+reg_counter
                min_q = min(qid1, qid2)
                max_q = max(qid1, qid2)
                edge_weight = 1
                if prog_graph.has_edge(min_q, max_q):
                    edge_weight = prog_graph[min_q][max_q]['weight'] + 1
                prog_graph.add_edge(min_q, max_q, weight=edge_weight)
            #######################
            depths.append(edge_weight)
            #######################
            self.prog_graphs.append(prog_graph)
            reg_counter += dag.num_qubits()
        return idx, depths

    def _qarg_to_id(self, qubit):
        """Convert qarg with name and value to an integer id."""
        return self.qarg_to_id[qubit.register.name + str(qubit.index)]

    def _select_next_edge(self):
        """Select the next edge.

        If there is an edge with one endpoint mapped, return it.
        Else return in the first edge
        """
        for edge in self.pending_program_edges:
            q1_mapped = edge[0] in self.prog2hw
            q2_mapped = edge[1] in self.prog2hw
            assert not (q1_mapped and q2_mapped)
            if q1_mapped or q2_mapped:
                return edge
        return self.pending_program_edges[0]

    def _select_best_remaining_cx(self):
        """Select best remaining CNOT in the hardware for the next program edge."""
        candidates = []
        for gate in self.gate_list:
            chk1 = gate[0] in self.available_hw_qubits
            chk2 = gate[1] in self.available_hw_qubits
            if chk1 and chk2:
                candidates.append(gate)
        best_reliab = 0
        best_item = None
        # update gate_reliability with considering about xtalk
        self._crosstalk_backend_prop()
        for item in candidates:
            if self.gate_reliability[item] > best_reliab:
                best_reliab = self.gate_reliability[item]
                best_item = item
        return best_item

    def _select_best_remaining_qubit(self, prog_qubit, prog_graph):
        """Select the best remaining hardware qubit for the next program qubit."""
        # update gate_reliability with considering about xtalk
        self._crosstalk_backend_prop()
        reliab_store = {}
        for hw_qubit in self.available_hw_qubits:
            reliab = 1
            for n in prog_graph.neighbors(prog_qubit):
                if n in self.prog2hw:
                    reliab *= self.swap_reliabs[self.prog2hw[n]][hw_qubit]
            reliab *= self.readout_reliability[hw_qubit]
            reliab_store[hw_qubit] = reliab
        max_reliab = 0
        best_hw_qubit = None
        for hw_qubit in reliab_store:
            if reliab_store[hw_qubit] > max_reliab:
                max_reliab = reliab_store[hw_qubit]
                best_hw_qubit = hw_qubit
        return best_hw_qubit

    def _compose_dag(self, dag_list):
        """Compose each dag and return new multitask dag"""

        """FIXME 下記と同様
        # name_list = []
        """
        bit_counter = 0
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
            self.composed_multidag.add_qreg(qr)
            self.composed_multidag.add_creg(cr)
            qubits = self.composed_multidag.qubits[bit_counter:bit_counter+register_size]
            clbits = self.composed_multidag.clbits[bit_counter:bit_counter+register_size]
            self.composed_multidag.compose(dag, qubits=qubits, clbits=clbits)

            bit_counter += register_size
        return self.composed_multidag

    def run(self, dag_list):
        """Run the CrosstalkAdaptiveLayout pass on `list of dag`."""
        self._initialize_backend_prop()
        num_qubits = self._create_program_graphs(dag_list=dag_list)
        if num_qubits > len(self.swap_graph):
            raise TranspilerError('Number of qubits greater than device.')

        layout = Layout()
        new_dag = self._compose_dag(self.dag_list)
        for hwid, q in enumerate(new_dag.qubits):
            self.qarg_to_id[q.register.name + str(q.index)] = hwid

        for prog_graph in self.prog_graphs:
            # sort by weight, then edge name for determinism (since networkx on python 3.5 returns
            # different order of edges)
            """NEXT STEP!
            ここに、Multi-programmingするかどうかの判定関数を噛ませる
            """
            self.pending_program_edges = sorted(prog_graph.edges(data=True),
                                                key=lambda x: [
                x[2]['weight'], -x[0], -x[1]],
                reverse=True)

            while self.pending_program_edges:
                edge = self._select_next_edge()
                q1_mapped = edge[0] in self.prog2hw
                q2_mapped = edge[1] in self.prog2hw
                if (not q1_mapped) and (not q2_mapped):
                    best_hw_edge = self._select_best_remaining_cx()
                    if best_hw_edge is None:
                        raise TranspilerError("CNOT({}, {}) could not be placed "
                                              "in selected device.".format(edge[0], edge[1]))
                    self.prog2hw[edge[0]] = best_hw_edge[0]
                    self.prog2hw[edge[1]] = best_hw_edge[1]
                    self.available_hw_qubits.remove(best_hw_edge[0])
                    self.available_hw_qubits.remove(best_hw_edge[1])
                elif not q1_mapped:
                    best_hw_qubit = self._select_best_remaining_qubit(
                        edge[0], prog_graph)
                    if best_hw_qubit is None:
                        raise TranspilerError(
                            "CNOT({}, {}) could not be placed in selected device. "
                            "No qubit near qr[{}] available".format(edge[0], edge[1], edge[0]))
                    self.prog2hw[edge[0]] = best_hw_qubit
                    self.available_hw_qubits.remove(best_hw_qubit)
                else:
                    best_hw_qubit = self._select_best_remaining_qubit(
                        edge[1], prog_graph)
                    if best_hw_qubit is None:
                        raise TranspilerError(
                            "CNOT({}, {}) could not be placed in selected device. "
                            "No qubit near qr[{}] available".format(edge[0], edge[1], edge[1]))
                    self.prog2hw[edge[1]] = best_hw_qubit
                    self.available_hw_qubits.remove(best_hw_qubit)
                new_edges = [x for x in self.pending_program_edges
                             if not (x[0] in self.prog2hw and x[1] in self.prog2hw)]
                self.pending_program_edges = new_edges
            for qid in self.qarg_to_id.values():
                if qid not in self.prog2hw:
                    self.prog2hw[qid] = self.available_hw_qubits[0]
                    self.available_hw_qubits.remove(self.prog2hw[qid])

        for q in new_dag.qubits:
            pid = self._qarg_to_id(q)
            hwid = self.prog2hw[pid]
            layout[q] = hwid
        self.property_set['layout'] = layout

        return new_dag, layout
