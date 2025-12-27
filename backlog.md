# 🎯 Scout Backlog

This document tracks all planned features, improvements, and technical debt for the Scout project.

## Legend

- **Priority**: 🔴 High | 🟡 Medium | 🟢 Low
- **Status**: 📋 Backlog | 🚧 In Progress | ✅ Done | ❌ Cancelled
- **Phase**: 1-4 (as per implementation roadmap)

---

## Phase 1: Foundation

### Core Extraction Pipeline

#### ✅ EX-001: Basic Job Extraction
- **Status**: ✅ Done
- **Priority**: 🔴 High
- **Description**: Implement basic job posting extraction using LlamaIndex structured output. Extract structured data from job posting text into JobInfo model.
- **Acceptance Criteria**:
  - [x] `get_job_info_program()` creates and returns LlamaIndex structured output program
  - [x] `extract_job_info(text: str)` function implemented and calls the program
  - [x] JobInfo model with all required fields
  - [x] Enum definitions implemented: `JobLevel`, `RemoteType`, `AtsType`
  - [x] Text preprocessing integration (normalize_html_text, find_heading_positions, slice_by_positions)
  - [x] Error handling for extraction failures (invalid text, API errors, parsing errors)
  - [x] Unit tests passing (test_extractor.py updated and active)
  - [x] Integration with `run_scout_agent()` pipeline
- **Files**: `src/scout/tools/extractor.py`, `src/scout/models.py`
- **Dependencies**: 
  - LlamaIndex structured output setup
  - OpenAI API key configured
  - JobInfo model structure finalized
- **Technical Notes**:
  - Helper functions exist (`normalize_html_text`, `find_heading_positions`, `slice_by_positions`) but need integration
  - Test file shows expected behavior: program should accept text and return JobInfo
  - Consider caching program instance for performance

#### 🚧 EX-002: HTML Fetching and Cleaning
- **Status**: 🚧 In Progress
- **Priority**: 🔴 High
- **Description**: Robust HTML fetching with Playwright for JS-heavy sites and text normalization
- **Acceptance Criteria**:
  - [ ] `fetch_job_page()` handles both static and dynamic content
  - [ ] Text cleaning removes noise and normalizes formatting
  - [ ] Error handling for network failures and timeouts
  - [ ] Support for common job board formats
- **Files**: `src/scout/tools/fetcher.py`, `src/scout/utils/text_cleaning.py`
- **Dependencies**: Playwright installation

#### 📋 EX-003: Google Sheets Integration
- **Status**: 📋 Backlog
- **Priority**: 🔴 High
- **Description**: Log extracted job data to Google Sheets for tracking
- **Acceptance Criteria**:
  - [ ] `log_job_to_sheet()` appends JobInfo to spreadsheet
  - [ ] Column order matches JobInfo model exactly
  - [ ] Handles authentication and permissions
  - [ ] Error handling for API rate limits
- **Files**: `src/scout/tools/tracker.py`
- **Dependencies**: Google Sheets API credentials

### RAG Foundation

#### 📋 RAG-001: ChromaDB Setup and Initialization
- **Status**: 📋 Backlog
- **Priority**: 🔴 High
- **Description**: Set up ChromaDB vector database with proper schema and collections
- **Acceptance Criteria**:
  - [ ] `init_db` module creates ChromaDB instance
  - [ ] Three collections: `user_experiences`, `job_postings`, `application_history`
  - [ ] Proper embedding dimension (1536) and distance metric (cosine)
  - [ ] Persistent storage configuration
- **Files**: `src/scout/rag/__init__.py`, `src/scout/rag/vectorstore.py`
- **Dependencies**: ChromaDB package

#### 📋 RAG-002: Embedding Generation
- **Status**: 📋 Backlog
- **Priority**: 🔴 High
- **Description**: Implement OpenAI embedding generation for documents and job postings
- **Acceptance Criteria**:
  - [ ] `embed_job_posting()` creates embeddings for job requirements
  - [ ] Uses `text-embedding-3-small` model
  - [ ] Batch processing support
  - [ ] Caching mechanism for performance
- **Files**: `src/scout/rag/embeddings.py`
- **Dependencies**: OpenAI API key, llama-index-embeddings-openai

#### 📋 RAG-003: User Profile Ingestion
- **Status**: 📋 Backlog
- **Priority**: 🔴 High
- **Description**: Parse and embed user resume, portfolio, and application history
- **Acceptance Criteria**:
  - [ ] Resume parsing (PDF/text) into structured format
  - [ ] Document chunking with semantic boundaries
  - [ ] Embedding generation and storage in ChromaDB
  - [ ] Metadata preservation (dates, companies, roles, skills)
