# CourseConnect

CourseConnect is an **AI-powered academic advising platform** that unifies the entire course planning experience into a single natural language interface. Instead of navigating multiple portals, static degree checkers, and scattered departmental websites, students can simply ask questions like:

* *“What courses fulfill my core requirements next semester without time conflicts?”*
* *“What electives match my interest in global politics and machine learning?”*

CourseConnect translates these questions into structured queries over knowledge graphs to generate **validated, personalized, and explainable academic recommendations**—all within one conversation.

---

## 🧠 System Architecture

* **Natural Language Academic Advising**
  Ask complex academic planning questions in plain English and receive structured, validated answers.

* **Dual Knowledge Graph Architecture**

  * **School Knowledge Graph (S-KG):** Encodes courses, prerequisites, schedules, instructors, and degree requirements.
  * **Personal Knowledge Graph (P-KG):** Models a student’s academic history, interests, completed coursework, and preferences.

* **SPARQL-Driven Reasoning**
  User queries are translated into formal SPARQL queries to ensure correctness, traceability, and constraint validation (e.g., prerequisites, time conflicts).

---

## 🔍 Example Queries

* "What courses fulfill my core requirements next semester without time conflicts?"
* "Which electives combine data science and public policy?"
* "Can I take INFO 206A if I haven’t completed INFO 206?"
* "Build me a conflict-free schedule with two electives and one core class."

---

## 🛠️ Tech Stack

* **Knowledge Graphs:** RDF / OWL
* **Query Language:** SPARQL
* **Backend:** Python
* **AI Orchestration:** CrewAI
* **Frontend:** HTML / CSS

---

## 🎓 Target Audience

CourseConnect is initially designed for the **UC Berkeley I-School community**, but the architecture is intentionally generalizable to other universities with structured course and degree data.

---

## 🚀 Goals & Vision

* Reduce cognitive overload in academic planning
* Replace static degree checkers with conversational, explainable systems
* Encourage cross-disciplinary exploration
* Demonstrate how **knowledge graphs + LLMs** can support high-stakes decision-making

---

## 📌 Project Status

This project is under active development as an **implementation-focused academic project**, created to fulfill the requirements of **INFO 290: Knowledge Representation for Intelligent Applications**. Current work includes expanding validation cases, improving SPARQL query generation, and refining personalization logic.

Team Members:
Kurumi Kaneko
Raras Pramudita
Tyler Twohig