# LLM-Powered Admin Search

## Overview

The `SuggestionCohorteAdmin` now includes LLM-powered natural language search functionality. This allows administrators to search using human-readable queries that are automatically converted into Django ORM filters.

## Features

- **Natural Language Search**: Search using plain language queries instead of complex ORM syntax
- **Read-Only Sandboxing**: The LLM is restricted to generating read-only queries only
- **Automatic Fallback**: Falls back to standard Django search if LLM is unavailable
- **Field Validation**: All LLM-generated filters are validated against the model schema
- **Safe Execution**: All queries are executed through Django ORM, preventing SQL injection

## Setup

### 1. Install Dependencies

The `anthropic` package is required:

```bash
uv sync
```

### 2. Configure API Key

Add your Anthropic API key to your environment variables:

```bash
# .env file
ANTHROPIC_API_KEY=sk-ant-...
```

You can obtain an API key from: https://console.anthropic.com/

### 3. Restart Django

After configuration, restart your Django server to pick up the new settings.

## Usage

### Basic Natural Language Queries

In the SuggestionCohorte admin search box, you can now use natural language queries:

**Examples:**

- `suggestions validated successfully`
  - Searches for suggestions with status "SUCCES"

- `errors from enrichment actions`
  - Searches for suggestions with status "ERREUR" and type_action containing "ENRICH"

- `clustering suggestions still pending`
  - Searches for clustering type actions with status "AVALIDER"

- `suggestions from last week`
  - Searches for suggestions created in the last 7 days

- `failed suggestions with metadata errors`
  - Searches for suggestions with ERREUR status and checks metadata field

### How It Works

1. **Natural Language Detection**: The system detects if your search query is natural language (contains spaces, no special operators)

2. **LLM Processing**: Your query is sent to Claude (Anthropic's LLM) along with the model schema

3. **Query Generation**: Claude generates Django ORM filter parameters in JSON format

4. **Validation**: The system validates that all fields exist in the model

5. **Execution**: Safe, read-only filters are applied to the queryset

6. **Fallback**: If LLM fails or is unavailable, standard Django search is used

### Example LLM Response

For a query like "show me failed enrichment suggestions":

```json
{
  "filters": {
    "statut__exact": "ERREUR",
    "type_action__icontains": "ENRICH"
  }
}
```

This gets converted to:
```python
SuggestionCohorte.objects.filter(
    statut__exact="ERREUR",
    type_action__icontains="ENRICH"
)
```

## Security & Sandboxing

### Read-Only Enforcement

The LLM is explicitly instructed to generate only READ operations. The system enforces this through:

1. **Prompt Engineering**: The LLM is told never to suggest write operations
2. **QuerySet API**: Only `.filter()` is used, which is read-only
3. **Field Validation**: Only existing model fields are allowed
4. **Django ORM**: All queries go through Django's ORM layer

### Safe by Design

- No raw SQL execution
- No `eval()` or `exec()` calls
- No database writes possible
- Field names are validated against model schema
- Errors are caught and logged, returning the original queryset

### What Cannot Happen

The LLM cannot:
- Create, update, or delete records
- Execute arbitrary Python code
- Access fields not in the model
- Bypass Django's ORM protections
- Execute raw SQL

## Monitoring

### Logs

All LLM searches are logged for monitoring:

```python
logger.info(f"LLM search applied: {search_query} -> {llm_response}")
logger.error(f"LLM query generation failed: {error}")
logger.warning(f"Ignoring invalid field: {field_name}")
```

### User Feedback

When an LLM search is applied, a success message is shown:
```
Recherche LLM appliquée pour: 'your search query'
```

## Troubleshooting

### LLM Search Not Working

1. **Check API Key**: Ensure `ANTHROPIC_API_KEY` is set correctly
2. **Check Logs**: Look for error messages in Django logs
3. **Network**: Ensure server can reach Anthropic's API
4. **Fallback**: Standard search will work even if LLM fails

### No Results Found

- Try rephrasing your query
- Check if the fields you're searching exist in the model
- Look at logs to see what filters were generated
- Try a simpler query first

### API Rate Limits

If you hit API rate limits:
- Reduce search frequency
- Use standard Django search operators (=, ~, etc.) which bypass LLM
- Upgrade your Anthropic API plan

## Model Schema

The LLM has access to these SuggestionCohorte fields:

- `id`: AutoField
- `identifiant_action`: CharField
- `identifiant_execution`: CharField
- `type_action`: CharField (choices: see SuggestionAction)
- `statut`: CharField (choices: AVALIDER, ENCOURS, SUCCES)
- `metadata`: JSONField
- `cree_le`: DateTimeField
- `modifie_le`: DateTimeField

## Advanced Examples

### Complex Queries

```
show me suggestions created after 2024-01-01 with status pending or in progress
```

Generates:
```python
Q(cree_le__gte="2024-01-01") & (Q(statut="AVALIDER") | Q(statut="ENCOURS"))
```

### Metadata Search

```
suggestions with error in metadata
```

Generates:
```python
metadata__icontains="error"
```

## Cost Considerations

Each LLM search query costs approximately:
- Input: ~500 tokens (model schema + prompt)
- Output: ~100 tokens (JSON response)
- Cost: ~$0.003 per search at current Anthropic pricing

For high-traffic admin sites, consider:
- Caching common queries
- Setting usage limits
- Using standard search for simple queries

## Future Enhancements

Potential improvements:
- Query result caching
- Query suggestion/autocomplete
- Multi-language support
- Custom model schemas
- Query history and favorites
- A/B testing vs standard search
