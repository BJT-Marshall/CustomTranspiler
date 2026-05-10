import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import state_fidelity
from qiskit.visualization import plot_histogram
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error, thermal_relaxation_error


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

def fidelity_cost_function(circuit):

    fidelity = 1
    for gate,_,__ in circuit.data:
        #If gate does not have a defined error rate, default to a value of 0.001
        gate_error = error_rates.get(gate.name, 0.001)
        if gate.params != []: #if the gate is dependant on a parameter (rotation gate in this example)
            gate_error = parameter_based_error(gate.name, gate.params[0])
        fidelity *= (1-gate_error)

    return fidelity


def noise_model(
        T1 = 1.5e-4, 
        T2 = 7.5e-5, 
        time_single_qubit = 2.5e-8, 
        time_two_qubit = 2.5e-7,
        single_qubit_depol_param = 2.5e-4, 
        two_qubit_depol_param = 2.5e-3
        ):
    
    """
    Custom Qiskit noise model aiming to simulate superconducting qubit based hardware. Implements thermal relaxation errors and 
    depoloarizing errors for supported single and two qubit gates.

    Model Constants:
    :param T1: t1 relaxation time constant, default = 150 \\mu s
    :type T1: float
    :param T2: relaxation time constant, default =75 \\mu s
    :type T2: float
    :param time_single_qubit: default = 25ns
    :type time_single_qubit: float
    :param time_two_qubit: default = 250ns
    :type time_two_qubit: float
    :param single_qubit_depol_param: default = 2.5e-4
    :type single_qubit_depol_param: float
    :param two_qubit_depol_param: default = 2.5e-3
    :type two_qubit_depol_param: float
    :returns model: Custom noise model
    :rtype: NoiseModel
    """

    model = NoiseModel() #basis_gates = ['id', 'rz', 'sx', 'cx'] by default

    #Single qubit noise channels
    single_qubit_thermal = thermal_relaxation_error(t1= T1,t2= T2,time=time_single_qubit)
    single_qubit_depol = depolarizing_error(param= single_qubit_depol_param ,num_qubits=1) #depolorizing error rate ~0.00025
    
    single_qubit_error = single_qubit_depol.compose(single_qubit_thermal)

    for gate in ["x","y","z","rx","ry","rz","sx"]:
        model.add_all_qubit_quantum_error(error=single_qubit_error, instructions=gate)

    #Two qubit noise channels
    two_qubit_thermal = thermal_relaxation_error(t1 = T1, t2 = T2, time = time_two_qubit)
    two_qubit_depol = depolarizing_error(param = two_qubit_depol_param, num_qubits=2) #depolorizing error rate ~0.0025

    two_qubit_error = two_qubit_depol.compose(two_qubit_thermal)
    for gate in ["cx","cy","cz","crx","cry","crz"]:
        model.add_all_qubit_quantum_error(error=two_qubit_error, instructions=gate)

    return model


def simulate_ideal_vs_noise(circuit, noise_model):
    """
    Runs a circuit using an ideal AerSimulator and a noisy AerSimulator using the passed noise model to 
    calculate the circuit fidelity under said noise model.

    :param circuit: Quantum circuit to be simulated.
    :type circuit: QuantumCircuit
    :param noise_model: Custom noise model to be simulated.
    :type noise_model: NoiseModel
    :returns fid: Fidelity of the quantum circuit under the custom noise model.
    :rtype: float
    """

    noisy_circ = circuit.copy()
    ideal_simulator = AerSimulator(method = "statevector")
    noisy_simulator = AerSimulator(method = "density_matrix", noise_model = noise_model)

    circuit.save_statevector()
    ideal_res = ideal_simulator.run(circuit).result()
    ideal_state = ideal_res.get_statevector()
    
    noisy_circ.save_density_matrix()
    noisy_res = noisy_simulator.run(noisy_circ).result()
    noisy_state = noisy_res.data(0)["density_matrix"]

    fid = state_fidelity(ideal_state,noisy_state)

    return fid



