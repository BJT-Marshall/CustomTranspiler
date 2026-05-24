import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer.noise import NoiseModel, depolarizing_error, thermal_relaxation_error
from qiskit.circuit.library import RXGate, RYGate, RZGate, CRXGate, CRYGate, CRZGate
from qiskit.converters import circuit_to_dag, dag_to_circuit

class CustomNoise(NoiseModel):
    """
    Custom noise model to simulate the errors of superconducting qubit-based hardware.
    """
    
    def __init__(self, basis_gates=None):
        super().__init__(basis_gates)
        #Setting attributes for to be accessed during optimisation
        self.single_qubit_depol = 2.5e-4
        self.two_qubit_depol = 2.5e-3


    def noise_model(
        self,
        circuit : QuantumCircuit,
        T1 : float = 1.5e-4, 
        T2 : float = 7.5e-5, 
        time_single_qubit : float = 2.5e-8, 
        time_two_qubit : float = 2.5e-7,
        single_qubit_depol_param : float = 2.5e-4, 
        two_qubit_depol_param : float = 2.5e-3
        ):
    
        """
        Custom Qiskit noise model aiming to simulate superconducting qubit based hardware. Implements thermal relaxation errors and 
        depoloarizing errors for supported single and two qubit gates.

        Model Constants:
        :param T1: Thermal t1 relaxation time constant, default = 150 \\mu s
        :type T1: float
        :param T2: Thermal t2 relaxation time constant, default = 75 \\mu s
        :type T2: float
        :param time_single_qubit: Single qubit gate thermal relaxation time, default = 25ns
        :type time_single_qubit: float
        :param time_two_qubit: Two qubit gate thermal relaxation time, default = 250ns
        :type time_two_qubit: float
        :param single_qubit_depol_param: Single qubit gate depolarizing constant, default = 2.5e-4
        :type single_qubit_depol_param: float
        :param two_qubit_depol_param: Two qubit gate depolarizing constant, default = 2.5e-3
        :type two_qubit_depol_param: float
        :returns model: Custom noise model
        :rtype: NoiseModel
        """
        
        self.single_qubit_depol = single_qubit_depol_param
        self.two_qubit_depol = two_qubit_depol_param

        model = NoiseModel() #basis_gates = ['id', 'rz', 'sx', 'cx'] by default
        
        #Single qubit noise channels
        single_qubit_thermal = thermal_relaxation_error(t1= T1,t2= T2,time=time_single_qubit)
        single_qubit_depol = depolarizing_error(param= single_qubit_depol_param ,num_qubits=1) #depolorizing error rate ~0.00025
        
        single_qubit_error = single_qubit_depol.compose(single_qubit_thermal)

        for gate in ["x","y","z","sx"]:
            model.add_all_qubit_quantum_error(error=single_qubit_error, instructions=gate)
        
        #Rotation gate errors:
        rotation_depol_errors_1q = rotation_based_noise_1q(circuit, single_qubit_depol_param)
        for gate_label in rotation_depol_errors_1q:
            rotation_error = rotation_depol_errors_1q[gate_label].compose(single_qubit_thermal)
            model.add_all_qubit_quantum_error(error = rotation_error, instructions = gate_label)
        
        #Two qubit noise channels
        two_qubit_thermal = thermal_relaxation_error(t1 = T1, t2 = T2, time = time_two_qubit)
        two_qubit_depol = depolarizing_error(param = two_qubit_depol_param, num_qubits=2) #depolorizing error rate ~0.0025
        two_qubit_error = two_qubit_depol.compose(two_qubit_thermal)
        for gate in ["cx","cy","cz"]:
            model.add_all_qubit_quantum_error(error=two_qubit_error, instructions=gate)

        #Two qubit rotation gate errors: 
        rotation_depol_errors_2q = rotation_based_noise_2q(circuit, two_qubit_depol_param)
        for gate_label in rotation_depol_errors_2q:
            rotation_error_2q = rotation_depol_errors_2q[gate_label].compose(two_qubit_thermal)
            model.add_all_qubit_quantum_error(error = rotation_error_2q, instructions = gate_label)

        self.model = model

        return model

#Helper methods for the CustomNoise class:

def rotation_based_noise_1q(circuit: QuantumCircuit, base_depol_error_rate: float):
    """
    Generates depolarizing errors for each rotation gate dependant on its rotation parameter, to be appended into the custom noise model.

    :param circuit: The quantum circuit being considered, from which the rotation gates will be taken
    :type circuit: QuantumCircuit
    :param base_depol_error_rate: The default depolarization error rate for the rotation gate type
    :returns rotation_errors: A dictionary containing the rotation gate error channels indexed by their parameter label
    :rtype: dict
    """
    
    dag = circuit_to_dag(circuit)

    rotation_errors = {

    }
    rotation_gate_constructors = [RXGate,RYGate,RZGate]
    
    for node in list(dag.topological_op_nodes()):
        #If node is not an operation, ignore
        if not hasattr(node, "op"):
            continue
        for constructor in rotation_gate_constructors:    
            if isinstance(node.op,constructor):
                param = node.op.params[0]
                label = node.op.name
                node.op.label = label+str(param)
                rotation_errors[label+str(param)] = depolarizing_error(param= parameter_adjustment(base_depol_error_rate,param) ,num_qubits=1)

    return rotation_errors

def rotation_based_noise_2q(circuit: QuantumCircuit, base_depol_error_rate: float):
    """
    Generates depolarizing errors for each controlled rotation gate dependant on its rotation parameter, to be appended into the custom noise model.

    :param circuit: The quantum circuit being considered, from which the controlled rotation gates will be taken
    :type circuit: QuantumCircuit
    :param base_depol_error_rate: The default depolarization error rate for the rotation gate type
    :returns rotation_errors: A dictionary containing the rotation gate error channels indexed by their parameter label
    :rtype: dict
    """
    
    dag = circuit_to_dag(circuit)

    rotation_errors = {

    }
    rotation_gate_constructors = [CRXGate,CRYGate,CRZGate]
    
    for node in list(dag.topological_op_nodes()):
        #If node is not an operation, ignore
        if not hasattr(node, "op"):
            continue
        for constructor in rotation_gate_constructors:    
            if isinstance(node.op,constructor):
                param = node.op.params[0]
                label = node.op.name
                node.op.label = label+str(param)
                rotation_errors[label+str(param)] = depolarizing_error(param= parameter_adjustment(base_depol_error_rate,param) ,num_qubits=2)

    return rotation_errors
            
def parameter_adjustment(base_error:float, param:float):
    """
    Mathematical model to define parameter based depolarization error rates for rotation gates. Larger rotations produce higher errors
    due to build up or errors through multiple smaller rotations in real hardware. 
    Adjusted errors are in the range :math:`(0,10b]` where :math:`b` is the base depolarization error rate passed through :python:`base_error`.

    :param base_error: The default depolarization error rate for the rotation gate type
    :type base_error: float
    :param param: The rotation parameter to be adjusted
    :type param: float
    :returns error: The adjusted depolarization error rate
    :rtype: float
    """
  
    error = 10*base_error*abs(np.sin(param/4)) 

    return error





