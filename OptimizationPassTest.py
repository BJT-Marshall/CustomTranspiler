from qiskit import QuantumCircuit, transpile, ClassicalRegister
from qiskit.transpiler import PassManager
from CustomPass import CustomOptimizationPass
from NoiseModel import error_cost_function
from qiskit.circuit.random import random_circuit


def example_qc():
    qc = QuantumCircuit(2)
    qc.x(0)
    qc.x(0)
    qc.cx(0,1)
    qc.cx(0,1)
    qc.barrier()
    qc.y(0)
    qc.y(0)
    qc.z(0)
    qc.cx(1,0)
    qc.rx(0.5,0)
    qc.rx(0.3,0)
    qc.crx(0.2,0,1)
    qc.crx(0.2,0,1)
    qc.ry(0.2,0)
    qc.ry(0.2,0)
    qc.rz(0.6,0)
    qc.crx(0.3,1,0)
    qc.ry(0.2,0)
    c = ClassicalRegister(1)
    qc.add_register(c)
    qc.measure(0,0)

    return qc

def print_circ_metrics(original_qc, optimised_qc):
    
    print("Original circuit:")
    print(original_qc)

    print("Optimized circuit:")
    print(optimised_qc)

    print("Circuit Depths:")
    print("Un-optimized: ",original_qc.depth())
    print("Optimized: ",optimised_qc.depth())

    print("\nErrors:")
    print("Un-optimized: ",error_cost_function(original_qc))
    print("Optimized: ",error_cost_function(optimised_qc))
    print("Error Ratio: ",round(100*error_cost_function(optimised_qc)/error_cost_function(original_qc),2),"%")
    print("\nRandom Circuit No. ",count)

    return None

pm = PassManager([CustomOptimizationPass()])

qc = random_circuit(num_qubits=2, depth=10, max_operands=2)
optimized_qc = pm.run(qc)

count = 0
while qc.depth() == optimized_qc.depth():
    qc = random_circuit(num_qubits=2, depth=10, max_operands=2)
    optimized_qc = pm.run(qc)
    count+=1

print_circ_metrics(qc,optimized_qc)
