"""Educational content and assessment instruments for the QAI pilot platform."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class MCQ:
    id: str
    concept: str
    question: str
    options: List[str]
    answer_index: int
    explanation: str


PRE_TEST: List[MCQ] = [
    MCQ(
        "pre_q1",
        "Quantum circuit",
        "In Qiskit, what does a QuantumCircuit(1, 1) usually represent?",
        [
            "A circuit with one quantum bit and one classical bit",
            "A circuit with one classical bit only",
            "A circuit with one quantum gate only",
            "A circuit that runs automatically on real quantum hardware",
        ],
        0,
        "QuantumCircuit(1, 1) allocates one qubit and one classical bit for measurement output.",
    ),
    MCQ(
        "pre_q2",
        "Qubit, state, and measurement",
        "Before any gate is applied, a newly created qubit in a basic circuit is usually initialized to:",
        ["|1>", "|0>", "A random classical bit", "Both 0 and 1 after measurement"],
        1,
        "A newly created qubit starts in state |0> by default.",
    ),
    MCQ(
        "pre_q3",
        "Hadamard gate",
        "What is the main role of a Hadamard gate H applied to |0>?",
        [
            "It deletes the qubit",
            "It creates a superposition state",
            "It measures the qubit immediately",
            "It converts a classical bit into a qubit",
        ],
        1,
        "H applied to |0> creates an equal superposition of |0> and |1>.",
    ),
    MCQ(
        "pre_q4",
        "Measurement",
        "What does measurement do in an introductory quantum circuit?",
        [
            "It copies the qubit without changing it",
            "It maps the quantum state to a classical outcome",
            "It increases the number of qubits",
            "It removes the need for classical bits",
        ],
        1,
        "Measurement converts quantum information into a classical result that can be read.",
    ),
    MCQ(
        "pre_q5",
        "Shots and counts",
        "Why are circuits often executed with many shots?",
        [
            "To estimate the distribution of possible measurement outcomes",
            "To make the circuit use fewer qubits",
            "To prevent measurement from occurring",
            "To automatically correct every programming error",
        ],
        0,
        "Many shots provide repeated samples, which are summarized as counts.",
    ),
    MCQ(
        "pre_q6",
        "CNOT gate",
        "In a CNOT gate, the target qubit is flipped when:",
        [
            "The control qubit is measured as 0",
            "The control qubit is in state 1",
            "The circuit has no classical bits",
            "The target qubit is measured first",
        ],
        1,
        "CNOT flips the target when the control is 1.",
    ),
    MCQ(
        "pre_q7",
        "Classical vs quantum",
        "Which statement best distinguishes a qubit from a classical bit before measurement?",
        [
            "A qubit can only store text",
            "A qubit can be described by amplitudes and may be in superposition",
            "A qubit is always exactly 0 or exactly 1 before measurement",
            "A qubit does not need any physical interpretation",
        ],
        1,
        "A qubit can be represented by amplitudes, and measurement gives classical outcomes probabilistically.",
    ),
    MCQ(
        "pre_q8",
        "Qiskit syntax",
        "In Qiskit, which line applies a Hadamard gate to qubit 0?",
        ["qc.h(0)", "qc.measure_all(0)", "qc.cnot(0)", "qc.bit(0)"],
        0,
        "qc.h(0) applies a Hadamard gate to qubit 0.",
    ),
    MCQ(
        "pre_q9",
        "Entanglement intuition",
        "A common purpose of using H on one qubit followed by CNOT is to demonstrate:",
        ["A syntax error", "Correlated quantum outcomes", "Classical sorting", "Database storage"],
        1,
        "H plus CNOT can create a simple Bell-state-like circuit with correlated outcomes.",
    ),
    MCQ(
        "pre_q10",
        "Debugging",
        "A frequent beginner mistake in Qiskit measurement is:",
        [
            "Using classical bits to store measurement results",
            "Measuring into a classical bit that was not allocated",
            "Executing circuits more than once",
            "Importing QuantumCircuit",
        ],
        1,
        "Measurement needs an available classical bit, such as QuantumCircuit(1, 1) then qc.measure(0, 0).",
    ),
]

POST_TEST: List[MCQ] = [
    MCQ(
        "post_q1",
        "Quantum circuit",
        "What are the two resources specified in QuantumCircuit(2, 2)?",
        [
            "Two Python functions and two files",
            "Two qubits and two classical bits",
            "Two simulations and two APIs",
            "Two measurement results only",
        ],
        1,
        "The first number allocates qubits and the second allocates classical bits.",
    ),
    MCQ(
        "post_q2",
        "Qubit, state, and measurement",
        "If a qubit remains in |0> and is measured many times, what result is expected?",
        ["Mostly 0", "Mostly 1", "Always a syntax error", "No classical output"],
        0,
        "A qubit left in |0> should produce 0 when measured in the computational basis.",
    ),
    MCQ(
        "post_q3",
        "Hadamard gate",
        "After applying H to |0> and measuring many shots, the counts should be approximately:",
        ["Only 0", "Only 1", "A balance between 0 and 1", "No result"],
        2,
        "The Hadamard gate creates a superposition that produces 0 and 1 with roughly equal probability.",
    ),
    MCQ(
        "post_q4",
        "Measurement",
        "Why is a classical bit used in qc.measure(0, 0)?",
        [
            "To store the measurement outcome of qubit 0",
            "To create another qubit",
            "To remove the quantum state without output",
            "To replace the simulator",
        ],
        0,
        "The second index identifies the classical bit used to store the measurement outcome.",
    ),
    MCQ(
        "post_q5",
        "Shots and counts",
        "If a result dictionary is {'0': 510, '1': 490}, what does it suggest?",
        [
            "An approximate 50/50 outcome distribution",
            "A broken simulator",
            "No measurement was performed",
            "The qubit was certainly |1>",
        ],
        0,
        "Counts near 50/50 are typical after H on |0> with many shots.",
    ),
    MCQ(
        "post_q6",
        "CNOT gate",
        "In a simple Bell-style circuit, why can outcomes 00 and 11 appear more often than 01 and 10?",
        [
            "Because the qubits are correlated by H and CNOT",
            "Because measurement was skipped",
            "Because classical bits create qubits",
            "Because shots always remove correlations",
        ],
        0,
        "H on the control followed by CNOT can create correlated measurement outcomes.",
    ),
    MCQ(
        "post_q7",
        "Classical vs quantum",
        "Why should a learner avoid saying that a superposed qubit is simply 'both classical values at once'?",
        [
            "Because qubits are only text labels",
            "Because amplitudes and measurement probabilities are more precise than that simplified phrase",
            "Because superposition cannot be simulated",
            "Because measurement is not allowed",
        ],
        1,
        "Superposition is better described through amplitudes and probabilities rather than as two ordinary bits.",
    ),
    MCQ(
        "post_q8",
        "Qiskit syntax",
        "Which instruction measures qubit 0 into classical bit 0?",
        ["qc.measure(0, 0)", "qc.h(0, 0)", "qc.cx(0)", "qc.qubit(0)"],
        0,
        "qc.measure(0, 0) measures qubit 0 and stores the result in classical bit 0.",
    ),
    MCQ(
        "post_q9",
        "Entanglement intuition",
        "Which pair of operations is commonly used to introduce correlated two-qubit outcomes?",
        ["H then CNOT", "Measure then delete", "Print then import", "Count then allocate"],
        0,
        "H on one qubit and CNOT to another is a standard introductory pattern for correlated outcomes.",
    ),
    MCQ(
        "post_q10",
        "Debugging",
        "A student writes QuantumCircuit(1, 0) then qc.measure(0, 0). What is the likely issue?",
        [
            "No classical bit was allocated for the measurement result",
            "Too many Hadamard gates were applied",
            "The qubit cannot start at |0>",
            "Qiskit cannot print circuits",
        ],
        0,
        "QuantumCircuit(1, 0) has no classical bit, so measuring into classical bit 0 is invalid.",
    ),
]

LESSONS: List[Dict] = [
    {
        "id": "orientation",
        "title": "1. Quantum programming orientation",
        "concepts": ["Quantum circuit", "Classical vs quantum"],
        "objective": "Understand the role of qubits, classical bits, gates, and measurement in a minimal Qiskit workflow.",
        "why_it_matters": "Students often try to read a quantum circuit as a classical program. This section builds a circuit-level view before discussing probability.",
        "concept": "A quantum program defines a circuit. A circuit contains qubits, classical bits, operations, and measurements. Qiskit lets learners build and inspect these circuits before execution.",
        "qiskit_code": """from qiskit import QuantumCircuit\n\nqc = QuantumCircuit(1, 1)\nqc.measure(0, 0)\nprint(qc)""",
        "before_measurement": "The qubit is initialized in |0>. No gate has changed its state.",
        "after_measurement": "The measurement stores the result in the classical bit. In this simple case, the expected result is 0.",
        "misconception": "A quantum circuit is not just a Python function. It is a structured description of quantum and classical resources.",
        "reflective_prompt": "Explain, in your own words, the difference between the qubit and the classical bit in this circuit.",
        "can_do": ["Identify qubit and classical registers in a circuit", "Explain what measurement adds to a circuit", "Connect a tiny Qiskit program to a circuit diagram"],
    },
    {
        "id": "qubit_measurement",
        "title": "2. Qubit, state, and measurement",
        "concepts": ["Qubit, state, and measurement", "Measurement"],
        "objective": "Describe what a qubit state means before measurement and what measurement produces afterward.",
        "why_it_matters": "Measurement is often misunderstood as simply reading a hidden classical value. This lesson frames measurement as the step that produces classical data.",
        "concept": "A qubit is described by a quantum state. Measurement maps that state to a classical outcome. The outcome is stored in a classical bit.",
        "qiskit_code": """from qiskit import QuantumCircuit\n\nqc = QuantumCircuit(1, 1)\n# Qubit 0 starts in |0>\nqc.measure(0, 0)\nprint(qc)""",
        "before_measurement": "The qubit has a quantum state. If no gate is applied, the state is |0>.",
        "after_measurement": "The classical bit receives the observed value. For |0>, repeated measurements should return 0.",
        "misconception": "Measurement is not just printing the state vector; it produces classical outcomes.",
        "reflective_prompt": "Why do we need a classical bit when we measure a qubit in Qiskit?",
        "can_do": ["Describe the qubit state before measurement", "Explain why measurement produces classical data", "Interpret the role of the classical bit"],
    },
    {
        "id": "hadamard_superposition",
        "title": "3. Hadamard gate and superposition",
        "concepts": ["Hadamard gate", "Classical vs quantum"],
        "objective": "Explain how the Hadamard gate creates a probabilistic measurement pattern from |0>.",
        "why_it_matters": "The Hadamard gate is a first example of a quantum operation whose behavior differs from deterministic classical assignment.",
        "concept": "Applying H to |0> creates a superposition. When measured many times, outcomes 0 and 1 tend to appear with similar frequencies.",
        "qiskit_code": """from qiskit import QuantumCircuit\n\nqc = QuantumCircuit(1, 1)\nqc.h(0)\nqc.measure(0, 0)\nprint(qc)""",
        "before_measurement": "After H, the qubit is in an equal superposition rather than a definite classical bit.",
        "after_measurement": "Each shot produces one classical outcome. Across many shots, both 0 and 1 should appear approximately equally.",
        "misconception": "Superposition is not the same as a classical variable that already has both values stored.",
        "reflective_prompt": "Explain what changes before and after measurement when H is applied to |0>.",
        "can_do": ["Explain the effect of H on |0>", "Predict an approximately balanced distribution", "Avoid interpreting superposition as a hidden classical value"],
    },
    {
        "id": "shots_counts",
        "title": "4. Shots, counts, and interpretation",
        "concepts": ["Shots and counts", "Measurement"],
        "objective": "Interpret a Qiskit counts dictionary as repeated samples of measurement outcomes.",
        "why_it_matters": "Beginners may expect one deterministic result. Counts help connect circuit behavior to probabilities.",
        "concept": "A shot is one execution of the circuit. Counts summarize how many times each measurement outcome occurred across repeated shots.",
        "qiskit_code": """# Example outcome after many shots\ncounts = {'0': 513, '1': 487}\nprint(counts)""",
        "before_measurement": "The circuit prepares a quantum state that determines probabilities of possible outcomes.",
        "after_measurement": "The counts dictionary summarizes observed classical strings and their frequencies.",
        "misconception": "Counts are not proof that the simulator is inconsistent; they represent repeated sampling.",
        "reflective_prompt": "If counts are {'0': 513, '1': 487}, what does that say about the underlying measurement distribution?",
        "can_do": ["Define a shot as one circuit execution", "Read a counts dictionary", "Distinguish exact results from sampled distributions"],
    },
    {
        "id": "cnot_correlation",
        "title": "5. CNOT gate and correlated outcomes",
        "concepts": ["CNOT gate", "Entanglement intuition"],
        "objective": "Describe the control-target structure of CNOT and interpret correlated two-qubit outcomes.",
        "why_it_matters": "CNOT introduces multi-qubit reasoning, which is central to quantum algorithms and entanglement intuition.",
        "concept": "CNOT uses a control qubit and a target qubit. The target flips when the control is 1. Combined with H, it can create correlated outcomes.",
        "qiskit_code": """from qiskit import QuantumCircuit\n\nqc = QuantumCircuit(2, 2)\nqc.h(0)\nqc.cx(0, 1)\nqc.measure([0, 1], [0, 1])\nprint(qc)""",
        "before_measurement": "H prepares the first qubit in superposition. CNOT correlates the target with the control.",
        "after_measurement": "Across many shots, outcomes such as 00 and 11 are expected more often than 01 and 10.",
        "misconception": "CNOT is not a simple copy operation for arbitrary quantum states.",
        "reflective_prompt": "Why can H followed by CNOT produce correlated outcomes such as 00 and 11?",
        "can_do": ["Identify control and target qubits", "Explain when the target flips", "Interpret correlated two-qubit outcomes"],
    },
    {
        "id": "qiskit_debugging",
        "title": "6. Common Qiskit mistakes",
        "concepts": ["Qiskit syntax", "Debugging"],
        "objective": "Identify and correct common beginner mistakes in introductory Qiskit circuits.",
        "why_it_matters": "Programming errors can hide conceptual misunderstandings, especially around qubit/classical-bit indexing.",
        "concept": "Many errors come from allocating the wrong number of classical bits, confusing control and target order, or measuring into unavailable bits.",
        "qiskit_code": """from qiskit import QuantumCircuit\n\n# Incorrect: no classical bit allocated\nqc = QuantumCircuit(1, 0)\nqc.measure(0, 0)\n\n# Correct version\nqc = QuantumCircuit(1, 1)\nqc.measure(0, 0)""",
        "before_measurement": "The circuit must allocate both the qubit to be measured and the classical bit that will store the result.",
        "after_measurement": "Correct allocation allows Qiskit to map qubit measurement outcomes to classical bits.",
        "misconception": "The second argument in measure is not another qubit; it is the classical bit index.",
        "reflective_prompt": "Explain why QuantumCircuit(1, 0) followed by qc.measure(0, 0) is problematic.",
        "can_do": ["Detect missing classical-bit allocation", "Recognize incorrect measurement indices", "Rewrite a minimal circuit correctly"],
    },
]

