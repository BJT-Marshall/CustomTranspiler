import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Kraus, SuperOp
from qiskit.visualization import plot_histogram
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, QuantumError, ReadoutError, depolarizing_error, pauli_error, thermal_relaxation_error


#Define a custom noise model assigning error rates to a set of gate types:

single_qubit_error_rates = {
    "x" : 0.001,
    "y" : 0.001,
    "z" : 0.001,
    "rx": 0.005,
    "ry": 0.005,
    "rz": 0.005
}

def squared_noise_model(single_qubit_errors):
    """
    For some inputted set of single qubit gate error rates, generates a new dictionary adding the error rates for the controlled
    versions of all sngle qubit gates where the error rate of a single qubit gate is equal to the square of its controlled counterpart.
    """
    error_rates = {}
    for gate in single_qubit_errors:
        error_rates[gate] = single_qubit_errors[gate]
        error_rates["c"+str(gate)] = np.sqrt(single_qubit_errors[gate])

    return error_rates

error_rates = squared_noise_model(single_qubit_error_rates)

def parameter_based_error(gate_name, gate_parameter):
    """
    The idea is to model the error for rotation gates as dependant on their rotation parameter. This is to simulate a case where certain
    rotations can be prepared with less error than others on some imaginary real hardware and therefore a merging from two rotations
    :math:`\\theta_1` and :math:`\\theta_2` to the single rotation :math:`\\Theta = \\theta_1 + \\theta_2` may not be optimal.
    
    Choses to scale rotations about the :math:`(X,Y,Z)` axis by :math:`(\\abs{\\sin{(\\theta)}}, \\abs{\\tan{(\\theta)}}}, \\abs{\\cos{\\theta})}` respectively.

    """
    error = error_rates.get(gate_name, 0.001)

    if gate_name[-2:] == "rx":
        error = error*np.abs(np.sin(gate_parameter))
    elif gate_name[-2:] == "ry":
        error = error*np.abs(np.tan(gate_parameter))
    elif gate_name[-2:] == "rz":
        error = error*np.abs(np.cos(gate_parameter))



    return error

def error_cost_function(circuit):

    error = 0
    for gate,_,__ in circuit.data:
        #If gate does not have a defined error rate, default to a value of 0.001
        gate_error = error_rates.get(gate.name, 0.001)
        if gate.params != []: #if the gate is dependant on a parameter (rotation gate in this example)
            gate_error = parameter_based_error(gate.name, gate.params[0])
        error += gate_error

    return error