- **Files**: `src/scout/rag/vectorstore.py`, `src/scout/utils/chunking.py`
- **Dependencies**: RAG-001, RAG-002

#### 📋 RAG-004: Basic Semantic Search
- **Status**: 📋 Backlog
- **Priority**: 🟡 Medium
- **Description**: Implement basic vector similarity search for matching experiences
- **Acceptance Criteria**:
  - [ ] `retrieve_relevant_experience()` finds top-k similar documents
  - [ ] Returns similarity scores
  - [ ] Handles empty results gracefully
- **Files**: `src/scout/rag/retriever.py`
- **Dependencies**: RAG-001, RAG-002

---

## Phase 2: Intelligence

### Advanced Retrieval

#### 📋 INT-001: Hybrid Search Implementation
- **Status**: 📋 Backlog
- **Priority**: 🟡 Medium
- **Description**: Combine keyword (BM25) and semantic search for better retrieval
- **Acceptance Criteria**:
  - [ ] Keyword search using TF-IDF/BM25
  - [ ] Hybrid ranking algorithm
  - [ ] Configurable weights for keyword vs semantic
  - [ ] Performance benchmarks
- **Files**: `src/scout/rag/retriever.py`
- **Dependencies**: RAG-004, scikit-learn

#### 📋 INT-002: Metadata Filtering
- **Status**: 📋 Backlog
- **Priority**: 🟡 Medium
- **Description**: Pre-filter search results using metadata (date, company, role, skills)
- **Acceptance Criteria**:
  - [ ] Filter by date range
  - [ ] Filter by company/industry
  - [ ] Filter by skill tags
  - [ ] Combine filters with semantic search
- **Files**: `src/scout/rag/retriever.py`
- **Dependencies**: RAG-004

#### 📋 INT-003: Re-ranking with Cross-Encoder
- **Status**: 📋 Backlog
- **Priority**: 🟢 Low
- **Description**: Improve retrieval quality with cross-encoder re-ranking
- **Acceptance Criteria**:
  - [ ] Cross-encoder model integration
  - [ ] Re-rank top 20 candidates to top 5
  - [ ] Performance improvement metrics
- **Files**: `src/scout/rag/retriever.py`
- **Dependencies**: INT-001

### Pattern Recognition

#### 📋 INT-004: Application Success Predictor
- **Status**: 📋 Backlog
- **Priority**: 🟡 Medium
- **Description**: Analyze factors to predict application success probability
- **Acceptance Criteria**:
  - [ ] Calculate skill match percentage
  - [ ] Experience alignment scoring
  - [ ] Company culture fit analysis
  - [ ] Competition level estimation
  - [ ] Success probability output (0-1)
- **Files**: `src/scout/rag/analyzer.py`
- **Dependencies**: RAG-004

#### 📋 INT-005: Insight Generation Engine
- **Status**: 📋 Backlog
- **Priority**: 🟡 Medium
- **Description**: Generate actionable insights from application patterns
- **Acceptance Criteria**:
  - [ ] Success rate by job type/industry
  - [ ] Response time analysis
  - [ ] Optimal application timing
  - [ ] Keyword correlation with interviews
  - [ ] Geographic and industry trends
- **Files**: `src/scout/rag/analyzer.py`
- **Dependencies**: INT-004, Google Sheets data

#### 📋 INT-006: Skill Gap Analysis
- **Status**: 📋 Backlog
- **Priority**: 🟡 Medium
- **Description**: Identify missing skills and suggest improvements
- **Acceptance Criteria**:
  - [ ] Compare job requirements to user skills
  - [ ] Identify skill gaps
  - [ ] Suggest learning resources or certifications
  - [ ] Track gap frequency across applications
- **Files**: `src/scout/rag/analyzer.py`
- **Dependencies**: RAG-003, RAG-004

---

## Phase 3: Generation

### Content Generation

#### 📋 GEN-001: Context-Aware Cover Letter Generation
- **Status**: 📋 Backlog
- **Priority**: 🔴 High
- **Description**: Generate personalized cover letters using retrieved context
- **Acceptance Criteria**:
  - [ ] Uses retrieved relevant experiences
  - [ ] Maintains user's voice and style
  - [ ] Cites specific experiences used
  - [ ] Allows editing before saving
  - [ ] Saves to file (PDF/Markdown)
- **Files**: `src/scout/rag/generator.py`
- **Dependencies**: RAG-004, OpenAI API

#### 📋 GEN-002: Resume Bullet Optimization
- **Status**: 📋 Backlog
- **Priority**: 🟡 Medium
- **Description**: Generate optimized resume bullets tailored to job requirements
- **Acceptance Criteria**:
  - [ ] Rewrites existing bullets with job keywords
  - [ ] Maintains truthfulness and accuracy
  - [ ] Quantifies achievements where possible
  - [ ] ATS-friendly formatting
