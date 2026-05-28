# Architecture Documentation

## Christianity AI Assistant - Technical Architecture

### Overview

This document describes the architecture of a Christianity-focused AI assistant designed to provide accurate, grounded, and safe responses to questions about the Bible and Christian faith.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                            │
│                    (Streamlit Chat App)                          │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ /chat       │  │ /image      │  │ /health                 │ │
│  └──────┬──────┘  └──────┬──────┘  └─────────────────────────┘ │
└─────────┼────────────────┼──────────────────────────────────────┘
          │                │
          ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Service Layer                                  │
│                                                                  │
│  ┌──────────────────┐    ┌──────────────────────────────────┐  │
│  │  LLM Service     │───▶│  Moderation Service              │  │
│  │  (Orchestration) │    │  - Input Safety Check            │  │
│  └────────┬─────────┘    │  - Output Validation             │  │
│           │              │  - Adversarial Detection         │  │
│           │              └──────────────────────────────────┘  │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────┐    ┌──────────────────────────────────┐  │
│  │  RAG Service     │───▶│  Memory Service                  │  │
│  │  - Query Enhance │    │  - Conversation History          │  │
│  │  - Retrieve      │    │  - Session Management            │  │
│  │  - Validate      │    │  - Denomination Tracking         │  │
│  └────────┬─────────┘    └──────────────────────────────────┘  │
│           │                                                     │
│           │              ┌──────────────────────────────────┐  │
│           │              │  Image Generation Service        │  │
│           │              │  - Prompt Safety Check           │  │
│           │              │  - Image Generation (DALL-E)     │  │
│           │              └──────────────────────────────────┘  │
└───────────┼─────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Layer                                    │
│                                                                  │
│  ┌──────────────────┐    ┌──────────────────────────────────┐  │
│  │  ChromaDB        │    │  Bible Data (JSON)               │  │
│  │  (Vector Store)  │◀───│  - 90+ Key Verses                │  │
│  │  - Embeddings    │    │  - Topics & Metadata             │  │
│  │  - Similarity    │    └──────────────────────────────────┘  │
│  └──────────────────┘                                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   External APIs                                  │
│  ┌──────────────────┐    ┌──────────────────────────────────┐  │
│  │  OpenAI GPT-4    │    │  OpenAI DALL-E 3                 │  │
│  │  - Chat          │    │  - Image Generation              │  │
│  │  - Embeddings    │    │                                  │  │
│  └──────────────────┘    └──────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

### 1. RAG-First Architecture

**Decision**: Use Retrieval-Augmented Generation (RAG) as the primary grounding mechanism for all Biblical responses.

**Rationale**:
- Prevents LLM hallucination of scripture
- Ensures cited verses actually exist
- Provides verifiable sources for every claim
- Allows for citation tracking and validation

**Implementation**:
- Bible verses are embedded using OpenAI's text-embedding-3-small
- Stored in ChromaDB with rich metadata (book, chapter, verse, topics)
- Every response retrieves relevant verses BEFORE generation
- Citations are validated against the retrieval context

### 2. Multi-Layer Safety Architecture

**Decision**: Implement safety checks at three levels: input, generation, and output.

**Rationale**:
- Catch adversarial attempts before LLM processing
- Prevent harmful content generation
- Validate that responses are properly grounded
- Handle edge cases gracefully

**Implementation**:

```
Input → [Pattern Detection] → [LLM Moderation] → [Processing]
                                                      │
                                                      ▼
                                    [Response Generation]
                                                      │
                                                      ▼
                          [Grounding Validation] → [Citation Check] → Output
```

### 3. Graceful Degradation for Invalid Requests

**Decision**: Handle invalid verse references and fake verses gracefully rather than refusing.

**Rationale**:
- Users may have honest mistakes
- Educational opportunity rather than rejection
- Maintains trust and helpfulness
- Distinguishes between malicious and accidental errors

**Implementation**:
- Verse validation checks book/chapter/verse existence
- Invalid references trigger helpful explanations
- Offers to find similar content on the topic
- No condescending tone

### 4. Denomination-Aware Responses

**Decision**: Track and respect user's denominational context while maintaining theological balance.

**Rationale**:
- Christianity has legitimate diversity of traditions
- Users deserve responses relevant to their context
- Avoids unintentional offense or confusion
- Maintains unity while acknowledging differences

**Implementation**:
- LLM-based denomination detection from messages
- Session-level denomination tracking
- System prompts encourage balanced perspectives
- Special handling for inter-denominational questions

### 5. Image Generation with Reverence

**Decision**: Transform all image requests through a "reverence filter" before generation.

**Rationale**:
- Sacred imagery requires respect
- Prevent subtle policy violations
- Ensure appropriateness for all Christian audiences
- Maintain spiritual tone

**Implementation**:
- Two-stage safety check (pattern + LLM)
- Prompt transformation to add reverence
- Safe alternative suggestions for rejected requests
- Curated theme suggestions

---

## Hallucination Prevention Strategies

### Strategy 1: Retrieval-Before-Generation

