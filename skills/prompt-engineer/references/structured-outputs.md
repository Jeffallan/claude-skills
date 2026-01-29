# Structured Outputs

---

## Structured Output Methods

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STRUCTURED OUTPUT APPROACHES                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │   Prompt-Based  │  │   JSON Mode     │  │ Function Calling│            │
│  │                 │  │                 │  │ (Tool Use)      │            │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤            │
│  │ Reliability: ~  │  │ Reliability: ++ │  │ Reliability: +++│            │
│  │ Flexibility: +++│  │ Flexibility: ++ │  │ Flexibility: +  │            │
│  │ Validation: --- │  │ Validation: +   │  │ Validation: +++ │            │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│                                                                             │
│  Use when:          Use when:             Use when:                        │
│  - Simple extracts  - Need valid JSON     - Strict schemas required        │
│  - Flexible schemas - Moderate complexity - Tool orchestration             │
│  - Quick prototypes - Claude/GPT models   - Type-safe parsing              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Prompt-Based Structured Output

### Basic JSON Request

```
Extract the following information from the text and return as JSON:
- person_name: string
- company: string
- role: string
- email: string or null

Text: {text}

Return only valid JSON, no other text:
```

### With Schema Definition

```
Extract meeting information from the transcript.

Return a JSON object matching this schema:
{
  "meeting_title": "string - the main topic discussed",
  "date": "string - ISO 8601 format (YYYY-MM-DD) or null if not mentioned",
  "attendees": ["array of strings - names of participants"],
  "action_items": [
    {
      "task": "string - what needs to be done",
      "assignee": "string - who is responsible",
      "due_date": "string - ISO 8601 format or null"
    }
  ],
  "decisions": ["array of strings - key decisions made"],
  "next_meeting": "string - ISO 8601 datetime or null"
}

Rules:
- Use null for fields not mentioned in the transcript
- Use empty arrays [] for list fields with no items
- Dates must be in ISO 8601 format
- Return ONLY the JSON object, no explanation

Transcript:
{transcript}
```

### Output Wrapping Technique

```
Analyze the code and identify issues. Return your analysis in this exact format:

<analysis>
{
  "summary": "one sentence overview",
  "issues": [
    {
      "severity": "critical|high|medium|low",
      "type": "bug|security|performance|style",
      "location": "file:line or function name",
      "description": "what's wrong",
      "suggestion": "how to fix"
    }
  ],
  "quality_score": 1-10
}
</analysis>

Code:
{code}
```

Parsing with tags:

```python
import re
import json

def extract_tagged_json(response: str, tag: str = "analysis") -> dict:
    """Extract JSON from tagged output."""
    pattern = rf"<{tag}>\s*(.*?)\s*</{tag}>"
    match = re.search(pattern, response, re.DOTALL)

    if not match:
        raise ValueError(f"No <{tag}> tags found in response")

    return json.loads(match.group(1))
```

---

## JSON Mode (Claude & OpenAI)

### Claude JSON Mode

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-opus-4-5-20251101",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": """Extract entities from this text and return as JSON.

            Required fields:
            - people: array of {name, role}
            - organizations: array of {name, type}
            - locations: array of strings

            Text: {text}"""
        }
    ],
    # Claude uses system prompt to enforce JSON
    system="You are a JSON extraction assistant. Always respond with valid JSON only, no other text."
)

# Parse the response
result = json.loads(response.content[0].text)
```

### OpenAI JSON Mode

```python
from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4-turbo-preview",
    response_format={"type": "json_object"},  # Enforces JSON output
    messages=[
        {
            "role": "system",
            "content": "Extract information and return as JSON."
        },
        {
            "role": "user",
            "content": f"Extract people and companies from: {text}"
        }
    ]
)

result = json.loads(response.choices[0].message.content)
```

### JSON Mode Best Practices

| Practice | Why |
|----------|-----|
| Always describe expected schema | Model needs to know structure |
| Specify null handling | "Use null for missing fields" |
| Define array behavior | "Return empty array if none found" |
| Include field descriptions | Improves extraction accuracy |
| Add type annotations | "date: string in YYYY-MM-DD format" |

---

## Function Calling / Tool Use

### Claude Tool Use

```python
import anthropic

client = anthropic.Anthropic()

# Define the tool schema
tools = [
    {
        "name": "extract_contact",
        "description": "Extract contact information from text",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Full name of the person"
                },
                "email": {
                    "type": "string",
                    "description": "Email address"
                },
                "phone": {
                    "type": "string",
                    "description": "Phone number in E.164 format"
                },
                "company": {
                    "type": "string",
                    "description": "Company or organization name"
                },
                "title": {
                    "type": "string",
                    "description": "Job title or role"
                }
            },
            "required": ["name"]
        }
    }
]

response = client.messages.create(
    model="claude-opus-4-5-20251101",
    max_tokens=1024,
    tools=tools,
    tool_choice={"type": "tool", "name": "extract_contact"},  # Force tool use
    messages=[
        {
            "role": "user",
            "content": f"Extract contact info from: {business_card_text}"
        }
    ]
)

