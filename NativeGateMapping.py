from qiskit.circuit.library import SXGate, RZGate, CXGate
from qiskit.dagcircuit import DAGCircuit
from qiskit import QuantumCircuit
from qiskit.converters import circuit_to_dag, dag_to_circuit
import numpy as np

#Basis Transformation into a common Native Gate Set
#Take the common native gate set {RZ, SX, CX}

#For the gates handled by the custom optimisation pass in CustomPass.py, this is a lookup table for their decompositions into the 
#native gate set {"rz","sx","cx"}.
lookup_table = {
    "x": ["sx","sx"],
    "y": [["rz",np.pi/2],"sx","sx",["rz",-np.pi/2]],
    "z": [["rz",np.pi]],
    "rx": [["rz",-np.pi/2],"sx",["rz","1"],"sx",["rz",np.pi/2]],
    "ry": [["rz",-np.pi/2],"sx",["rz","1"],"sx",["rz",np.pi/2]],
    "rz": ["rz"], #native
    "cx": ["cx"], #native
    "cy": [["rz",-np.pi/2], "cx", ["rz",np.pi/2]],
    "cz": [["rz",np.pi],"sx",["rz",np.pi/2],"cx",["rz",np.pi],"sx",["rz",np.pi/2]],
    "crx": [["rz",np.pi],"sx",["rz",np.pi/2],["rz","0.5"],"cx",["rz","-0.5"],"cx",["rz",np.pi],"sx",["rz",np.pi/2]],
    "cry": [["rz",-np.pi/2],["rz",np.pi],"sx",["rz",np.pi/2],["rz","0.5"],"cx",["rz","-0.5"],"cx",["rz",np.pi],"sx",["rz",np.pi/2],["rz",np.pi/2]],
    "crz": [["rz","0.5"],"cx",["rz","-0.5"],"cx"]
}

def circuit_generator(gate_name:str, gate_params:list):
    """
    Generates native gate set decomposition for an inputted gate using the gate set :python:`('rz','sx','cx')`.

    :param gate_name: The name string for the gate to be decomposed
    :type gate_name: str
    :param gate_params: The list of parameters for the gate to be decomposed
    :type gate_params: str
    """
    
    op_list = lookup_table[gate_name]
    if len(gate_name) == 1:
        qc = QuantumCircuit(1)
        qubits = [0]
    else:
        qc = QuantumCircuit(2) #define qubit 1 to be the control and qubit 0 to be the target
        qubits = [0,1]
    

    for op in op_list:
        if op == "sx":
            qc.sx(qubits[-1])
        if op == "cx":
            qc.cx(qubits[0],qubits[1])
        #else must be a RZ gate
        if isinstance(op,list):
            if isinstance(op[1],float) or isinstance(op[1],int):
                qc.rz(op[1],qubits[-1])
            if isinstance(op[1],str):
                qc.rz(float(op[1])*gate_params[0],qubits[-1])

    return circuit_to_dag(qc)

class NativeGateMap():
    """Used to generate circuit mappings using the imaginary native gate set :math:`\\{RZ(\\theta),CX,\\sqrt{X}\\}`."""

    def map(self, circuit: QuantumCircuit):
        """
        Generates a decomposition of the inputted quantum circuit in terms of the gate set :math:`\\{RZ(\\theta), CX, \\sqrt{X}\\}`.
        Supported gates for decomposition are: :math:`X, Y, Z, RX, RY, RZ` and their controlled variants.

        :param circuit:
        :type circuit: QuantumCircuit
        :returns new_circuit:
        :rtype: QuantumCircuit
        """

        dag = circuit_to_dag(circuit)
        new_dag = dag.copy_empty_like()
        for node in dag.topological_op_nodes():
            new_dag.apply_operation_back(node.op, node.qargs, node.cargs)

        self.native_gate_mapping(new_dag)
        new_circuit = dag_to_circuit(new_dag)
        
        return new_circuit

    def native_gate_mapping(self, dag:DAGCircuit):
        """
        Performs the circuit decomposition iterating through the original circuit and iteratively replacing each gate
        with its corresponding decomposition.

        :param dag: Initial DAG circuit in terms of supported gates.
        :type dag: DAGCircuit
        :returns dag: Decomposed DAG circuit in terms of the native gate set.
        :rtype: DAGCircuit
        """

        for node in list(dag.topological_op_nodes()):
            #If the operation is not a gate, ignore it. (i.e. barriers, measurments etc)
            if not hasattr(node, "op"):
                    continue
            decomp = circuit_generator(node.op.name,node.op.params)
            dag.substitute_node_with_dag(node, decomp)

        return dag