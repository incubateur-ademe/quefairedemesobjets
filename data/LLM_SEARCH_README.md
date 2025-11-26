# LLM-Powered Search in SuggestionCohorteAdmin

## Summary of Changes

This implementation adds AI-powered natural language search to the Django admin interface for `SuggestionCohorte` models.

## Files Modified

### 1. `data/admin.py`
- Added `LLMQueryBuilder` class for safe, sandboxed query generation
- Enhanced `SuggestionCohorteAdmin` with `get_search_results()` override
- Integrated natural language query detection and processing

### 2. `pyproject.toml`
- Added `anthropic>=0.40.0,<1` dependency

### 3. `.env.template`
- Added `ANTHROPIC_API_KEY` configuration

## New Files

### 1. `docs/llm-powered-search.md`
Complete documentation including:
- Setup instructions
- Usage examples
- Security details
- Troubleshooting guide

### 2. `data/tests/test_llm_search.py`
Comprehensive test suite covering:
- LLM query builder functionality
- Admin integration
- Security and sandboxing
- Error handling

## Key Features

### 🔍 Natural Language Search
Search using plain language:
```
"show me failed enrichment suggestions"
```
Instead of complex queries:
```
statut = 'ERREUR' AND type_action ~ 'ENRICH'
```

### 🔒 Security & Sandboxing
- **Read-only operations**: LLM can only generate SELECT queries
- **Field validation**: All fields are validated against model schema
- **Safe execution**: All queries go through Django ORM
- **Error handling**: Graceful fallback to standard search

### 🎯 Smart Detection
Automatically detects:
- Natural language queries (uses LLM)
- DjangoQL queries (bypasses LLM)
- Empty queries (returns all)

## Installation

```bash
# 1. Install dependencies
uv sync

# 2. Add API key to .env
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env

# 3. Run migrations (if any)
python manage.py migrate

# 4. Restart server
```

## Usage Examples

### In Django Admin Search Box

**Simple queries:**
- `suggestions with errors`
- `successful clustering actions`
- `pending validation suggestions`

**Complex queries:**
- `show enrichment suggestions that failed last week`
- `clustering suggestions still pending validation`
- `suggestions with metadata containing error messages`

**Date-based:**
- `suggestions created yesterday`
- `recent failed suggestions`

## How It Works

```
User Query → Natural Language Detection → LLM Processing → 
JSON Filter Generation → Field Validation → Django ORM Filter → Results
                                ↓
                         (if error or unavailable)
                                ↓
                         Standard Search Fallback
```

## Security Architecture

### Layer 1: Prompt Engineering
```python
"IMPORTANT: Only generate READ operations. 
Never suggest create, update, or delete operations."
```

### Layer 2: Field Validation
```python
valid_fields = {field.name for field in model._meta.get_fields()}
if base_field not in valid_fields:
    logger.warning(f"Ignoring invalid field: {base_field}")
```

### Layer 3: Django ORM
- Only uses `.filter()` method
- No raw SQL execution
- No `eval()` or `exec()` calls

### Layer 4: Error Handling
```python
try:
    queryset = apply_llm_filters(queryset)
except Exception:
    return original_queryset  # Fallback
```

## Cost Analysis

**Per Search:**
- ~500 tokens input (prompt + schema)
- ~100 tokens output (JSON filter)
- ~$0.003 USD per search

**Monthly estimates:**
- 100 searches: ~$0.30
- 1,000 searches: ~$3.00
- 10,000 searches: ~$30.00

## Testing

Run the test suite:
```bash
pytest data/tests/test_llm_search.py -v
```

Test coverage:
- ✅ LLM query builder initialization
- ✅ Model schema generation
- ✅ API call handling
- ✅ Filter validation
- ✅ Q object generation
- ✅ Error handling
- ✅ Security measures
- ✅ Admin integration

## Configuration Options

### Environment Variables

```bash
# Required for LLM search
ANTHROPIC_API_KEY=sk-ant-...

# Optional: Model selection (default: claude-3-5-sonnet-20241022)
# ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Optional: Max tokens for response (default: 1024)
# ANTHROPIC_MAX_TOKENS=1024
```

## Monitoring

### Logs to Watch

```python
# Successful LLM search
logger.info(f"LLM search applied: {query} -> {filters}")

# LLM unavailable
logger.warning("ANTHROPIC_API_KEY not configured, skipping LLM search")

# Invalid field detected
logger.warning(f"Ignoring invalid field: {field_name}")

# LLM error
logger.error(f"LLM query generation failed: {error}")
```

### Admin Messages

Users see feedback:
```
✓ Recherche LLM appliquée pour: 'show failed suggestions'
```

## Limitations

### Current Limitations
- Only works with `SuggestionCohorte` model (can be extended)
- Requires internet connection to Anthropic API
- Rate limited by Anthropic API tier
- French/English language primarily

### Not Supported
- Aggregations (COUNT, SUM, etc.)
- Joins across models
- Updates/Deletes via search
- Raw SQL queries

## Future Enhancements

### Possible Improvements
1. **Query Caching**: Cache common queries to reduce API calls
2. **Multi-model Support**: Extend to other admin models
3. **Query History**: Save and reuse successful queries
4. **Autocomplete**: Suggest queries based on history
5. **Multi-language**: Better support for non-English queries
6. **Local LLM**: Option to use local models for privacy

### Performance Optimizations
- Implement query result caching
- Add rate limiting
- Use smaller/faster models for simple queries
- Batch multiple searches

## Troubleshooting

### Common Issues

**1. LLM search not working**
```bash
# Check API key
echo $ANTHROPIC_API_KEY

# Check logs
tail -f logs/django.log | grep LLM
```

**2. No results found**
- Try simpler query
- Check logs for generated filters
- Verify fields exist in model

**3. Rate limit errors**
- Reduce search frequency
- Use DjangoQL syntax to bypass LLM
- Upgrade Anthropic plan

**4. Import errors**
```bash
# Ensure anthropic is installed
uv sync
python -c "import anthropic; print(anthropic.__version__)"
```

## Contributing

When extending this feature:

1. **Always validate fields** before applying filters
2. **Log all LLM interactions** for debugging
3. **Provide fallback behavior** on errors
4. **Add tests** for new functionality
5. **Update documentation** with examples

## Support

For issues:
1. Check logs for error messages
2. Review documentation in `docs/llm-powered-search.md`
3. Run test suite to verify installation
4. Check Anthropic API status

## License

Same as parent project (MIT)