Every response that cites scripture MUST:
1. First retrieve verses from the vector database
2. Only cite verses present in the retrieval context
3. Include exact reference (Book Chapter:Verse) for every claim

### Strategy 2: Citation Validation

Post-generation validation checks:
- Extract all verse references from response
- Verify each exists in the provided context
- Flag ungrounded citations

### Strategy 3: Explicit Uncertainty

System prompts instruct the model to:
- Say "I don't have that verse in my reference" rather than fabricating
- Acknowledge when a topic isn't covered in available data
- Suggest alternatives rather than guessing

### Strategy 4: Fake Verse Detection

Proactive detection for:
- Non-existent book names
- Chapter numbers exceeding book length
- Common misattributed quotes
- Popular "Bible verses" that aren't biblical

---

## Edge Case Handling

### Adversarial Prompts

| Attack Type | Detection Method | Response |
|-------------|------------------|----------|
| Scripture manipulation | Regex + LLM | Firm refusal with explanation |
| Jailbreak attempts | Pattern matching | Redirect to purpose |
| Ideology injection | LLM moderation | Neutral, grounded response |
| Fake verse claims | Book/chapter validation | Helpful correction |

### Theological Controversies

| Scenario | Approach |
|----------|----------|
| Predestination debate | Present Reformed and Arminian views |
| Salvation (faith vs works) | Show Catholic and Protestant perspectives |
| Mary/Saints | Explain traditions without advocacy |
| End times | Present major interpretive frameworks |

### Sensitive Pastoral Topics

| Topic | Handling |
|-------|----------|
| Suffering/Evil | Compassionate, no pat answers |
| Doubt | Non-judgmental, encouraging |
| Loss/Grief | Comforting scripture, pastoral tone |
| Sin struggles | Grace-focused, not condemning |

---

## Data Flow: Chat Request

```
1. User sends message
   │
2. ├─► Moderation Service: Check input safety
   │   ├─► Pattern matching for adversarial content
   │   └─► LLM-based content classification
   │
3. ├─► [If unsafe] Return refusal response
   │
4. ├─► LLM Service: Enhance query for retrieval
   │
5. ├─► RAG Service: Retrieve relevant verses
   │   ├─► Generate query embedding
   │   ├─► Vector similarity search in ChromaDB
   │   └─► Return top-k verses with metadata
   │
6. ├─► Memory Service: Get conversation context
   │   ├─► Retrieve session history
   │   └─► Get user's denomination preference
   │
7. ├─► LLM Service: Generate response
   │   ├─► Build system prompt with context
   │   ├─► Include retrieved verses
   │   ├─► Include conversation history
   │   └─► Generate grounded response
   │
8. ├─► Moderation Service: Validate grounding
   │   └─► Verify all citations exist in context
   │
9. ├─► Memory Service: Store messages
   │
10.└─► Return response with citations
```

---

## Technology Choices

| Component | Technology | Rationale |
|-----------|------------|-----------|
| LLM | GPT-4 Turbo | Best reasoning, instruction following |
| Embeddings | text-embedding-3-small | Cost-effective, good quality |
| Vector DB | ChromaDB | Simple, local, good for demo |
| Image Gen | DALL-E 3 | High quality, content policies |
| Backend | FastAPI | Modern, async, great for AI apps |
| UI | Streamlit | Rapid prototyping, chat support |
| Memory | In-memory dict | Simple for demo; Redis for prod |

---

## Scalability Considerations

For production deployment:

1. **Vector Database**: Migrate to Pinecone or Weaviate for scale
2. **Caching**: Add Redis for conversation memory and embeddings cache
3. **Rate Limiting**: Implement per-user request limits
4. **Monitoring**: Add observability for safety violations
5. **Bible Data**: Expand to full Bible text (31,000+ verses)

---

## Security Measures

1. **API Key Protection**: Environment variables, not hardcoded
2. **Input Sanitization**: Max length limits, encoding validation
3. **Rate Limiting**: Prevent abuse through request throttling
4. **Audit Logging**: Track safety violations for review
5. **Content Policies**: Multi-layer content filtering

---

## Testing Strategy

### Unit Tests
- RAG retrieval accuracy
- Verse validation logic
- Moderation pattern matching

### Integration Tests
- End-to-end chat flow
- Image generation pipeline
- Session management

### Evaluation Suite
- Standard questions (10+ cases)
- Denomination handling (4+ cases)
- Edge cases (5+ cases)
- Adversarial prompts (15+ cases)
- Hallucination traps (15+ cases)

---

## Future Enhancements

1. **Full Bible Coverage**: Index all 31,102 verses
2. **Multi-language Support**: Add Bible translations in other languages
3. **Audio Features**: Bible verse audio playback
4. **Study Tools**: Cross-references, word studies
5. **User Accounts**: Save conversations, preferences
6. **Fine-tuned Model**: Christianity-specific model training

---

## Conclusion

This architecture prioritizes:
- **Accuracy** through RAG-based grounding
- **Safety** through multi-layer moderation
- **Respect** through denomination awareness
- **Trust** through transparent citations

The system is designed to be a helpful, accurate, and respectful assistant for exploring Christianity and the Bible.
