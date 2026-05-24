from CustomPass import CustomOptimisationPass
from NoiseModel import CustomNoise
from NativeGateMapping import NativeGateMap
from Simulations import simulate_ideal_vs_noise
from qiskit import QuantumCircuit, qpy
from qiskit.transpiler import PassManager
import matplotlib.pyplot as plt
import random
import numpy as np
import re

# Native Gate Map
ngMap = NativeGateMap()

# Load the test batch of circuits each containing 10 qubits with a minimum depth of 50: 

with open("Test_Batch_Q10D50.qpy", "rb") as file:
    loaded_circuits = qpy.load(file)
    file.close()

# Load the example circuit containing 4 qubits with a depth of 20:
with open("Example_Circuit.qpy", "rb") as file:
    loaded_circuit = qpy.load(file)
    example_circuit = loaded_circuit[0]
    file.close()

# Methods for generation of random circuits compatable with the custom optimisation pass, used for testing and benchmarking.

def apply_XYZ(circ: QuantumCircuit, gate_name: str, qubits: list, theta = None):
    """
    Helper method to apply the correct gate given a gate name string from the defined set of allowed gates in 
    :python:`custom_random_circuit`.
    """
    if "x" in gate_name:
        if gate_name == "sx":
            circ.sx(qubits[0])
        if len(qubits) == 2 and theta == None:
            circ.cx(qubits[0],qubits[1])
        elif len(qubits) == 2 and theta != None:
            circ.crx(theta,qubits[0],qubits[1])
        elif len(qubits) == 1 and theta != None:
            circ.rx(theta,qubits[0])
        else:
            circ.x(qubits[0])
    if "y" in gate_name:
        if len(qubits) == 2 and theta == None:
            circ.cy(qubits[0],qubits[1])
        elif len(qubits) == 2 and theta != None:
            circ.cry(theta,qubits[0],qubits[1])
        elif len(qubits) == 1 and theta != None:
            circ.ry(theta,qubits[0])
        else:
            circ.y(qubits[0])
    if "z" in gate_name:
        if len(qubits) == 2 and theta == None:
            circ.cz(qubits[0],qubits[1])
        elif len(qubits) == 2 and theta != None:
            circ.crz(theta,qubits[0],qubits[1])
        elif len(qubits) == 1 and theta != None:
            circ.rz(theta,qubits[0])
        else:
            circ.z(qubits[0])
    
    return circ

def custom_random_circuit(num_qubits:int,depth:int):
    """
    Generates a random circuit using the set of gates :math:`X, Y, Z, RX, RY, RZ` and their controlled variants (e.g. :math:`CRX`).

    :param num_qubits: Number of qubits in the generated circuit.
    :type num_qubits: int
    :param depth: Minimum depth of the generated circuit. Circuit depth may exceed this value due to controlled operations increasing the depth of their target wires.
    :type depth: int
    :returns qc: The randomly generated quantum circuit.
    :rtype: QuantumCircuit
    """

    qc = QuantumCircuit(num_qubits)
    gate_set = ["x","y","z","rx","ry","rz","cx","cy","cz","crx","cry","crz","sx"]

    for i in range(depth):
        for j in range(num_qubits):
            gate_name = gate_set[random.randint(0,len(gate_set))-1]
            if "c" in gate_name and "r" not in gate_name:
                qubit = random.randint(0, num_qubits-1)
                #Prevents control gates being mapped to a single qubit
                while qubit == j:
                    qubit = random.randint(0, num_qubits-1)
                qc = apply_XYZ(circ = qc,gate_name = gate_name, qubits = [j,qubit])
            if "r" in gate_name and "c" not in gate_name:
                theta = random.uniform(0,2*np.pi)
                qc = apply_XYZ(circ = qc,gate_name = gate_name, qubits = [j], theta = theta)
            if len(gate_name) == 3:
                theta = random.uniform(0,2*np.pi)
                qubit = random.randint(0, num_qubits-1)
                #Prevents control gates being mapped to a single qubit
                while qubit == j:
                    qubit = random.randint(0, num_qubits-1)
                qc = apply_XYZ(circ = qc,gate_name = gate_name, qubits = [j,qubit], theta = theta)
            else:
                qc = apply_XYZ(circ = qc,gate_name = gate_name, qubits = [j])

    return qc

    
