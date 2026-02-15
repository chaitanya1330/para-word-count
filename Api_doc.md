# API Documentation - Para Word Count

## Base URL
`http://localhost:8000/user`

## Authentication
All endpoints require authentication token in header:
```
Authorization: Token YOUR_TOKEN_HERE
```

---

## 1. Save Paragraph

**POST** `/api/save-paragraph/`

### Input
```json
{
    "raw_text": "First paragraph text.\n\n\nSecond paragraph text."
}
```

### Output (201)
```json
{
    "status": "success",
    "message": "Saved and processed 2 paragraphs successfully",
    "paragraphs_created": 2,
    "paragraph_ids": [1, 2]
}
```

### Error (400)
```json
{
    "status": "error",
    "message": "Please enter at least one paragraph"
}
```

---

## 2. Search Word

**GET** `/api/search-word/?word=python`

### Input
Query parameter: `word=python`

### Output (200)
```json
{
    "status": "success",
    "word": "python",
    "results_count": 2,
    "results": [
        {
            "paragraph_id": 1,
            "user_name": "john",
            "raw_text": "Python is great...",
            "word_count": 5,
            "created_at": "2025-02-15T10:30:00Z"
        },
        {
            "paragraph_id": 3,
            "user_name": "john",
            "raw_text": "Python makes...",
            "word_count": 3,
            "created_at": "2025-02-15T11:20:00Z"
        }
    ]
}
```

### Error (400)
```json
{
    "status": "error",
    "message": "Word must be at least 2 characters"
}
```

---

## cURL Examples

### Save Paragraph
```bash
curl -X POST http://localhost:8000/user/api/save-paragraph/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"raw_text": "Text here.\n\n\nMore text."}'
```

### Search Word
```bash
curl -X GET "http://localhost:8000/user/api/search-word/?word=python" \
  -H "Authorization: Token YOUR_TOKEN"
```
