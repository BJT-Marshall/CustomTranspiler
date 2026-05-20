# CustomTranspiler

A modular quantum transpilation pipeline implementing custom noise‑aware optimisation, native‑gate decomposition, and fidelity‑based evaluation for superconducting qubit-based quantum hardware.
Built using Qiskit, with a focus on hardware‑aware noise modelling, realistic gate set decomposition, and modular optimisation pass design.

This project demonstrates competence with:

    Quantum circuit optimisation
    Custom Qiskit transpiler passes
    Hardware‑motivated noise modelling
    Parametric gate handling and decomposition
    End‑to‑end workflow design for quantum software stacks
    Benchmarking & fidelity evaluation

## Overview

Current quantum hardware suffers from gate errors, short coherence times, and restrictive native gate sets. Efficient computation therefore requires:

    Mapping logical circuits to specific hardware native gate sets
    Accurately modelling hardware inspired noise
    Optimising circuits with respect to that noise model, not just gate count
    Evaluating improvements through depth and fidelity

CustomTranspiler implements a miniature but realistic version of a quantum software stack:

## Core Components

    Custom Noise Model
    A superconducting qubit-based hardware inspired noise model incorporating:
        Thermal relaxation errors (T1/T2)
        Depolarizing channels (1‑ and 2‑qubit)
        Parameter‑dependent rotation noise channels
        (larger rotation angles → stronger decoherence/drive errors)

    Custom Transpiler Optimisation Pass
        Cancels pairs of identical hermetian gates
        Merges consecutive rotation gates while checking noise costs
        Swaps commuting gates to expose new optimisation patterns
        Works directly on the Qiskit DAGCircuit representation

    Native Gate Mapping
        Decomposes supported gates into the native gate set
        {RZ(θ),SX,CX}{RZ(θ),SX,CX}
        Uses analytical decompositions for
        X, Y, Z, RX, RY, RZ and their controlled variants

    Simulation & Benchmarking
        Fidelity comparison (ideal vs noise)
        Random circuit generation
        Depth/error ratio plots
        End‑to‑end workflow evaluation

## Repository Structure

    CustomTranspiler/
    │
    ├── CustomPass.py               # Custom OptimisationPass implementation
    ├── NoiseModel.py               # Superconducting qubit-based hardware-inspired custom noise model
    ├── NativeGateMapping.py        # Gate decomposition into the native gate set {RZ, SX, CX}
    ├── Simulations.py              # Fidelity simulators using AerSimulator
    ├── OptimizationPassTest.py     # Benchmarking & workflow utilities

## Installation

    bash
    
    pip install qiskit qiskit-aer numpy matplotlib

## Clone the repo:

    bash
    
    git clone [github.com](https://github.com/BJT-Marshall/CustomTranspiler.git)cd CustomTranspiler