# ----------------------------Example using the example circuit (imported from Example_Circuit.qpy):----------------------------

# What metrics to measure to maximise performance:

# Fidelity - Minimise the errors propogated through the circuit
# Duration - Minimise the duration of the circuit to reduce error accumulated through each operation 
#            (estimating this requires a specific choice of hardware and will not be focussed on here)
# Depth - Minimise the depth of the circuit to reduce error accumulated through many operations

# Typically:
# 
# Lower Depth -> Lower Duration -> Higher Fidelity
# 
# However, not every gate behaves the same and accumulates the same error over the same duration, hence the final goal should
# be the maximisation of fidelity with the depth and duration being important, but secondary, metrics to support this goal. 

# Native Gate Set Decompositions:

# For meaningful performance metrics to be aquirred for the optimisation pass, the circuit must first be decomposed into a native
# gate set, as it is this circuit that could actually be executed on real hardware. The native gate set used in NativeGateMap is 
# the set (RZ,CX,SX), a commonly used native gate set in superconducting qubit-based quantum hardware.
#

# Decompose the example circuit into the native gate set
example_circuit_decomp = ngMap.map(example_circuit)

# Generate the custom noise model
noise_model_generator = CustomNoise()
example_noise_model = noise_model_generator.noise_model(example_circuit_decomp)

# Generate the custom optimisation pass and set the noise model
custom_pass = CustomOptimisationPass()
custom_pass.set_noise_model(noise_model_generator)

# Generate the optimisation passmanager using the custom pass
pm = PassManager([custom_pass])

# Optimise the circuit with respect to the custom noise model
optimised_example_circuit = pm.run(example_circuit_decomp)

# Generate the custom noise model for the optimised circuit
noise_model_generator = CustomNoise()
optimised_noise_model = noise_model_generator.noise_model(optimised_example_circuit)


# Metric #1: Fidelity:

# The fidelity of the example circuit and the optimised example circuit:
example_fidelity = simulate_ideal_vs_noise(circuit = example_circuit_decomp, noise_model = example_noise_model) # ~0.914
optimised_fidelity = simulate_ideal_vs_noise(circuit = optimised_example_circuit, noise_model = optimised_noise_model) # ~0.953

print("\nExample Fidelity:\n")
print("Example circuit fidelity: ",np.round(example_fidelity,3))
print("Optimised example circuit fidelity: ",np.round(optimised_fidelity,3))

# Metric #2: Depth:

# The depth of the example circuit and the optimised example circuit:
example_depth = example_circuit_decomp.depth() # 74
optmised_example_depth = optimised_example_circuit.depth() # 48

print("\nExample Depth:\n")
print("Example circuit depth: ",example_depth)
print("Optimised example circuit depth: ",optmised_example_depth)


#----------------------------Example batch using the test batch (imported from Test_Batch_Q10D50.qpy):----------------------------


# Helper function to generate the native gate set decomposition, noise model, optimisation pass and optimised circuit

def general_circuit_workflow(circuit: QuantumCircuit):
    
    # Decompose the example circuit into the native gate set
    circuit_decomp = ngMap.map(circuit)

    # Generate the custom noise model
    noise_model_generator = CustomNoise()
    noise_model = noise_model_generator.noise_model(circuit_decomp)

    # Generate the custom optimisation pass and set the noise model
    custom_pass = CustomOptimisationPass()
    custom_pass.set_noise_model(noise_model_generator)

    # Generate the optimisation passmanager using the custom pass
    pm = PassManager([custom_pass])

    # Optimise the circuit with respect to the custom noise model
    optimised_circuit = pm.run(circuit_decomp)

    # Generate the custom noise model for the optimised circuit
    noise_model_generator = CustomNoise()
    optimised_noise_model = noise_model_generator.noise_model(optimised_example_circuit)

    noise_models = [noise_model, optimised_noise_model]

    return circuit_decomp, optimised_circuit, noise_models

