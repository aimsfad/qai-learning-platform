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
    cognitive_level: str = "Understanding"


ASSESSMENT_BLUEPRINT: Dict[str, Dict[str, str]] = {
    "Circuit basics": {
        "lesson_id": "orientation",
        "description": "Qubits, classical bits, circuit structure, and measurement mapping.",
    },
    "Qubit measurement": {
        "lesson_id": "qubit_measurement",
        "description": "Distinguishing quantum state before measurement from classical outcome after measurement.",
    },
    "Hadamard and superposition": {
        "lesson_id": "hadamard_superposition",
        "description": "Understanding that H changes the state before measurement and leads to balanced sampled outcomes.",
    },
    "Shots and counts": {
        "lesson_id": "shots_counts",
        "description": "Interpreting repeated executions, sampling variation, and counts dictionaries.",
    },
    "CNOT and correlation": {
        "lesson_id": "cnot_correlation",
        "description": "Control-target reasoning and correlated two-qubit measurement outcomes.",
    },
    "Qiskit debugging": {
        "lesson_id": "qiskit_debugging",
        "description": "Diagnosing beginner errors in register allocation, measurement, and indexing.",
    },
}

PRE_TEST: List[MCQ] = [
    # Circuit basics — recall, understanding, application
    MCQ(
        "pre_cb_1",
        "Circuit basics",
        "In Qiskit, what does QuantumCircuit(1, 1) allocate?",
        [
            "One qubit and one classical bit",
            "One Hadamard gate and one measurement",
            "One simulator and one backend",
            "One classical bit only",
        ],
        0,
        "The first argument allocates qubits and the second allocates classical bits.",
        "Recall",
    ),
    MCQ(
        "pre_cb_2",
        "Circuit basics",
        "Which statement best describes a quantum circuit diagram?",
        [
            "A random drawing of Python instructions",
            "A left-to-right model of quantum operations and classical outputs",
            "A table of final grades",
            "A replacement for all Qiskit code",
        ],
        1,
        "A circuit diagram visually represents how qubits are transformed and measured over time.",
        "Understanding",
    ),
    MCQ(
        "pre_cb_3",
        "Circuit basics",
        "A circuit has q0 and c0. What does c0 normally store after measurement?",
        [
            "The quantum state itself",
            "The classical measurement result",
            "The name of the simulator",
            "The Hadamard matrix",
        ],
        1,
        "Classical bits store measured classical outcomes, not the full quantum state.",
        "Application",
    ),

    # Qubit measurement — recall, understanding, application
    MCQ(
        "pre_qm_1",
        "Qubit measurement",
        "Before any gate is applied, a newly allocated qubit is usually initialized as:",
        ["|1>", "|0>", "A random bit", "A measured classical value"],
        1,
        "Introductory Qiskit circuits normally start newly allocated qubits in |0>.",
        "Recall",
    ),
    MCQ(
        "pre_qm_2",
        "Qubit measurement",
        "What is the main role of measurement in an introductory circuit?",
        [
            "It stores a quantum state inside another qubit",
            "It converts a quantum state into a classical outcome for one run",
            "It automatically creates superposition",
            "It removes the need for classical bits",
        ],
        1,
        "Measurement is the boundary where quantum information becomes readable classical data.",
        "Understanding",
    ),
    MCQ(
        "pre_qm_3",
        "Qubit measurement",
        "If q0 is still in |0> and you measure it many times in the computational basis, what should you expect ideally?",
        ["Mostly 0", "Mostly 1", "Exactly half 0 and half 1", "No output"],
        0,
        "A qubit left in |0> should produce 0 in an ideal computational-basis measurement.",
        "Application",
    ),

    # Hadamard — recall, understanding, application
    MCQ(
        "pre_h_1",
        "Hadamard and superposition",
        "Which Qiskit instruction applies a Hadamard gate to qubit 0?",
        ["qc.h(0)", "qc.measure(0, 0)", "qc.cx(0, 1)", "qc.counts(0)"],
        0,
        "qc.h(0) applies H to qubit 0.",
        "Recall",
    ),
    MCQ(
        "pre_h_2",
        "Hadamard and superposition",
        "What does H do when applied to |0> in the introductory model?",
        [
            "It measures the qubit immediately",
            "It prepares a state that can produce 0 or 1 when measured repeatedly",
            "It creates a classical bit",
            "It deletes the circuit",
        ],
        1,
        "H changes the state before measurement; many shots reveal the resulting probability pattern.",
        "Understanding",
    ),
    MCQ(
        "pre_h_3",
        "Hadamard and superposition",
        "A circuit applies H to |0> and then measures 1000 shots. Which result is most plausible ideally?",
        ["{'0': 1000, '1': 0}", "{'0': 0, '1': 1000}", "{'0': 510, '1': 490}", "No counts can be produced"],
        2,
        "After H on |0>, counts should be approximately balanced, with small sampling variation.",
        "Application",
    ),

    # Shots and counts — recall, understanding, application
    MCQ(
        "pre_sc_1",
        "Shots and counts",
        "What is one shot in a Qiskit experiment?",
        [
            "One execution of the circuit followed by measurement",
            "One qubit inside the register",
            "One Python file",
            "One AI tutor response",
        ],
        0,
        "A shot is one run/sample of the circuit.",
        "Recall",
    ),
    MCQ(
        "pre_sc_2",
        "Shots and counts",
        "Why can 10 shots look less stable than 1000 shots?",
        [
            "Because small samples fluctuate more",
            "Because 10 shots use different quantum gates",
            "Because counts are not allowed for 10 shots",
            "Because measurement is disabled for small samples",
        ],
        0,
        "Small samples can deviate noticeably from the underlying probability distribution.",
        "Understanding",
    ),
    MCQ(
        "pre_sc_3",
        "Shots and counts",
        "For counts {'0': 18, '1': 2} with 20 shots, what is the percentage of outcome 0?",
        ["10%", "20%", "50%", "90%"],
        3,
        "18 out of 20 shots is 90%.",
        "Application",
    ),

    # CNOT — recall, understanding, application
    MCQ(
        "pre_cnot_1",
        "CNOT and correlation",
        "In qc.cx(0, 1), which qubit is the control?",
        ["qubit 0", "qubit 1", "classical bit 0", "classical bit 1"],
        0,
        "The first argument is the control and the second is the target.",
        "Recall",
    ),
    MCQ(
        "pre_cnot_2",
        "CNOT and correlation",
        "What is the CNOT rule in the computational basis?",
        [
            "The target flips when the control is 1",
            "The control always flips when the target is 1",
            "Both qubits are measured immediately",
            "The target is deleted",
        ],
        0,
        "CNOT flips the target conditional on the control being 1.",
        "Understanding",
    ),
    MCQ(
        "pre_cnot_3",
        "CNOT and correlation",
        "After H on q0 followed by cx(0, 1), which two outcomes are expected to dominate ideally?",
        ["00 and 11", "01 and 10", "00 and 01", "10 and 11"],
        0,
        "The Bell-style pattern creates correlated outcomes, typically 00 and 11.",
        "Application",
    ),

    # Debugging — recall, understanding, application
    MCQ(
        "pre_dbg_1",
        "Qiskit debugging",
        "What does the second number in QuantumCircuit(1, 1) specify?",
        ["Number of classical bits", "Number of Hadamard gates", "Number of shots", "Number of simulators"],
        0,
        "The second argument specifies how many classical bits are allocated.",
        "Recall",
    ),
    MCQ(
        "pre_dbg_2",
        "Qiskit debugging",
        "Why does QuantumCircuit(1, 0) followed by qc.measure(0, 0) fail?",
        [
            "No classical bit was allocated for the measurement result",
            "The qubit starts in |1>",
            "The H gate is missing",
            "The simulator cannot run one-qubit circuits",
        ],
        0,
        "The measurement tries to write into classical bit 0, but no classical bits exist.",
        "Understanding",
    ),
    MCQ(
        "pre_dbg_3",
        "Qiskit debugging",
        "Which corrected line allocates one qubit and one classical bit?",
        ["QuantumCircuit(1, 1)", "QuantumCircuit(1, 0)", "QuantumCircuit(0, 1)", "QuantumCircuit('one')"],
        0,
        "QuantumCircuit(1, 1) provides both q0 and c0.",
        "Application",
    ),
]

