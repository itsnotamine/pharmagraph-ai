# PharmaGraph AI
### Evidence-Grounded Pharmaceutical Research Assistant

PharmaGraph AI is an agentic AI application designed to assist pharmaceutical research through structured reasoning, hybrid document retrieval, specialized tools, and evidence-based answer validation.

Unlike a traditional chatbot, PharmaGraph AI orchestrates a multi-stage workflow that plans research tasks, retrieves relevant pharmaceutical evidence, invokes domain-specific tools, reviews generated answers, and provides traceable source citations.

> **Disclaimer:** This application is intended for research and educational purposes only. It is not a clinical decision-support system and must not replace professional medical advice.

---

## 1. Key Features

- **LangGraph orchestration:** Structured multi-stage agent workflow.
- **Hybrid RAG:** Combines semantic embeddings with lexical retrieval.
- **Adaptive Critic:** Reviews generated responses and can trigger additional attempts.
- **Dynamic tool selection:** Invokes specialized pharmaceutical tools according to the question.
- **Evidence-grounded answers:** Includes references to retrieved pharmaceutical documents.
- **Agent traceability:** Exposes planning, retrieval, tool execution, critic feedback, and retry information.
- **Interactive web interface:** Provides a conversational research experience with supporting evidence.
- **Docker deployment:** Containerized FastAPI application.

---

## 2. Agent Architecture

```mermaid
flowchart TD
    A[User Question] --> B[PLAN]
    B --> C[RETRIEVE]
    C --> D[Hybrid RAG]
    D --> E[USE TOOLS]
    E --> F[ANSWER GENERATION]
    F --> G[REVIEW - Adaptive Critic]
    G -->|Approved| H[Final Answer + Citations]
    G -->|Revision Required| I[Retry / Refinement]
    I --> F
    H --> J[Web Interface + Evidence Center]
```

### Workflow

**PLAN → RETRIEVE → USE TOOLS → REVIEW → ANSWER**

1. **Plan:** Analyze the question and identify research steps.
2. **Retrieve:** Search the local pharmaceutical corpus using hybrid retrieval.
3. **Use Tools:** Execute specialized tools based on the research requirements.
4. **Review:** Evaluate the generated response using an adaptive critic.
5. **Answer:** Return an evidence-grounded response with citations and execution trace.

The system supports iterative refinement when the critic identifies issues requiring revision.

---

## 3. Hybrid Retrieval-Augmented Generation

The retrieval component combines:

- **Semantic retrieval:** Embedding-based similarity for contextual relevance.
- **Lexical retrieval:** Keyword-based matching for precise pharmaceutical terminology.
- **Retrieval fusion:** Combines complementary search signals to select supporting evidence.

This approach helps retrieve both conceptually relevant passages and exact medical terminology.

---

## 4. Pharmaceutical Research Tools

PharmaGraph AI provides specialized tools for:

| Tool | Purpose |
|------|---------|
| `contraindication_lookup` | Identify documented drug contraindications |
| `renal_safety_check` | Investigate renal-function-related medication restrictions |
| `interaction_analysis` | Analyze documented drug interaction warnings |
| `evidence_comparison` | Compare evidence across medications or sources |

Tool execution is selected according to the question rather than following a fixed tool sequence.

---

## 5. Evidence Sources

The application uses a local pharmaceutical research corpus containing **21 Markdown documents**:

- 10 DailyMed drug-label documents
- 10 MedlinePlus medication-information documents
- 1 pharmaceutical glossary

The corpus covers medications including:

- Warfarin
- Apixaban
- Metformin
- Sertraline
- Aspirin
- Ibuprofen
- Acetaminophen
- Amoxicillin
- Atorvastatin
- Albuterol

Generated responses reference retrieved evidence passages to support factual claims.

---

## 6. Technology Stack

| Layer | Technology |
|-------|------------|
| Backend | Python, FastAPI |
| Agent orchestration | LangGraph |
| LLM integration | OpenAI-compatible API |
| Retrieval | Semantic embeddings + lexical search |
| Answer validation | LLM-based adaptive critic |
| Frontend | HTML, CSS, JavaScript |
| Deployment | Docker |
| Evaluation | Python benchmark script |

