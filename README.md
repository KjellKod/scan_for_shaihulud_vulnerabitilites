```
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 1: Text Extraction (file_processor.py)                      │
│  ─────────────────────────────────────────────────────────────────  │
│  PDF file → extract_text_from_pdf() → RAW TEXT string              │
│                                                                      │
│  - pypdf (primary) → raw text                                       │
│  - OpenAI fallback → raw text                                       │
│                                                                      │
│  Output: Plain text string stored in Candidate.resume_text          │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 2: Pass 1 Parsing (parsing/pass1_parser.py via ai_client)   │
│  ─────────────────────────────────────────────────────────────────  │
│  RAW TEXT → parse_resume() → STRUCTURED JSON (ParsedResume)        │
│                                                                      │
│  - Uses LLM to extract: work_history, education, skills, metadata   │
│  - Saved to data/candidates/{job}/{name}/parsed.json                │
│                                                                      │
│  Output: Dict with schema keys (work_history, education, etc.)      │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 3: Pass 2 Evaluation (ai_client.py)                         │
│  ─────────────────────────────────────────────────────────────────  │
│  STRUCTURED JSON + Job Context → evaluate_candidate() → Evaluation  │
└─────────────────────────────────────────────────────────────────────┘
```