- **Files**: `src/scout/rag/generator.py`
- **Dependencies**: RAG-003, RAG-004

#### 📋 GEN-003: Application Answer Generation
- **Status**: 📋 Backlog
- **Priority**: 🟡 Medium
- **Description**: Generate answers to common application questions
- **Acceptance Criteria**:
  - [ ] Handles "Why this company?" questions
  - [ ] Handles "Why you?" questions
  - [ ] Uses retrieved context for personalization
  - [ ] Multiple answer variations
- **Files**: `src/scout/rag/generator.py`
- **Dependencies**: GEN-001

#### 📋 GEN-004: Multi-Format Output
- **Status**: 📋 Backlog
- **Priority**: 🟢 Low
- **Description**: Support multiple output formats (PDF, DOCX, Markdown, HTML)
- **Acceptance Criteria**:
  - [ ] PDF generation with proper formatting
  - [ ] DOCX export
  - [ ] Markdown for easy editing
  - [ ] HTML preview
- **Files**: `src/scout/rag/generator.py`
- **Dependencies**: GEN-001, GEN-002

### Learning Loop

#### 📋 GEN-005: Feedback Loop Integration
- **Status**: 📋 Backlog
- **Priority**: 🟡 Medium
- **Description**: Update embeddings and improve recommendations based on outcomes
- **Acceptance Criteria**:
  - [ ] Track application outcomes (interview, rejection, offer)
  - [ ] Update successful application patterns
  - [ ] Identify deteriorating strategies
  - [ ] Re-embed with outcome metadata
- **Files**: `src/scout/rag/vectorstore.py`, `src/scout/tools/tracker.py`
- **Dependencies**: EX-003, RAG-002

#### 📋 GEN-006: Application Strategy Agent
- **Status**: 📋 Backlog
- **Priority**: 🟢 Low
- **Description**: High-level agent that orchestrates application strategy
- **Acceptance Criteria**:
  - [ ] Analyzes job and user profile
  - [ ] Decides which materials to generate
  - [ ] Suggests application timing
  - [ ] Provides strategic recommendations
- **Files**: `src/scout/agent/application_agent.py`
- **Dependencies**: INT-004, GEN-001

---

## Phase 4: Optimization

### Performance

#### 📋 OPT-001: Embedding Caching Layer
- **Status**: 📋 Backlog
- **Priority**: 🟡 Medium
- **Description**: Cache embeddings to avoid redundant API calls
- **Acceptance Criteria**:
  - [ ] Cache embeddings by content hash
  - [ ] Configurable cache size and TTL
  - [ ] Cache invalidation strategy
  - [ ] Performance improvement metrics
- **Files**: `src/scout/rag/embeddings.py`
- **Dependencies**: RAG-002

#### 📋 OPT-002: Batch Processing
- **Status**: 📋 Backlog
- **Priority**: 🟡 Medium
- **Description**: Process multiple jobs efficiently
- **Acceptance Criteria**:
  - [ ] `batch` command processes job list file
  - [ ] Parallel processing where safe
  - [ ] Progress tracking
  - [ ] Error handling and retry logic
- **Files**: `src/scout/cli.py`
- **Dependencies**: EX-001, EX-002

#### 📋 OPT-003: Performance Tuning
- **Status**: 📋 Backlog
- **Priority**: 🟢 Low
- **Description**: Optimize retrieval and generation latency
- **Acceptance Criteria**:
  - [ ] Embedding generation < 2s per document
  - [ ] Retrieval < 500ms
  - [ ] Generation < 10s per document
  - [ ] Benchmark suite
- **Files**: Multiple
- **Dependencies**: All Phase 1-3 features

### User Experience

#### 📋 UX-001: CLI Improvements
- **Status**: 📋 Backlog
- **Priority**: 🟡 Medium
- **Description**: Enhanced CLI with better output formatting and progress indicators
- **Acceptance Criteria**:
  - [ ] Rich terminal output with colors
  - [ ] Progress bars for long operations
  - [ ] Better error messages
  - [ ] Helpful command suggestions
- **Files**: `src/scout/cli.py`
- **Dependencies**: Rich library

#### 📋 UX-002: Insights Dashboard
- **Status**: 📋 Backlog
- **Priority**: 🟡 Medium
- **Description**: Interactive dashboard showing job search insights
- **Acceptance Criteria**:
  - [ ] Success rate visualization
  - [ ] Timeline of applications
  - [ ] Skill gap trends
  - [ ] Recommendations display