# Get structured output from tool call
for block in response.content:
    if block.type == "tool_use":
        contact = block.input  # Already parsed as dict
        print(f"Name: {contact['name']}")
        print(f"Email: {contact.get('email', 'N/A')}")
```

### OpenAI Function Calling

```python
from openai import OpenAI

client = OpenAI()

functions = [
    {
        "name": "analyze_sentiment",
        "description": "Analyze sentiment of customer feedback",
        "parameters": {
            "type": "object",
            "properties": {
                "sentiment": {
                    "type": "string",
                    "enum": ["positive", "negative", "neutral", "mixed"]
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1
                },
                "key_phrases": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Phrases that indicate sentiment"
                },
                "topics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Main topics discussed"
                }
            },
            "required": ["sentiment", "confidence"]
        }
    }
]

response = client.chat.completions.create(
    model="gpt-4-turbo-preview",
    messages=[
        {"role": "user", "content": f"Analyze this feedback: {feedback}"}
    ],
    functions=functions,
    function_call={"name": "analyze_sentiment"}  # Force specific function
)

# Parse function call
fn_call = response.choices[0].message.function_call
result = json.loads(fn_call.arguments)
```

---

## Schema Design Patterns

### Enum Constraints

```json
{
  "type": "object",
  "properties": {
    "priority": {
      "type": "string",
      "enum": ["critical", "high", "medium", "low"],
      "description": "Issue priority level"
    },
    "status": {
      "type": "string",
      "enum": ["open", "in_progress", "blocked", "resolved", "closed"]
    },
    "category": {
      "type": "string",
      "enum": ["bug", "feature", "improvement", "documentation"]
    }
  }
}
```

### Nested Objects

```json
{
  "type": "object",
  "properties": {
    "order": {
      "type": "object",
      "properties": {
        "id": {"type": "string"},
        "total": {"type": "number"},
        "currency": {"type": "string", "enum": ["USD", "EUR", "GBP"]},
        "items": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "product_id": {"type": "string"},
              "name": {"type": "string"},
              "quantity": {"type": "integer", "minimum": 1},
              "unit_price": {"type": "number", "minimum": 0}
            },
            "required": ["product_id", "quantity", "unit_price"]
          }
        },
        "shipping_address": {
          "$ref": "#/definitions/address"
        }
      },
      "required": ["id", "items"]
    }
  },
  "definitions": {
    "address": {
      "type": "object",
      "properties": {
        "street": {"type": "string"},
        "city": {"type": "string"},
        "state": {"type": "string"},
        "postal_code": {"type": "string"},
        "country": {"type": "string", "pattern": "^[A-Z]{2}$"}
      },
      "required": ["street", "city", "country"]
    }
  }
}
```

### Conditional Fields

```json
{
  "type": "object",
  "properties": {
    "contact_method": {
      "type": "string",
      "enum": ["email", "phone", "mail"]
    },
    "email": {"type": "string", "format": "email"},
    "phone": {"type": "string"},
    "address": {"$ref": "#/definitions/address"}
  },
  "required": ["contact_method"],
  "allOf": [
    {
      "if": {"properties": {"contact_method": {"const": "email"}}},
      "then": {"required": ["email"]}
    },
    {
      "if": {"properties": {"contact_method": {"const": "phone"}}},
      "then": {"required": ["phone"]}
    },
    {
      "if": {"properties": {"contact_method": {"const": "mail"}}},
      "then": {"required": ["address"]}
    }
  ]
}
```

---

## Validation and Error Handling

### Pydantic Validation (Python)

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from enum import Enum

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class CodeIssue(BaseModel):
    severity: Severity
    type: str = Field(..., pattern="^(bug|security|performance|style)$")
    location: str
    description: str = Field(..., min_length=10, max_length=500)
    suggestion: Optional[str] = None

    @validator('location')
    def validate_location(cls, v):
        if ':' not in v and '(' not in v:
            raise ValueError('Location must be file:line or function()')
        return v

class CodeAnalysis(BaseModel):
    summary: str = Field(..., max_length=200)
    issues: List[CodeIssue]
    quality_score: int = Field(..., ge=1, le=10)

    @validator('issues')
    def critical_issues_first(cls, v):
        return sorted(v, key=lambda x: list(Severity).index(x.severity))

# Usage
def parse_analysis(llm_response: str) -> CodeAnalysis:
    """Parse and validate LLM response."""
    try:
        data = json.loads(llm_response)
        return CodeAnalysis(**data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")
    except ValidationError as e:
        raise ValueError(f"Schema validation failed: {e}")
```

### Zod Validation (TypeScript)

