#!/usr/bin/env python3
import os
import re
import pickle
import fitz
import docx
import rdflib
from rdflib.namespace import RDF, Namespace
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from crewai import Agent, Task, Crew, LLM


# ============================================================
#                     NAMESPACES
# ============================================================

EX = Namespace("http://example.org/schema#")
SCHEMA = Namespace("http://schema.org/")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")


# ============================================================
#                LOAD THE ONTOLOGY MODEL
# ============================================================

def load_ontology(path="model.ttl"):
    with open(path, "r") as f:
        return f.read()

ONTOLOGY_TEXT = load_ontology()


# ============================================================
#              SANITIZE LLM-GENERATED TURTLE
# ============================================================

def sanitize_ttl(ttl: str) -> str:
    cleaned = []
    for line in ttl.splitlines():
        line = line.strip()

        # Strip obvious non-Turtle noise
        if line.startswith("(") or line.endswith(")"):
            continue

        banned = [
            "the above", "this turtle", "cleaned version",
            "note:", "explanation:", "summary:"
        ]
        if any(b in line.lower() for b in banned):
            continue

        if line == "":
            continue

        cleaned.append(line)

    result = "\n".join(cleaned).strip()

    if not result:
        return result

    # Ensure rdf: prefix is declared if rdf: is used
    if "rdf:" in result and "@prefix rdf:" not in result:
        rdf_prefix = "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> ."
        # If there are existing prefix lines, insert after them; otherwise just prepend
        lines = result.splitlines()
        insert_idx = 0
        while insert_idx < len(lines) and lines[insert_idx].startswith("@prefix "):
            insert_idx += 1
        lines.insert(insert_idx, rdf_prefix)
        result = "\n".join(lines)

    return result



# ============================================================
#            TRIPLE EXTRACTION AGENT (OPENAI)
# ============================================================

triple_extractor = Agent(
    role="Triple Extractor",
    goal="Extract valid RDF triples from text about ONE student only.",
    backstory="You output only Turtle triples from text, following a strict ontology.",
    llm=LLM(model="gpt-4.1-mini", provider="openai"),
    verbose=False,
    allow_delegation=False
)


# ============================================================
#                     CLEANER AGENT
# ============================================================

cleaner_agent = Agent(
    role="KG Cleaner",
    goal="Clean triples so they describe exactly ONE student.",
    backstory="You remove irrelevant triples and enforce a canonical student identity.",
    llm=LLM(model="gpt-4.1-mini", provider="openai"),
    verbose=False,
    allow_delegation=False
)


# ============================================================
#               DOCUMENT TEXT EXTRACTION
# ============================================================

def extract_text(file_path):
    print(f"[INFO] Extracting text from: {file_path}")

    ext = file_path.lower().split(".")[-1]

    def clean(t):
        return re.sub(r"\s+", " ", t.replace("\n", " ")).strip()

    if ext == "pdf":
        print("[INFO] PDF detected.")
        doc = fitz.open(file_path)
        text = " ".join(page.get_text() for page in doc)
        print("[INFO] PDF extraction complete.")
        return clean(text)

    if ext == "docx":
        print("[INFO] DOCX detected.")
        d = docx.Document(file_path)
        print("[INFO] DOCX extraction complete.")
        return clean(" ".join(p.text for p in d.paragraphs))

    raise ValueError("Unsupported file type. Use PDF or DOCX.")


# ============================================================
#                        CHUNKING
# ============================================================

def chunk_document(text, chunk_size=900, overlap=150):
    print("[INFO] Chunking document...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap
    )
    chunks = splitter.split_text(text)
    print(f"[INFO] Created {len(chunks)} chunks.")
    return chunks


# ============================================================
#                EMBEDDING STORAGE (INCREMENTAL)
# ============================================================

EMB_PATH = "p-kg-embeddings.pkl"
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


def save_embeddings_incremental(chunks):
    print("[INFO] Generating embeddings...")

    if os.path.exists(EMB_PATH):
        with open(EMB_PATH, "rb") as f:
            store = pickle.load(f)
    else:
        store = []

    for i, chunk in enumerate(chunks):
        emb = embedding_model.encode(chunk).tolist()
        store.append({"chunk_id": len(store), "embedding": emb, "text": chunk})

    with open(EMB_PATH, "wb") as f:
        pickle.dump(store, f)

    print(f"[INFO] Saved {len(chunks)} new embeddings → {EMB_PATH}")


# ============================================================
#              BUILD TRIPLE EXTRACTION TASK
# ============================================================

def make_task(chunk, chunk_id, filename):
    return Task(
        description=f"""
Extract RDF triples describing a single student.

Rules:
- Use ONLY classes & properties in the ontology.
- Include provenance triple: ex:foundInDocument "<{filename}>" .
- No inventing new properties.
- No commentary.

Ontology:
{ONTOLOGY_TEXT}

Chunk #{chunk_id}:
{chunk}
""",
        expected_output="Only valid Turtle triples.",
        agent=triple_extractor
    )


# ============================================================
#              APPEND RAW TRIPLES (APPEND-ONLY)
# ============================================================

def append_raw_triples(triples_list, output="p-kg-raw.ttl"):
    with open(output, "a") as f:
        for entry in triples_list:
            f.write(f"\n# --- Chunk {entry['chunk_id']} ---\n")
            f.write(entry["triples"])
            f.write("\n")

    print(f"[INFO] Appended {len(triples_list)} chunks → {output}")