- **Files**: `src/scout/cli.py` (or separate dashboard module)
- **Dependencies**: INT-005

#### 📋 UX-003: Profile Management Commands
- **Status**: 📋 Backlog
- **Priority**: 🟡 Medium
- **Description**: CLI commands for managing user profile
- **Acceptance Criteria**:
  - [ ] `profile add resume.pdf`
  - [ ] `profile update resume.pdf`
  - [ ] `profile view`
  - [ ] `profile skills add/remove`
- **Files**: `src/scout/cli.py`
- **Dependencies**: RAG-003

---

## Technical Debt

#### 📋 TD-001: Test Coverage
- **Status**: 📋 Backlog
- **Priority**: 🟡 Medium
- **Description**: Increase test coverage to >80%
- **Acceptance Criteria**:
  - [ ] Unit tests for all core functions
  - [ ] Integration tests for pipelines
  - [ ] Mock external APIs
  - [ ] Coverage report in CI
- **Files**: `tests/`
- **Dependencies**: Existing test infrastructure

#### 📋 TD-002: Error Handling
- **Status**: 📋 Backlog
- **Priority**: 🟡 Medium
- **Description**: Comprehensive error handling and logging
- **Acceptance Criteria**:
  - [ ] Custom exception types
  - [ ] Structured logging
  - [ ] Graceful degradation
  - [ ] User-friendly error messages
- **Files**: All modules
- **Dependencies**: None

#### 📋 TD-003: Documentation
- **Status**: 📋 Backlog
- **Priority**: 🟢 Low
- **Description**: API documentation and code comments
- **Acceptance Criteria**:
  - [ ] Docstrings for all public functions
  - [ ] Type hints throughout
  - [ ] Architecture diagrams
  - [ ] Usage examples
- **Files**: All modules
- **Dependencies**: None

#### 📋 TD-004: Configuration Management
- **Status**: 📋 Backlog
- **Priority**: 🟡 Medium
- **Description**: Centralized configuration with validation
- **Acceptance Criteria**:
  - [ ] Environment variable validation
  - [ ] Default values
  - [ ] Configuration file support
  - [ ] Runtime configuration updates
- **Files**: `src/scout/config.py`
- **Dependencies**: None

---

## Future Enhancements

#### 📋 FUT-001: Interview Prep Generator
- **Status**: 📋 Backlog
- **Priority**: 🟢 Low
- **Description**: Generate likely interview questions based on job posting
- **Acceptance Criteria**:
  - [ ] Extract key topics from job description
  - [ ] Generate behavioral questions
  - [ ] Generate technical questions
  - [ ] Provide answer templates
- **Dependencies**: INT-004

#### 📋 FUT-002: Negotiation Assistant
- **Status**: 📋 Backlog
- **Priority**: 🟢 Low
- **Description**: Analyze offer patterns and suggest negotiation strategies
- **Acceptance Criteria**:
  - [ ] Market rate analysis
  - [ ] Offer comparison
  - [ ] Negotiation script generation
  - [ ] Counter-offer suggestions
- **Dependencies**: INT-005

#### 📋 FUT-003: ATS Optimization
- **Status**: 📋 Backlog
- **Priority**: 🟢 Low
- **Description**: Keyword optimization for applicant tracking systems
- **Acceptance Criteria**:
  - [ ] Extract keywords from job posting
  - [ ] Score resume ATS compatibility
  - [ ] Suggest keyword additions
  - [ ] Format optimization
- **Dependencies**: GEN-002

#### 📋 FUT-004: Multi-modal Support
- **Status**: 📋 Backlog
- **Priority**: 🟢 Low
- **Description**: Support for portfolio images and video submissions
- **Acceptance Criteria**:
  - [ ] Image embedding (CLIP)
  - [ ] Video transcription and embedding
  - [ ] Multi-modal retrieval
  - [ ] Portfolio analysis
- **Dependencies**: RAG-002

#### 📋 FUT-005: Network Effects
- **Status**: 📋 Backlog
- **Priority**: 🟢 Low
- **Description**: Anonymous sharing of success patterns across users
- **Acceptance Criteria**:
  - [ ] Anonymized pattern sharing
  - [ ] Aggregate success metrics
  - [ ] Industry benchmarks
  - [ ] Privacy-preserving design
- **Dependencies**: INT-005

---

## Notes

- **Sprint Planning**: Focus on completing Phase 1 before moving to Phase 2
- **Dependencies**: Many tickets depend on RAG foundation (RAG-001, RAG-002, RAG-003)
- **Priority Order**: High priority tickets should be completed first within each phase
- **Testing**: Each feature should include tests before marking as done

---

*Last Updated: [Auto-updated on changes]*

