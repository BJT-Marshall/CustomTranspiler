from qiskit.transpiler.basepasses import TransformationPass
from qiskit.dagcircuit import DAGCircuit
from qiskit.circuit.library import RXGate, RZGate, RYGate, CRXGate, CRYGate, CRZGate
import numpy as np



class CustomOptimizationPass(TransformationPass):
    """
    A custom transpilation pass checking for the consecutive application of identical gates and consecutive rotation gates to be optimised.
    """

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

        #Applying the optimization to the copied DAGCircuit object
        self.cancel_consec_gates(new_dag)
        self.merge_rotation_gates(new_dag)

        return new_dag
    
    def cancel_consec_gates(self, dag: DAGCircuit):
        """
        Due to unitarity of quantum logic gates, consecutive applications have the action of identity.
        Removing pairs of consecutive gates therefore reduces the total gate count and build-up of error
        within a circuit.

        :param dag: A :python:`DAGCircuit` object to be optimised.
        :type dag: DAGCircuit
        """

        for node in list(dag.topological_op_nodes()):
            succesive_operation = dag.quantum_successors(node)

            for operation in succesive_operation:
                #If the operation is not a gate, ignore it. (i.e. barriers, measurments etc)
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
    
    def merge_rotation_gates(self, dag: DAGCircuit):
        """
        Merges consecutive single qubit and controlled rotation gates into a single application therefore reducing the total gate count and build-up of error
        within a circuit.

        :param dag: A :python:`DAGCircuit` object to be optimised.
        :type dag: DAGCircuit
        """

        for node in list(dag.topological_op_nodes()):
            succesive_operation = dag.quantum_successors(node)

            for operation in succesive_operation:
                #If the operation is not a gate, ignore it. (i.e. barriers, measurments etc)
                if not hasattr(operation, "op"):
                    continue
                if node.qargs != operation.qargs:
                    continue

                #If two consecutive operations are RZ gates, merge them:
                if isinstance(node.op, RZGate) and isinstance(operation.op, RZGate):
                    theta = node.op.params[0] + operation.op.params[0]
                    new_gate = RZGate(theta)

                    dag.substitute_node(node, new_gate)
                    dag.remove_op_node(operation)

                    break

                #If two consecutive operations are RX gates, merge them:
                if isinstance(node.op, RXGate) and isinstance(operation.op, RXGate):
                    theta = node.op.params[0] + operation.op.params[0]
                    new_gate = RXGate(theta)

                    dag.substitute_node(node, new_gate)
                    dag.remove_op_node(operation)

                    break

                #If two consecutive operations are RY gates, merge them:
                if isinstance(node.op, RYGate) and isinstance(operation.op, RYGate):
                    theta = node.op.params[0] + operation.op.params[0]
                    new_gate = RYGate(theta)

                    dag.substitute_node(node, new_gate)
                    dag.remove_op_node(operation)

                    break

                #If two consecutive operations are CRX gates, merge them:
                if isinstance(node.op, CRXGate) and isinstance(operation.op, CRXGate):
                    theta = node.op.params[0] + operation.op.params[0]
                    new_gate = CRXGate(theta)

                    dag.substitute_node(node, new_gate)
                    dag.remove_op_node(operation)

                    break

                #If two consecutive operations are CRY gates, merge them:
                if isinstance(node.op, CRYGate) and isinstance(operation.op, CRYGate):
                    theta = node.op.params[0] + operation.op.params[0]
                    new_gate = CRYGate(theta)

                    dag.substitute_node(node, new_gate)
                    dag.remove_op_node(operation)

                    break

                #If two consecutive operations are CRZ gates, merge them:
                if isinstance(node.op, CRZGate) and isinstance(operation.op, CRZGate):
                    theta = node.op.params[0] + operation.op.params[0]
                    new_gate = CRZGate(theta)

                    dag.substitute_node(node, new_gate)
                    dag.remove_op_node(operation)

                    break

        return None