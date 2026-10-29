
from src.processors import load_processor, validate_processor_d

# Load Processor D
processor_d = load_processor("processor_D")

# Validate against the PS-O3 requirement of 9 qubits
try:
    validate_processor_d(processor_d, required_qubits=9)

    print("================================")
    print("Processor D Validation")
    print("================================")
    print("Qubit count: PASS")
    print("Connectivity: PASS")
    print("Maximum degree: PASS")
    print("Basis gates: PASS")
    print("Noise rates: PASS")
    print("--------------------------------")
    print("Processor D is VALID!")
    print("================================")

except ValueError as error:
    print("Processor D validation FAILED:")
    print(error)
