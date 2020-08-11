import networkx as nx
from qiskit.transpiler.layout import Layout
from qiskit.transpiler.basepasses import AnalysisPass
from qiskit.transpiler.exceptions import TranspilerError


class CrosstalkAdaptiveLayout(AnalysisPass):
    def __init__(self, backend_prop, crosstalk_prop):

        super.__init__()
        self.backend_prop = backend_prop
        self.crosstalk_prop = crosstalk_prop
