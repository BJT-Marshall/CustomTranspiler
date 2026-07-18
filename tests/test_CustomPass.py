from CustomTranspilation.CustomPass import CustomOptimisationPass
from qiskit.transpiler import PassManager
from CustomTranspilation.NoiseModel import CustomNoise
from qiskit import QuantumCircuit

# Testing suite for CustomPass.py

def optimise_circuit(circuit):

    noise_model_generator = CustomNoise()
    example_noise_model = noise_model_generator.noise_model(circuit)

    # Generate the custom optimisation pass and set the noise model
    custom_pass = CustomOptimisationPass()
    custom_pass.set_noise_model(noise_model_generator)

    # Generate the optimisation passmanager using the custom pass
    pm = PassManager([custom_pass])

    # Optimise the circuit with respect to the custom noise model
    optimised_example_circuit = pm.run(circuit)

    return circuit


class test_gate_cancellation():

    def test_xx(self):
        circ = QuantumCircuit(1)
        circ.x(0)
        circ.x(0)
        print(circ.count_ops()['x'])

        opt_circ = optimise_circuit(circ)
        print(opt_circ.count_ops()['x'])

        assert opt_circ.count_ops()['x'] == 0


t = test_gate_cancellation()
t.test_xx()