SURVEY_ITEMS = [
    ("scaffolding_clarity", "The step-by-step conceptual scaffolding helped me understand quantum programming concepts."),
    ("qiskit_examples", "The guided Qiskit examples helped me connect theory with code."),
    ("ai_feedback", "The AI-mediated feedback helped me identify and correct misunderstandings."),
    ("exercise_generation", "The AI-generated exercises were useful for practice."),
    ("reflection_prompts", "The reflective prompts encouraged me to think before relying on generated answers."),
    ("overreliance_awareness", "The platform helped me avoid simply copying AI-generated answers."),
    ("usability", "The platform was easy to use during the learning activity."),
]

OPEN_ENDED_ITEMS = [
    ("most_useful", "What was the most useful part of the platform?"),
    ("difficulties", "What difficulties did you face while learning quantum programming?"),
    ("ai_reflection", "Did the AI tutor help you think, or did it sometimes encourage over-reliance? Explain briefly."),
]


def questions_for(kind: str) -> List[MCQ]:
    if kind == "pre":
        return PRE_TEST
    if kind == "post":
        return POST_TEST
    raise ValueError(f"Unknown test kind: {kind}")


def lesson_by_id(lesson_id: str) -> Dict:
    for lesson in LESSONS:
        if lesson["id"] == lesson_id:
            return lesson
    raise KeyError(lesson_id)


CONCEPT_TO_LESSONS: Dict[str, List[str]] = {}
for lesson in LESSONS:
    for concept in lesson["concepts"]:
        CONCEPT_TO_LESSONS.setdefault(concept, []).append(lesson["id"])