---

## 7. Installation

### Requirements

- Python 3.11 or compatible environment
- Docker (optional)
- Access to a compatible LLM and embedding API

### Local Setup

Clone the repository and navigate to the project directory.

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create the environment configuration:

```bash
cp .env.example .env
```

Configure the following variables in `.env`:

```env
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=your_api_base_url
OPENAI_MODEL=your_chat_model
OPENAI_EMBEDDING_MODEL=your_embedding_model
```

Never commit your actual `.env` file.

Start the application:

```bash
python -m uvicorn app.main:app --reload
```

Open the application at:

- Web interface: `http://localhost:8000`
- API documentation: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

---

## 8. Docker Deployment

Build the Docker image:

```bash
docker build -t pharmagraph-ai .
```

Start the container:

```bash
docker run --rm \
  --name pharmagraph-ai \
  -p 8000:8000 \
  --env-file .env \
  pharmagraph-ai
```

Open:

`http://localhost:8000`

---

## 9. API Usage

### POST /ask

Example request:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Is metformin contraindicated at an eGFR of 25?"}'
```

The API returns:

- `question`: Original research question
- `answer`: Generated evidence-grounded response
- `sources`: Supporting pharmaceutical evidence
- `agent_trace`: Agent execution information
- `disclaimer`: Medical safety disclaimer

The agent trace includes:

- Research plan
- Search queries
- Executed tools
- Critic approval status
- Critic feedback
- Retry count

---

## 10. Evaluation

The application was evaluated using four pharmaceutical research scenarios.

| Test Scenario | Duration | Evidence Sources | Critic Approved | Retries |
|---------------|----------|------------------|-----------------|---------|
| Warfarin contraindications | 51.79 s | 4 | Yes | 0 |
| Warfarin vs. Apixaban | 33.53 s | 5 | Yes | 1 |
| Warfarin + Sertraline interaction | 15.32 s | 11 | Yes | 0 |
| Metformin with eGFR 25 | 9.18 s | 3 | Yes | 0 |

**Observed technical success rate: 4/4 requests (100%) in this limited benchmark.**

All four requests returned answers with supporting evidence, and the critic approved the final responses.

The comparative contraindication scenario required one retry, illustrating the review-and-refinement capability.

These results are specific to the tested environment and do not constitute clinical validation or a guarantee of medical accuracy.

### Run the Benchmark

Start the application, then execute:

```bash
python tests/benchmark.py
```

Results are saved locally to:

`tests/benchmark_results.json`

---

## 11. Project Structure

```text
pharma-agent-starter/
├── app/
│   ├── agent/
│   ├── rag/
│   ├── static/
│   └── main.py
├── corpus/
├── tests/
│   └── benchmark.py
├── .env.example
├── .gitignore
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 12. Limitations

- The pharmaceutical corpus is limited to the supplied documents.
- Retrieval quality depends on document coverage and relevance.
- Generated answers may contain inaccuracies despite critic validation.
- The critic is an automated quality-control mechanism, not a clinical expert.
- The system does not provide personalized treatment recommendations.
- Medical decisions must be reviewed by qualified healthcare professionals.

---

## 13. Future Improvements

Potential extensions include:

- Larger and regularly updated pharmaceutical knowledge bases
- More extensive evaluation datasets
- Automated citation verification
- Retrieval quality metrics
- Latency and cost optimization
- Additional pharmaceutical research tools

---

## 14. Project Context

Developed as part of the **Syntax GenAI pharmaceutical research assistant assignment**.

The project demonstrates the integration of agentic AI orchestration, retrieval-augmented generation, specialized tool execution, evidence traceability, and automated answer review.

---

## Medical Disclaimer

PharmaGraph AI is intended exclusively for research and educational purposes.