```typescript
import { z } from 'zod';

const SeveritySchema = z.enum(['critical', 'high', 'medium', 'low']);

const CodeIssueSchema = z.object({
  severity: SeveritySchema,
  type: z.enum(['bug', 'security', 'performance', 'style']),
  location: z.string().regex(/[:()]/, 'Must be file:line or function()'),
  description: z.string().min(10).max(500),
  suggestion: z.string().optional(),
});

const CodeAnalysisSchema = z.object({
  summary: z.string().max(200),
  issues: z.array(CodeIssueSchema),
  quality_score: z.number().int().min(1).max(10),
});

type CodeAnalysis = z.infer<typeof CodeAnalysisSchema>;

function parseAnalysis(llmResponse: string): CodeAnalysis {
  const data = JSON.parse(llmResponse);
  return CodeAnalysisSchema.parse(data);
}
```

### Retry with Correction

```python
def get_structured_output(
    prompt: str,
    schema: dict,
    max_retries: int = 3
) -> dict:
    """Get structured output with automatic retry on validation failure."""

    for attempt in range(max_retries):
        response = llm.complete(prompt)

        try:
            data = json.loads(response)
            validate(data, schema)  # JSON Schema validation
            return data
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON at position {e.pos}: {e.msg}"
        except ValidationError as e:
            error_msg = format_validation_error(e)

        # Retry with error feedback
        if attempt < max_retries - 1:
            prompt = f"""Your previous response had an error:
{error_msg}

Please fix and try again. Return only valid JSON matching the schema.

Original request:
{prompt}"""

    raise ValueError(f"Failed to get valid output after {max_retries} attempts")
```

---

## Complex Extraction Patterns

### Multi-Entity Extraction

```
Extract all entities from the following document.

Return JSON with this structure:
{
  "people": [
    {
      "name": "full name",
      "aliases": ["nicknames or alternate names"],
      "role": "their role/position if mentioned",
      "mentioned_with": ["names of people they're associated with"]
    }
  ],
  "organizations": [
    {
      "name": "organization name",
      "type": "company|nonprofit|government|education|other",
      "location": "headquarters if mentioned"
    }
  ],
  "events": [
    {
      "name": "event name",
      "date": "YYYY-MM-DD or null",
      "location": "where it happened",
      "participants": ["people or organizations involved"]
    }
  ],
  "relationships": [
    {
      "entity1": "name",
      "entity2": "name",
      "type": "works_at|acquired|partnered|competed|invested",
      "details": "additional context"
    }
  ]
}

Document:
{document}
```

### Hierarchical Data Extraction

```
Parse this organizational structure and return as JSON:

{
  "organization": {
    "name": "company name",
    "departments": [
      {
        "name": "department name",
        "head": "department head name",
        "teams": [
          {
            "name": "team name",
            "lead": "team lead name",
            "members": ["member names"],
            "responsibilities": ["key responsibilities"]
          }
        ]
      }
    ]
  }
}

Text:
{org_description}
```

### Form Data Extraction

```
Extract form data from this image/document.

Return JSON:
{
  "form_type": "detected form type",
  "fields": {
    "field_name": {
      "value": "extracted value",
      "confidence": 0.0-1.0,
      "location": "where on form (if applicable)"
    }
  },
  "checkboxes": {
    "checkbox_label": true/false
  },
  "signatures": [
    {
      "signer": "name if readable",
      "date": "date if present",
      "location": "signature location on form"
    }
  ],
  "missing_fields": ["fields that appear required but are empty"]
}

Document content:
{document}
```

---

## Performance Optimization

### Batch Processing

```python
async def extract_structured_batch(
    items: list,
    schema: dict,
    batch_size: int = 10
) -> list:
    """Process multiple items efficiently."""
    results = []

    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]

        # Create batch prompt
        prompt = f"""Extract information from each item below.
Return a JSON array with one object per item, matching this schema:
{json.dumps(schema, indent=2)}

Items:
{json.dumps([{"index": j, "content": item} for j, item in enumerate(batch)])}

Response (JSON array only):"""

        response = await llm.complete_async(prompt)
        batch_results = json.loads(response)
        results.extend(batch_results)

    return results
```

### Schema Simplification

**Overly complex schema (expensive):**
```json
{
  "analysis": {
    "sentiment": {
      "overall": {"score": -1 to 1, "label": "string"},
      "aspects": [{"aspect": "string", "sentiment": {...}}]
    },
    "entities": [...],
    "topics": [...],
    "summary": {...}
  }
}
```

**Simplified schema (cost-effective):**
```json
{
  "sentiment": "positive|negative|neutral",
  "confidence": 0.0-1.0,
  "key_points": ["string"]
}
```

---

## Common Pitfalls

| Pitfall | Problem | Solution |
|---------|---------|----------|
| No schema in prompt | Model invents structure | Always specify expected schema |
| Ambiguous field names | Inconsistent extraction | Use descriptive names with examples |
| Missing null handling | Errors on optional fields | Explicitly state "null if not found" |
| Complex nested schemas | Inconsistent output | Flatten when possible |
| No validation | Silent failures | Always validate with Pydantic/Zod |
| Large schemas | Token waste, confusion | Split into multiple calls |

---

## Related Skills

- **API Designer** - Schema design for APIs
- **Data Engineer** - Data validation pipelines
- **RAG Architect** - Structured extraction for retrieval
