from qiskit_aer import AerSimulator
from qiskit.quantum_info import state_fidelity

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