# ============================================================
#              CLEAN ONLY *NEW* RAW TRIPLES
# ============================================================

def clean_new_ttl(ttl_text):
    task = Task(
        description=f"""
Clean these Turtle triples so that:

- They refer to EXACTLY ONE student.
- Remove irrelevant or contradictory triples.
- DO NOT invent new triples.
- DO NOT wrap the output in parentheses.
- DO NOT include comments, explanations, or prose.
- Output MUST be pure valid Turtle triples.

Input:
{ttl_text}
""",
        expected_output="Clean Turtle RDF describing only one student. No comments. No parentheses.",
        agent=cleaner_agent
    )

    crew = Crew(agents=[cleaner_agent], tasks=[task], verbose=False)
    cleaned = crew.kickoff()
    return str(cleaned).strip()


# ============================================================
#      MERGE NEW CLEAN TRIPLES INTO FINAL KG INCREMENTALLY
# ============================================================

def merge_students_incremental(new_clean_ttl, final_file="p-kg-final.ttl"):
    print("[INFO] Incremental KG merge starting...")

    final_g = rdflib.Graph()
    if os.path.exists(final_file):
        final_g.parse(final_file, format="turtle")
        print(f"[INFO] Loaded existing KG: {len(final_g)} triples.")
    else:
        print("[INFO] No final KG found; creating new KG.")

    safe_ttl = sanitize_ttl(new_clean_ttl)

    if not safe_ttl:
        print("❌ ERROR: Sanitized TTL is empty.")
        print("RAW TTL:\n", new_clean_ttl)
        raise ValueError("Sanitized TTL was empty.")

    new_g = rdflib.Graph()
    try:
        new_g.parse(data=safe_ttl, format="turtle")
    except Exception as e:
        print("\n❌ RDFLib FAILED TO PARSE CLEANED TTL")
        print("---- RAW CLEANED TTL ----")
        print(new_clean_ttl)
        print("\n---- SANITIZED TTL ----")
        print(safe_ttl)
        print("──────────────────────────────────────")
        raise e

    print(f"[INFO] Loaded new cleaned triples: {len(new_g)} triples.")

    existing_students = list(final_g.subjects(RDF.type, EX.Student))
    if existing_students:
        canonical = existing_students[0]
        print(f"[INFO] Canonical student = {canonical}")
    else:
        new_students = list(new_g.subjects(RDF.type, EX.Student))
        canonical = new_students[0]
        print(f"[INFO] Canonical student initialized = {canonical}")

    merged_new_g = rdflib.Graph()
    for (s, p, o) in new_g:
        if (s, RDF.type, EX.Student) in new_g and s != canonical:
            s = canonical
        if (o, RDF.type, EX.Student) in new_g and o != canonical:
            o = canonical
        merged_new_g.add((s, p, o))

    print(f"[INFO] New triples after canonical merge: {len(merged_new_g)}")

    for triple in merged_new_g:
        final_g.add(triple)

    print(f"[INFO] Final KG updated: {len(final_g)} total triples.")
    final_g.serialize(final_file, format="turtle")
    print(f"✔ Final KG saved → {final_file}")


# ============================================================
#                  FULL DOCUMENT PIPELINE
# ============================================================

def process_document(file_path):

    print("\n======================================================")
    print(f"[PIPELINE] Processing document: {file_path}")
    print("======================================================\n")

    text = extract_text(file_path)
    chunks = chunk_document(text)
    save_embeddings_incremental(chunks)

    filename = os.path.basename(file_path)

    extracted = []
    for i, chunk in enumerate(chunks):
        print(f"[INFO] Extracting triples from chunk {i}")
        task = make_task(chunk, i, filename)
        crew = Crew(agents=[triple_extractor], tasks=[task], verbose=False)

        try:
            result = crew.kickoff()
            triples = str(result).strip()
            if not triples:
                raise ValueError("Empty LLM output")
        except Exception as e:
            print(f"[WARN] Chunk {i} failed: {e}")
            triples = "# No triples extracted.\n"

        extracted.append({"chunk_id": i, "triples": triples})

    append_raw_triples(extracted, "p-kg-raw.ttl")

    new_raw = "\n".join(
        f"# --- Chunk {e['chunk_id']} ---\n{e['triples']}"
        for e in extracted
    )

    print("[INFO] Cleaning new triples...")
    cleaned_new = clean_new_ttl(new_raw)

    with open("p-kg-clean-latest.ttl", "w") as f:
        f.write(cleaned_new)

    print("[INFO] Saved cleaned triples → p-kg-clean-latest.ttl")

    merge_students_incremental(cleaned_new, "p-kg-final.ttl")

    print("\n======================================================")
    print("[PIPELINE] Processing complete.")
    print("→ Raw triples: p-kg-raw.ttl")
    print("→ New cleaned triples: p-kg-clean-latest.ttl")
    print("→ Final KG: p-kg-final.ttl")
    print("======================================================\n")


# ============================================================
#                          CLI ENTRY
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Process a document into incremental PKG.")
    parser.add_argument("file", help="PDF or DOCX")
    args = parser.parse_args()

    process_document(args.file)