POST_TEST: List[MCQ] = [
    # Circuit basics — parallel but not identical to pre-test
    MCQ(
        "post_cb_1",
        "Circuit basics",
        "In QuantumCircuit(2, 2), what do the two numbers represent?",
        ["Two qubits and two classical bits", "Two gates and two shots", "Two files and two functions", "Two AI prompts"],
        0,
        "QuantumCircuit(2, 2) allocates two qubits and two classical bits.",
        "Recall",
    ),
    MCQ(
        "post_cb_2",
        "Circuit basics",
        "Why is a circuit diagram useful for beginners?",
        [
            "It shows the flow of qubits, gates, and measurement visually",
            "It guarantees a real quantum computer will be used",
            "It removes all probability from the result",
            "It replaces the need to understand measurement",
        ],
        0,
        "The diagram helps connect code to operations on qubits and classical outputs.",
        "Understanding",
    ),
    MCQ(
        "post_cb_3",
        "Circuit basics",
        "A circuit shows q0 measured into c0. What is the best interpretation?",
        [
            "The result of measuring q0 is stored in classical bit c0",
            "c0 becomes a quantum state",
            "q0 is copied into another qubit",
            "The circuit has no classical output",
        ],
        0,
        "Measurement maps the qubit result into a classical bit.",
        "Application",
    ),

    # Qubit measurement
    MCQ(
        "post_qm_1",
        "Qubit measurement",
        "What is produced by a single measurement shot?",
        ["One classical outcome", "The full wavefunction", "A new quantum gate", "A complete proof of superposition"],
        0,
        "One shot gives one classical measurement result.",
        "Recall",
    ),
    MCQ(
        "post_qm_2",
        "Qubit measurement",
        "Which statement is most accurate?",
        [
            "Measurement is where a quantum state is sampled into classical data",
            "Measurement always creates a 50/50 distribution",
            "Measurement removes the need for a classical register",
            "Measurement is the same as applying H",
        ],
        0,
        "Measurement returns classical data from the quantum state according to the measurement basis and probabilities.",
        "Understanding",
    ),
    MCQ(
        "post_qm_3",
        "Qubit measurement",
        "If no gate changes q0 from |0>, what should repeated ideal measurements show?",
        ["Mostly 0", "Mostly 1", "Randomly 50/50", "Only syntax errors"],
        0,
        "Without a state-changing gate, |0> measured in the computational basis gives 0.",
        "Application",
    ),

    # Hadamard
    MCQ(
        "post_h_1",
        "Hadamard and superposition",
        "Which line creates the Hadamard transformation on q0?",
        ["qc.h(0)", "qc.measure(0, 0)", "QuantumCircuit(1, 1)", "print(counts)"],
        0,
        "The H gate is applied by qc.h(0).",
        "Recall",
    ),
    MCQ(
        "post_h_2",
        "Hadamard and superposition",
        "Why is it misleading to say that H directly outputs both 0 and 1?",
        [
            "H changes the quantum state; measurement later samples one classical outcome",
            "H only creates classical bits",
            "H prevents measurement",
            "H is a debugging command",
        ],
        0,
        "H affects the pre-measurement state; each measurement still returns one classical bit.",
        "Understanding",
    ),
    MCQ(
        "post_h_3",
        "Hadamard and superposition",
        "A learner runs H on |0> for 1000 shots and obtains {'0': 487, '1': 513}. What is the best conclusion?",
        [
            "This is consistent with an approximately balanced distribution",
            "The circuit must be broken",
            "The qubit was certainly |1> before measurement",
            "Measurement did not occur",
        ],
        0,
        "Counts near 50/50 are expected for H applied to |0>.",
        "Application",
    ),

    # Shots and counts
    MCQ(
        "post_sc_1",
        "Shots and counts",
        "What does a counts dictionary summarize?",
        ["Frequencies of measured bitstrings", "Only the source code", "The number of qubits allocated", "The AI tutor rating"],
        0,
        "Counts summarize how often each measured bitstring occurred.",
        "Recall",
    ),
    MCQ(
        "post_sc_2",
        "Shots and counts",
        "Why should learners compare proportions when shot counts differ?",
        [
            "Raw counts depend on the number of shots, so proportions are more comparable",
            "Proportions remove all quantum effects",
            "Raw counts are always wrong",
            "Shot counts do not affect any output",
        ],
        0,
        "Proportions normalize counts when total shots differ.",
        "Understanding",
    ),
    MCQ(
        "post_sc_3",
        "Shots and counts",
        "A run gives {'0': 250, '1': 750}. What proportion of the samples are outcome 1?",
        ["25%", "50%", "75%", "100%"],
        2,
        "750 of 1000 total samples is 75%.",
        "Application",
    ),

    # CNOT
    MCQ(
        "post_cnot_1",
        "CNOT and correlation",
        "In qc.cx(0, 1), which qubit is the target?",
        ["qubit 0", "qubit 1", "classical bit 0", "classical bit 1"],
        1,
        "The second argument is the target.",
        "Recall",
    ),
    MCQ(
        "post_cnot_2",
        "CNOT and correlation",
        "What does it mean that outcomes 00 and 11 dominate after H followed by CNOT?",
        [
            "The two measured qubits are correlated",
            "The simulator skipped measurement",
            "The target was deleted",
            "The circuit used no qubits",
        ],
        0,
        "Dominant 00 and 11 outcomes indicate correlated measurement results.",
        "Understanding",
    ),
    MCQ(
        "post_cnot_3",
        "CNOT and correlation",
        "If the control value is 1 and the target starts as 0, what does CNOT do to the target?",
        ["Leaves it 0", "Flips it to 1", "Deletes it", "Measures it into c0 automatically"],
        1,
        "When control is 1, CNOT flips the target.",
        "Application",
    ),

    # Debugging
    MCQ(
        "post_dbg_1",
        "Qiskit debugging",
        "In qc.measure(0, 0), what does the second 0 refer to?",
        ["classical bit 0", "a second qubit", "the number of shots", "the simulator index"],
        0,
        "The second argument is the classical bit index where the result is stored.",
        "Recall",
    ),
    MCQ(
        "post_dbg_2",
        "Qiskit debugging",
        "What should you check first if measurement raises a classical-bit index error?",
        [
            "Whether enough classical bits were allocated",
            "Whether the AI tutor is enabled",
            "Whether the circuit title is short enough",
            "Whether H was applied exactly twice",
        ],
        0,
        "Measurement needs a valid classical-bit destination.",
        "Understanding",
    ),
    MCQ(
        "post_dbg_3",
        "Qiskit debugging",
        "A student wants to measure q0 into c0. Which minimal circuit header is appropriate?",
        ["QuantumCircuit(1, 1)", "QuantumCircuit(1, 0)", "QuantumCircuit(0, 0)", "QuantumCircuit('q0','c0')"],
        0,
        "The circuit needs one qubit and one classical bit.",
        "Application",
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
