from qiskit.transpiler.basepasses import TransformationPass
from qiskit.dagcircuit import DAGCircuit
from qiskit.converters import dag_to_circuit
from qiskit.circuit.library import XGate, YGate, ZGate, CXGate, CYGate, CZGate, RXGate, RZGate, RYGate, CRXGate, CRYGate, CRZGate
from qiskit_aer.noise import NoiseModel
import numpy as np
from NoiseModel import CustomNoise, parameter_adjustment




class CustomOptimisationPass(TransformationPass):
    """
    A custom optmisisation pass implementing modular optimisations to Qiskit :python:`QuantumCircuit` objects.
    """

    def __init__(self):
        super().__init__()
        self.noise_model = None

    def set_noise_model(self, noise: CustomNoise):
        """
        Sets the noise model to be used in optimisation.

        :param noise: The noise model to be set
        :type noise: CustomNoise
        """

        self.noise_model = noise
        return None

    def run(self, dag: DAGCircuit) -> DAGCircuit:
        """
        Runs the custom optimisation on the :python:`DAGCircuit` object.

        :param dag: A :python:`DAGCircuit` object to be optimised.
        :type dag: DAGCircuit
        :returns new_dag: The optimised :python:`DAGCircuit` object.
        :rtype DAGCircuit:
        """

        #Copying the DAGCircuit object
        new_dag = dag.copy_empty_like()

        for node in dag.topological_op_nodes():
            new_dag.apply_operation_back(node.op, node.qargs, node.cargs)

        #Applying the optimisation to the copied DAGCircuit object
        
        self.swap_commuting_gates(new_dag)
        self.cancel_consec_gates(new_dag)
        if self.noise_model != None:
            self.merge_rotation_gates(new_dag, self.noise_model)
        else:
            self.merge_rotation_gates(new_dag)

        return new_dag        
    
    def cancel_consec_gates(self, dag: DAGCircuit):
        """
        Removes consecutive applications of hermetian gates within the circuit. Due to unitarity of quantum logic gates, consecutive applications of hermetian gates have the action of identity.
        Removing pairs of consecutive gates therefore reduces the total gate count and build-up of error
        within a circuit.

        :param dag: A :python:`DAGCircuit` object to be optimised.
        :type dag: DAGCircuit
        """
        for node in list(dag.topological_op_nodes()):
            succesive_operation = dag.quantum_successors(node)

            for operation in succesive_operation:       
                #If node is not an operation, ignore
                if not hasattr(operation, "op"):
                    continue
        
                #if the operation is the same and it is one the same qubits
                if type(node.op) == type(operation.op) and node.qargs == operation.qargs and node.op.params == operation.op.params:
                    #If the operation is Hermetian and therefore U^2 = U^dag U = I (as must be unitary)
                    if np.array_equal(node.op.to_matrix().conj().T,node.op.to_matrix()):
                        dag.remove_op_node(node)
                        dag.remove_op_node(operation)
                        break
        return None
    
    def merge_rotation_gates(self, dag: DAGCircuit, noise = None):
        """
        Merges consecutive single qubit and controlled rotation gates into a single application therefore reducing the total gate count and build-up of error
        within a circuit.

        :param dag: A :python:`DAGCircuit` object to be optimised.
        :type dag: DAGCircuit
        """

        rotation_gate_constructors = [RZGate, RXGate, RYGate, CRZGate, CRXGate, CRYGate]

        for node in list(dag.topological_op_nodes()):
            succesive_operation = dag.quantum_successors(node)

            for operation in succesive_operation:
                #If node is not an operation, ignore
                if not hasattr(operation, "op"):
                    continue
                if node.qargs != operation.qargs:
                    continue

                for constructor in rotation_gate_constructors:
                #If two consecutive operations are RZ gates, merge them:
                    if isinstance(node.op, constructor) and isinstance(operation.op, constructor):
                        theta = node.op.params[0] + operation.op.params[0]
                        if theta == 0:
                            dag.remove_op_node(node)
                            dag.remove_op_node(operation)
                        else:
                            new_gate = constructor(theta)

                            if noise != None:
                                old_error = parameter_adjustment(noise.single_qubit_depol, node.op.params[0]) + parameter_adjustment(noise.single_qubit_depol, operation.op.params[0])
                                new_error = parameter_adjustment(noise.single_qubit_depol, theta)
                                if new_error < old_error:
                                    dag.substitute_node(node, new_gate)
                                    dag.remove_op_node(operation)
                            else:
                                dag.substitute_node(node, new_gate)
                                dag.remove_op_node(operation)

                        break
        return None
    
    def swap_commuting_gates(self, dag:DAGCircuit):
        """
        Swaps operation order for commuting gates if swaps result in gate cancellations or rotation merges.

        :param dag: A :python:`DAGCircuit` object to be optimised.
        :type dag: DAGCircuit
        """

        single_qubit_commuting_pairs = {
            #Convention: If TwoQubitGate commutes with "single_qubit_name" only on certain qubit(s) with qargs then its entry is [TwoQubitGate, [qargs]]
            "x": [RXGate, [CXGate,[1]], [CRXGate,[1]]],
            "y": [RYGate, [CYGate,[1]], [CRYGate,[1]]],
            "z": [RZGate, CZGate, CRZGate, [CXGate,[0]], [CRXGate,[0]], [CYGate,[0]], [CRYGate,[0]]],
            "rx": [XGate, [CXGate,[1]], [CRXGate,[1]]],
            "ry": [YGate, [CYGate,[1]], [CRYGate,[1]]],
            "rz": [ZGate, CZGate, CRZGate, [CXGate,[0]], [CRXGate,[0]], [CYGate,[0]], [CRYGate,[0]]],
            "sx": [XGate, RXGate,[CXGate,[1]],[CZGate,[0]],[CRZGate,[0]],[CRXGate,[0,1]]] 
            
        } 

        two_to_one_qubit_commuting_pairs = {
            #Convention: if "two_qubit_name" commutes with SingleQubitGate only on certain qubit(s) with qargs then its entry is [TwoQubitGate, [qargs]]
            "cx": [[XGate,[1]],[RXGate,[1]],[ZGate,[0]],[RZGate,[0]]],
            "cy": [[YGate,[1]],[RYGate,[1]],[ZGate,[0]],[RZGate,[0]]],
            "cz": [ZGate,RZGate],
            "crx": [[XGate,[1]],[RXGate,[1]],[ZGate,[0]],[RZGate,[0]]],
            "cry": [[YGate,[1]],[RYGate,[1]],[ZGate,[0]],[RZGate,[0]]],
            "crz": [ZGate,RZGate]
        } 

        two_to_two_qubit_commuting_pairs = {
            #Convention: True means same qargs, False means different qargs
            "cx": [[CRXGate, True], [CZGate, True], [CRZGate, True]],
            "cy": [[CRYGate, True], [CZGate, True], [CRZGate, True]],
            "cz": [[CRZGate, True], [CRZGate, True]]

        } #TODO finish this list of commutators

        for qubit in dag.qubits:
            operations = list(dag.nodes_on_wire(qubit, only_ops=True))
            for i in range(1,len(operations)-1):
                prev_node = operations[i-1]
                node = operations[i]
                next_node = operations[i+1]
                if type(prev_node.op) == type(next_node.op) and len(node.qargs) == 1: #if they would cancel or merge.
                    for gate in single_qubit_commuting_pairs[node.op.name]:
                        if isinstance(gate,list): #if the gate is a two qubit gate that requires more careful treatment
                            if isinstance(next_node.op, gate[0]): #if they also can be brought together through commutation
                                for arg in gate[1]:
                                    if node.qargs[0] == next_node.qargs[arg]: #if the qargs are correct to allow commutation
                                        dag.swap_nodes(node,next_node)
                            break
                                        
                        else:
                            if isinstance(next_node.op, gate): #if the single qubit gates commute and can be swapped
                                dag.swap_nodes(node,next_node)
                            break

                
                elif type(prev_node.op) == type(next_node.op):
                    for gate in two_to_one_qubit_commuting_pairs[node.op.name]: #[[XGate,[1]],[RXGate,[1]],[ZGate,[0]],[RZGate,[0]]]
                        if isinstance(gate,list): #if the gate is a two qubit gate that requires more careful treatment
                            if isinstance(next_node.op, gate[0]): #if they also can be brought together through commutation
                                for arg in gate[1]:
                                    if node.qargs[arg] == next_node.qargs[0]: #if the qargs are correct to allow commutation
                                        dag.swap_nodes(node,next_node)
                            break
                        else:
                            if isinstance(next_node.op, gate): #if the single qubit gates commute and can be swapped
                                dag.swap_nodes(node,next_node)
                            break
                        
                        
                    #for gate in two_to_two_qubit_commuting_pairs:
        
        return None