# Set 'run = True' to run the optimisation and fidelity simulations for the test batch of circuit
run = False

if run:
    data = {
    'optimised_circuits' : [],
    'fidelity' : [],
    'optimised_fidelity' : [],
    'depth' : [],
    'optimised_depth' : []
    }
    for circ in loaded_circuits:
        circuit_decomp, optimised_circ, noise_models = general_circuit_workflow(circ)
        data['optimised_circuits'].append(optimised_circ)
        data['fidelity'].append(simulate_ideal_vs_noise(circuit_decomp, noise_models[0]))
        data['optimised_fidelity'].append(simulate_ideal_vs_noise(optimised_circ, noise_models[1]))
        data['depth'].append(circuit_decomp.depth())
        data['optimised_depth'].append(optimised_circ.depth())

    with open("Test_Batch_Optimised_Q10D50.qpy", "wb") as file:
        qpy.dump(data['optimised_circuits'],file)
        file.close()

    with open("Test_Batch_Data_Q10D50", "w") as file:
        for i in range(len(data['fidelity'])):
            file.write(str(data['fidelity'][i])+","+str(data['optimised_fidelity'][i])+","+str(data['depth'][i])+","+str(data['optimised_depth'][i])+"\n")
        file.close()

# Helper function to reformat the data entries

def read_entry(data_string: str):
    data_entry = []
    split_string = data_string.split(',')
    for element in split_string:
        data_entry.append(float(element)) 

    return data_entry

if not run:

    # Read back in fidelity and depth data

    data = {
    'optimised_circuits' : [],
    'fidelity' : [],
    'optimised_fidelity' : [],
    'depth' : [],
    'optimised_depth' : []
    }

    with open("Test_Batch_Data_Q10D50", "r") as file:
        for i in range(len(loaded_circuits)):
            next_str = file.readline()
            next_data = read_entry(next_str)
            data['fidelity'].append(next_data[0])
            data['optimised_fidelity'].append(next_data[1])
            data['depth'].append(next_data[2])
            data['optimised_depth'].append(next_data[3])
        file.close()

# Plot fidelity and optimised fidelity

circuit_numbers = [x for x in range(len(data['fidelity']))]

plt.plot(circuit_numbers, data['fidelity'], color = 'b', label = 'Original Circuit Fidelity')
plt.plot(circuit_numbers, data['optimised_fidelity'], color = 'r', label = 'Optimised Circuit Fidelity')
plt.legend()
plt.xlabel('Circuit Number')
plt.ylabel('Circuit Fidelity')
plt.title('Original and Optimised Fidelity for Circuits in Test_Batch_Q10D50')
plt.savefig('Test_Batch_Fidelity_Plot')
plt.clf()

# Average fidelity and average optimised

print("\nBatch Fidelity:\n")

print("Average fidelity of batch circuits: ",np.round(np.average(data['fidelity']),3))
print("Average fidelity of optimised circuits: ",np.round(np.average(data['optimised_fidelity']),3))

# Average absolute increase in fidelity

print("Average absolute increase in fidelity: +",np.round(np.average(data['optimised_fidelity']) - np.average(data['fidelity']),3))

# Plot depth and optimised depth

circuit_numbers = [x for x in range(len(data['fidelity']))]

plt.plot(circuit_numbers, data['depth'], color = 'b', label = 'Original Circuit Depth')
plt.plot(circuit_numbers, data['optimised_depth'], color = 'r', label = 'Optimised Circuit Depth')
plt.legend()
plt.xlabel('Circuit Number')
plt.ylabel('Circuit Depth')
plt.title('Original and Optimised Depth for Circuits in Test_Batch_Q10D50')
plt.savefig('Test_Batch_Depth_Plot')
plt.clf()

# Average depth and optimised depth

print("\nBatch Depth:\n")

print("Average depth of batch circuits: ",np.round(np.average(data['depth']),2))
print("Average depth of optimised circuits: ",np.round(np.average(data['optimised_depth']),2))

# Average decrease in depth

print("Average decrease in circuit depth: ",-100*np.round((np.average(data['optimised_depth']) - np.average(data['depth']))/np.average(data['depth']),2),"%")