# Fixes: pt-ba0n

## Critical Issues Fixed

### 1. XSS Vulnerability in data-signals (topics.html)
**Issue**: `data-signals:search="{{ search_query }}"` was vulnerable to HTML attribute injection.
**Fix**: Added explicit escaping with `|e` filter:
```html
data-signals:search="{{ search_query|e }}"
```

### 2. Template Injection in data-on:click (_topics_list.html)
**Issue**: Topic ID embedded directly in Datastar directive could break JavaScript string context.
**Fix**: Added URL encoding filter:
```html
data-on:click="@get('/topic/{{ topic.id|urlencode }}')"
```

### 3. Defensive Access in topic_detail.html
**Issue**: Doc path display used unsafe attribute access.
**Fix**: Added getattr with default:
```html
{{ topic_obj[doc_type].path if topic_obj and getattr(topic_obj, doc_type, None) else '' }}
```

## Major Issues Fixed

### 4. Search Query Length Limit (web_ui.py)
**Issue**: No input sanitization on search query.
**Fix**: Added trimming and 100-character limit in `get_topics_data()`:
```python
search_query = search_query.strip()[:100] if search_query else ""
```

### 5. Debounced Search Input (topics.html)
**Issue**: Search fired on every keystroke, causing excessive server load.
**Fix**: Added Datastar debounce modifier:
```html
data-on:input__debounce.300ms="@get('/api/topics?search=' + $search)"
```

## Note on "_topic_to_dict" Review Comment

The reviewer reported that `_topic_to_dict()` referenced non-existent properties `topic.has_overview`, etc. This was a misunderstanding - the code correctly accesses `topic.overview` (which exists) and stores the result in a dict key named `has_overview`. The implementation was correct and required no changes.

## Files Modified
- `tf_cli/web_ui.py` - Added search query sanitization
- `tf_cli/templates/topics.html` - Added escaping and debounce
- `tf_cli/templates/_topics_list.html` - Added URL encoding
- `tf_cli/templates/topic_detail.html` - Added defensive attribute access

## Verification
Run syntax check:
```bash
python -m py_compile tf_cli/web_ui.py
```