It is not medical advice, is not clinically validated, and must not be used as a substitute for consultation with a qualified healthcare professional.
EOFcat > README.md <<'EOF'
# PharmaGraph AI
### Evidence-Grounded Pharmaceutical Research Assistant

PharmaGraph AI is an agentic AI application designed to assist pharmaceutical research through structured reasoning, hybrid document retrieval, specialized tools, and evidence-based answer validation.

Unlike a traditional chatbot, PharmaGraph AI orchestrates a multi-stage workflow that plans research tasks, retrieves relevant pharmaceutical evidence, invokes domain-specific tools, reviews generated answers, and provides traceable source citations.

> **Disclaimer:** This application is intended for research and educational purposes only. It is not a clinical decision-support system and must not replace professional medical advice.

---

## 1. Key Features

- **LangGraph orchestration:** Structured multi-stage agent workflow.
- **Hybrid RAG:** Combines semantic embeddings with lexical retrieval.
- **Adaptive Critic:** Reviews generated responses and can trigger additional attempts.
- **Dynamic tool selection:** Invokes specialized pharmaceutical tools according to the question.
- **Evidence-grounded answers:** Includes references to retrieved pharmaceutical documents.
- **Agent traceability:** Exposes planning, retrieval, tool execution, critic feedback, and retry information.
- **Interactive web interface:** Provides a conversational research experience with supporting evidence.
- **Docker deployment:** Containerized FastAPI application.

---

## 2. Agent Architecture

```mermaid
flowchart TD
    A[User Question] --> B[PLAN]
    B --> C[RETRIEVE]
    C --> D[Hybrid RAG]
    D --> E[USE TOOLS]
    E --> F[ANSWER GENERATION]
    F --> G[REVIEW - Adaptive Critic]
    G -->|Approved| H[Final Answer + Citations]
    G -->|Revision Required| I[Retry / Refinement]
    I --> F
    H --> J[Web Interface + Evidence Center]
```

### Workflow

**PLAN → RETRIEVE → USE TOOLS → REVIEW → ANSWER**

1. **Plan:** Analyze the question and identify research steps.
2. **Retrieve:** Search the local pharmaceutical corpus using hybrid retrieval.
3. **Use Tools:** Execute specialized tools based on the research requirements.
4. **Review:** Evaluate the generated response using an adaptive critic.
5. **Answer:** Return an evidence-grounded response with citations and execution trace.

The system supports iterative refinement when the critic identifies issues requiring revision.

---

## 3. Hybrid Retrieval-Augmented Generation

The retrieval component combines:

- **Semantic retrieval:** Embedding-based similarity for contextual relevance.
- **Lexical retrieval:** Keyword-based matching for precise pharmaceutical terminology.
- **Retrieval fusion:** Combines complementary search signals to select supporting evidence.

This approach helps retrieve both conceptually relevant passages and exact medical terminology.

---

## 4. Pharmaceutical Research Tools

PharmaGraph AI provides specialized tools for:

| Tool | Purpose |
|------|---------|
| `contraindication_lookup` | Identify documented drug contraindications |
| `renal_safety_check` | Investigate renal-function-related medication restrictions |
| `interaction_analysis` | Analyze documented drug interaction warnings |
| `evidence_comparison` | Compare evidence across medications or sources |

Tool execution is selected according to the question rather than following a fixed tool sequence.

---

## 5. Evidence Sources

The application uses a local pharmaceutical research corpus containing **21 Markdown documents**:

- 10 DailyMed drug-label documents
- 10 MedlinePlus medication-information documents
- 1 pharmaceutical glossary

The corpus covers medications including:

- Warfarin
- Apixaban
- Metformin
- Sertraline
- Aspirin
- Ibuprofen
- Acetaminophen
- Amoxicillin
- Atorvastatin
- Albuterol

Generated responses reference retrieved evidence passages to support factual claims.

---

## 6. Technology Stack

| Layer | Technology |
|-------|------------|
| Backend | Python, FastAPI |
| Agent orchestration | LangGraph |
| LLM integration | OpenAI-compatible API |
| Retrieval | Semantic embeddings + lexical search |
| Answer validation | LLM-based adaptive critic |
| Frontend | HTML, CSS, JavaScript |
| Deployment | Docker |
| Evaluation | Python benchmark script |

