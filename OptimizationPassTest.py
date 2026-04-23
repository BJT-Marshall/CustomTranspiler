from qiskit import QuantumCircuit, transpile, ClassicalRegister
from qiskit.transpiler import PassManager
from CustomPass import CustomOptimizationPass
from NoiseModel import error_cost_function

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

print("Original circuit:")
print(qc)

pm = PassManager([CustomOptimizationPass()])
optimized_qc = pm.run(qc)

print("Optimized circuit:")
print(optimized_qc)

print("Errors:")
print("Un-optimized: ", error_cost_function(qc))
print("Optimized: ", error_cost_function(optimized_qc))
print("Error Ratio: ", round(100*error_cost_function(optimized_qc)/error_cost_function(qc),2),"%")

print(qc.data)

