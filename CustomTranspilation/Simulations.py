from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel
from qiskit.quantum_info import state_fidelity, hellinger_fidelity
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
from qiskit.transpiler import generate_preset_pass_manager
from qiskit.visualization import plot_histogram

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

def simulate_hellinger_fidelity(circuit,noise_model):
    """
    Uses an AerSimulator to simulate an optimised circuit under ideal and noisy conditions using the inputted noise model to compute the hellinger
    fidelity of the circuit. Used for comparing optimisation passes with respect to a noise model simulating a real backend, e.g. ibm_aachen.


    :param circuit: Optimised circuit to be simulated.
    :type circuit: QuantumCircuit
    :param noise_model: The noise model to be used when simulating the optimised circuit.
    :type noise_model: NoiseModel
    :returns fid: The computed hellinger fidelity of the circuit.
    :rtype: float
    """

    #transpile the circuit into the supported native gate set of ibm_aachen
    circuit = transpile(circuit, basis_gates=['cz','id','rz','sx','x'])
    
    ideal_simulator = AerSimulator()
    ideal_counts = ideal_simulator.run(circuit).result().get_counts()
    plot_histogram(ideal_counts, filename = 'Ideal Counts')

    noisy_simulator = AerSimulator(noise_model = noise_model)
    noisy_counts = noisy_simulator.run(circuit).result().get_counts()
    plot_histogram(noisy_counts,filename='Simulated Counts')

    fid = hellinger_fidelity(ideal_counts,noisy_counts)

    return fid


def compute_hellinger_fidelity(circuit,pass_manager,backend,pmstr):
    """
    :param circuit:
    :type circuit: QuantumCircuit
    :param pass_manager:
    :type pass_manager: PassManager
    """    

    # optimise circuit using pass manager
    opt_circ = pass_manager.run(circuit)
    
    ideal_simulator = AerSimulator()
    ideal_counts = ideal_simulator.run(circuit).result().get_counts()
    plot_histogram(ideal_counts, filename = 'Ideal Counts'+pmstr)

    sampler = SamplerV2(mode=backend)
    job = sampler.run([opt_circ])
    print('Job ID: ',job.job_id())
    result = job.result()[0]
    counts = result.data.meas.get_counts()
    plot_histogram(counts,filename='Counts Hardware'+pmstr)

    fid = hellinger_fidelity(ideal_counts,counts)

    return fid

from qiskit import QuantumCircuit, transpile
from CustomPass import CustomOptimisationPass
from NoiseModel import CustomNoise
from NativeGateMapping import NativeGateMap
from qiskit.transpiler import PassManager
import numpy as np

#CIRC---------------------------------------------------------------------------------

circ = QuantumCircuit(4)
circ.rx(np.pi/2,0)
circ.cx(0,1)
circ.z(1)
circ.x(0)
circ.y(3)
circ.cx(0,3)
circ.cz(1,0)
circ.y(0)
circ.cx(0,1)
circ.z(1)
circ.x(1)
circ.x(1)
circ.ry(np.pi/2,0)
circ.cx(2,1)
circ.cx(0,1)
circ.rx(np.pi/2,2)
circ.cx(0,3)
circ.z(3)
circ.z(3)
circ.x(0)
circ.ry(np.pi/2,1)
circ.x(2)
circ.cz(3,2)
circ.y(2)
circ.cx(2,0)
circ.cx(2,3)
circ.rz(3*np.pi/2,0)
circ.cx(2,3)
circ.cx(2,3)
circ.z(3)
circ.x(3)
circ.ry(np.pi/2,2)
circ.cx(2,3)

circ.draw(output = 'mpl', filename = '1')

#transpile the circuit into the supported native gate set of ibm_aachen
ng_circ = transpile(circ, optimization_level = 0, basis_gates=['cz','id','rz','sx','x'])
ng_circ.measure_all()

ng_circ.draw(output = 'mpl', filename = '2')

#CUSTOM--------------------------------------------------------------------------------

service = QiskitRuntimeService()
backend = service.backend("ibm_aachen")
noise_model = NoiseModel.from_backend(backend)

# Generate the custom optimisation pass and set the noise model
custom_pass = CustomOptimisationPass()
custom_pass.set_noise_model(noise_model)


# Generate the optimisation passmanager using the custom pass
pm = PassManager([custom_pass])

#HARDWARE-------------------------------------------------------------------------------------

pm_q = generate_preset_pass_manager(backend = backend, optimization_level=3)

#SIMULATE FIDS----------------------------------------------------------------------------------

opt_custom = pm.run(ng_circ)
opt_qiskit = pm_q.run(ng_circ)

opt_custom.draw(output = 'mpl', filename = '3')
opt_qiskit.draw(output = 'mpl', filename = '4')

fid_custom = simulate_hellinger_fidelity(opt_custom,noise_model)
fid_qiskit = simulate_hellinger_fidelity(opt_qiskit,noise_model)

print("Custom:")
print(fid_custom)
print("Qiskit:")
print(fid_qiskit)

print("Custom vs Qiskit: "+str(np.round(100*(fid_custom - fid_qiskit),3))+"%")