---

## 7. Installation

### Requirements

- Python 3.11 or compatible environment
- Docker (optional)
- Access to a compatible LLM and embedding API

### Local Setup

Clone the repository and navigate to the project directory.

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create the environment configuration:

```bash
cp .env.example .env
```

Configure the following variables in `.env`:

```env
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=your_api_base_url
OPENAI_MODEL=your_chat_model
OPENAI_EMBEDDING_MODEL=your_embedding_model
```

Never commit your actual `.env` file.

Start the application:

```bash
python -m uvicorn app.main:app --reload
```

Open the application at:

- Web interface: `http://localhost:8000`
- API documentation: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

---

## 8. Docker Deployment

Build the Docker image:

```bash
docker build -t pharmagraph-ai .
```

Start the container:

```bash
docker run --rm \
  --name pharmagraph-ai \
  -p 8000:8000 \
  --env-file .env \
  pharmagraph-ai
```

Open:

`http://localhost:8000`

---

## 9. API Usage

### POST /ask

Example request:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Is metformin contraindicated at an eGFR of 25?"}'
```

The API returns:

- `question`: Original research question
- `answer`: Generated evidence-grounded response
- `sources`: Supporting pharmaceutical evidence
- `agent_trace`: Agent execution information
- `disclaimer`: Medical safety disclaimer

The agent trace includes:

- Research plan
- Search queries
- Executed tools
- Critic approval status
- Critic feedback
- Retry count

---

## 10. Evaluation

The application was evaluated using four pharmaceutical research scenarios.

| Test Scenario | Duration | Evidence Sources | Critic Approved | Retries |
|---------------|----------|------------------|-----------------|---------|
| Warfarin contraindications | 51.79 s | 4 | Yes | 0 |
| Warfarin vs. Apixaban | 33.53 s | 5 | Yes | 1 |
| Warfarin + Sertraline interaction | 15.32 s | 11 | Yes | 0 |
| Metformin with eGFR 25 | 9.18 s | 3 | Yes | 0 |

**Observed technical success rate: 4/4 requests (100%) in this limited benchmark.**

All four requests returned answers with supporting evidence, and the critic approved the final responses.

The comparative contraindication scenario required one retry, illustrating the review-and-refinement capability.

These results are specific to the tested environment and do not constitute clinical validation or a guarantee of medical accuracy.

### Run the Benchmark

Start the application, then execute:

```bash
python tests/benchmark.py
```

Results are saved locally to:

`tests/benchmark_results.json`

---

## 11. Project Structure

```text
pharma-agent-starter/
├── app/
│   ├── agent/
│   ├── rag/
│   ├── static/
│   └── main.py
├── corpus/
├── tests/
│   └── benchmark.py
├── .env.example
├── .gitignore
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 12. Limitations

- The pharmaceutical corpus is limited to the supplied documents.
- Retrieval quality depends on document coverage and relevance.
- Generated answers may contain inaccuracies despite critic validation.
- The critic is an automated quality-control mechanism, not a clinical expert.
- The system does not provide personalized treatment recommendations.
- Medical decisions must be reviewed by qualified healthcare professionals.

---

## 13. Future Improvements

Potential extensions include:

- Larger and regularly updated pharmaceutical knowledge bases
- More extensive evaluation datasets
- Automated citation verification
- Retrieval quality metrics
- Latency and cost optimization
- Additional pharmaceutical research tools

---

## 14. Project Context

Developed as part of the **Syntax GenAI pharmaceutical research assistant assignment**.

The project demonstrates the integration of agentic AI orchestration, retrieval-augmented generation, specialized tool execution, evidence traceability, and automated answer review.

---

## Medical Disclaimer

PharmaGraph AI is intended exclusively for research and educational purposes.

It is not medical advice, is not clinically validated, and must not be used as a substitute for consultation with a qualified healthcare professional.
