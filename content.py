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
        "title": "1. Quantum circuit basics",
        "short_title": "Circuit basics",
        "concepts": ["Quantum circuit", "Classical vs quantum"],
        "duration": "8–10 min",
        "level": "Foundation",
        "objective": "Build a mental model of a minimal quantum program: qubits, classical bits, gates, measurement, and output.",
        "why_it_matters": "Before discussing probabilities or algorithms, learners need to see that Qiskit code describes a circuit rather than an ordinary sequential classical program.",
        "big_idea": "A quantum circuit is a structured plan: qubits carry quantum states, gates transform them, and measurement writes classical data that can be read after execution.",
        "concept": "In Qiskit, QuantumCircuit(1, 1) allocates one qubit and one classical bit. The instruction qc.measure(0, 0) measures qubit 0 and stores its result in classical bit 0.",
        "qiskit_code": """from qiskit import QuantumCircuit

qc = QuantumCircuit(1, 1)
qc.measure(0, 0)
print(qc)""",
        "code_focus": ["QuantumCircuit(1, 1) means one qubit and one classical bit.", "measure(0, 0) maps qubit 0 to classical bit 0.", "The circuit diagram is read left-to-right."],
        "visual_steps": ["Locate the quantum wire q0.", "Find the measurement symbol M.", "Follow the arrow into the classical output bit c0."],
        "before_measurement": "The qubit is initialized to |0> unless a gate changes it.",
        "after_measurement": "The result is stored as a classical value. In this minimal example the expected result is 0.",
        "misconception": "Do not treat the circuit as a Python print statement. It is a model of quantum and classical resources.",
        "mini_task": "Point to the exact line of code that creates the classical bit, then explain why it is needed.",
        "check_question": "Why does QuantumCircuit(1, 1) include two numbers instead of one?",
        "reflective_prompt": "Explain, in your own words, how the Qiskit code maps to the circuit diagram and output bit.",
        "can_do": ["Identify qubit and classical registers", "Explain why measurement needs a classical bit", "Connect a minimal Qiskit program to a circuit diagram"],
    },
    {
        "id": "qubit_measurement",
        "title": "2. Qubit state and measurement",
        "short_title": "Measurement",
        "concepts": ["Qubit, state, and measurement", "Measurement"],
        "duration": "10–12 min",
        "level": "Foundation",
        "objective": "Distinguish the quantum state before measurement from the classical outcome after measurement.",
        "why_it_matters": "Many beginners imagine measurement as revealing a hidden classical value. This module builds the more accurate idea that measurement produces classical data from a quantum state.",
        "big_idea": "Measurement is the boundary between quantum information and classical information.",
        "concept": "Before measurement, a qubit is described by a quantum state. After measurement, a single shot produces one classical outcome, stored in a classical bit.",
        "qiskit_code": """from qiskit import QuantumCircuit

qc = QuantumCircuit(1, 1)
# The qubit starts in |0>
qc.measure(0, 0)""",
        "code_focus": ["The qubit exists before the result is known.", "The classical bit stores the measured value.", "A single shot gives one observed outcome."],
        "visual_steps": ["Start at the prepared qubit state.", "Move through the measurement symbol.", "Read the final classical value."],
        "before_measurement": "The system is described as a quantum state. If no gate has been applied, the default state is |0>.",
        "after_measurement": "The output is a classical 0 or 1. For |0>, repeated measurements should give 0.",
        "misconception": "Measurement is not simply displaying the full state vector. It produces a classical sample.",
        "mini_task": "Explain why a program can have a qubit before it has a classical measurement result.",
        "check_question": "What is stored in the classical bit after measurement?",
        "reflective_prompt": "Why do we need a classical bit when we measure a qubit in Qiskit?",
        "can_do": ["Separate state preparation from measurement", "Explain why measurement produces classical data", "Interpret qc.measure(0, 0)"],
    },
    {
        "id": "hadamard_superposition",
        "title": "3. Hadamard and superposition",
        "short_title": "Hadamard",
        "concepts": ["Hadamard gate", "Classical vs quantum"],
        "duration": "12–15 min",
        "level": "Core concept",
        "objective": "Explain how H applied to |0> creates a balanced probability pattern after many measurements.",
        "why_it_matters": "Hadamard is the first gate where learners experience a clearly non-classical pattern: one prepared state can lead to different observed outcomes across shots.",
        "big_idea": "H changes the state before measurement; measurement samples from the probabilities created by that state.",
        "concept": "Applying H to |0> prepares an equal superposition. Each shot still returns one classical bit, but over many shots the counts are expected to be approximately balanced between 0 and 1.",
        "qiskit_code": """from qiskit import QuantumCircuit

qc = QuantumCircuit(1, 1)
qc.h(0)
qc.measure(0, 0)""",
        "code_focus": ["qc.h(0) applies H to qubit 0.", "The gate changes the state before measurement.", "The histogram summarizes many single-shot outcomes."],
        "visual_steps": ["Compare the state before and after H.", "Notice that measurement still returns one bit per shot.", "Read the histogram as an approximate distribution."],
        "before_measurement": "After H, the qubit is not a definite classical 0 or 1.",
        "after_measurement": "Across many shots, 0 and 1 appear with similar frequencies.",
        "misconception": "Superposition is more precise than saying the qubit is simply 'both values at once'.",
        "mini_task": "Predict what the histogram should look like after 1000 shots, then compare your idea with the visual.",
        "check_question": "Why do we need many shots to see the 50/50 pattern?",
        "reflective_prompt": "Explain what changes before and after measurement when H is applied to |0>.",
        "can_do": ["Describe the effect of H on |0>", "Predict an approximately balanced distribution", "Avoid a hidden-classical-value interpretation"],
    },
    {
        "id": "shots_counts",
        "title": "4. Shots and counts",
        "short_title": "Counts",
        "concepts": ["Shots and counts", "Measurement"],
        "duration": "8–10 min",
        "level": "Interpretation",
        "objective": "Read a counts dictionary as repeated samples of a quantum circuit's measurement outcomes.",
        "why_it_matters": "Quantum programming often produces distributions. Learners must interpret samples rather than expect one deterministic answer.",
        "big_idea": "A shot is one execution. Counts are the accumulated evidence from repeated executions.",
        "concept": "The same circuit can be executed many times. Qiskit reports a dictionary such as {'0': 513, '1': 487}, meaning outcome 0 occurred 513 times and outcome 1 occurred 487 times.",
        "qiskit_code": """# Example result after repeated execution
counts = {'0': 513, '1': 487}
print(counts)""",
        "code_focus": ["Dictionary keys are observed bitstrings.", "Dictionary values are frequencies.", "More shots usually make patterns easier to see."],
        "visual_steps": ["Compare 10 shots with 1000 shots.", "Notice that both are samples.", "Use proportions, not just raw counts, when interpreting results."],
        "before_measurement": "The circuit defines probabilities for possible outcomes.",
        "after_measurement": "Counts summarize observed classical bitstrings across repeated shots.",
        "misconception": "Different counts do not mean the simulator is broken; they reflect sampling variation.",
        "mini_task": "Convert {'0': 513, '1': 487} into approximate percentages.",
        "check_question": "What does a shot represent in a Qiskit experiment?",
        "reflective_prompt": "If counts are {'0': 513, '1': 487}, what does that say about the underlying measurement distribution?",
        "can_do": ["Define a shot", "Read a counts dictionary", "Distinguish deterministic output from sampled distribution"],
    },
    {
        "id": "cnot_correlation",
        "title": "5. CNOT and correlated outcomes",
        "short_title": "CNOT",
        "concepts": ["CNOT gate", "Entanglement intuition"],
        "duration": "12–15 min",
        "level": "Two-qubit reasoning",
        "objective": "Explain the control-target structure of CNOT and interpret correlated two-qubit outcomes.",
        "why_it_matters": "CNOT introduces multi-qubit reasoning, a core requirement for understanding quantum algorithms and entanglement intuition.",
        "big_idea": "CNOT relates two qubits: the target flips only when the control is 1.",
        "concept": "CNOT has a control qubit and a target qubit. With H on the control followed by CNOT, repeated measurements often concentrate on correlated outcomes such as 00 and 11.",
        "qiskit_code": """from qiskit import QuantumCircuit

qc = QuantumCircuit(2, 2)
qc.h(0)
qc.cx(0, 1)
qc.measure([0, 1], [0, 1])""",
        "code_focus": ["qc.cx(0, 1) means qubit 0 controls qubit 1.", "The target flips when the control is 1.", "H before CNOT creates the possibility of correlated outcomes."],
        "visual_steps": ["Find the filled control dot.", "Follow the vertical line to the target.", "Use the rule table to predict target changes."],
        "before_measurement": "H prepares the first qubit in superposition; CNOT correlates the second qubit with it.",
        "after_measurement": "Across many shots, 00 and 11 are expected more often than 01 and 10 in the Bell-style circuit.",
        "misconception": "CNOT is not a general copying operation for arbitrary quantum states.",
        "mini_task": "Use the rule table to predict the target output when the control is 1 and the target starts as 0.",
        "check_question": "Which qubit is the control in qc.cx(0, 1)?",
        "reflective_prompt": "Why can H followed by CNOT produce correlated outcomes such as 00 and 11?",
        "can_do": ["Identify control and target qubits", "Apply the CNOT rule", "Interpret correlated two-qubit outcomes"],
    },
    {
        "id": "qiskit_debugging",
        "title": "6. Qiskit syntax and debugging",
        "short_title": "Debugging",
        "concepts": ["Qiskit syntax", "Debugging"],
        "duration": "10–12 min",
        "level": "Practice",
        "objective": "Identify and fix common beginner mistakes in introductory Qiskit circuits.",
        "why_it_matters": "Syntax errors often reveal conceptual errors about resources, indexing, and measurement mapping.",
        "big_idea": "Debug Qiskit by checking resources first: qubits, classical bits, indices, then gate order.",
        "concept": "Most beginner mistakes come from missing classical bits, measuring into unavailable indices, confusing control and target order, or forgetting that measurement output is classical.",
        "qiskit_code": """from qiskit import QuantumCircuit

# Incorrect: no classical bit allocated
qc = QuantumCircuit(1, 0)
qc.measure(0, 0)

# Correct
qc = QuantumCircuit(1, 1)
qc.measure(0, 0)""",
        "code_focus": ["The second number in QuantumCircuit is the number of classical bits.", "The second argument in measure is a classical-bit index.", "Fix the allocation before rerunning the circuit."],
        "visual_steps": ["Compare the incorrect and corrected code.", "Locate the missing classical bit.", "Explain why the corrected version can store the result."],
        "before_measurement": "A valid circuit must allocate a classical bit if a measurement result will be stored.",
        "after_measurement": "Correct allocation allows Qiskit to map qubit measurement results to classical bits.",
        "misconception": "The second argument in measure is not another qubit; it is the target classical bit.",
        "mini_task": "Explain why QuantumCircuit(1, 0) followed by qc.measure(0, 0) fails.",
        "check_question": "What should you check first when a measurement instruction fails?",
        "reflective_prompt": "Explain why QuantumCircuit(1, 0) followed by qc.measure(0, 0) is problematic and how to fix it.",
        "can_do": ["Detect missing classical-bit allocation", "Recognize measurement-index errors", "Rewrite a minimal circuit correctly"],
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
