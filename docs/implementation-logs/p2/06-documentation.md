# Documentation Updates Across Skills

## Task Summary

Updated documentation across five JIRA skills to improve clarity, add missing sections, and enhance usability.

## Files Updated

### 1. `.claude/skills/jira-bulk/SKILL.md`

**Added Sections:**

#### Return Values and Exit Codes
- Documented exit codes (0 = success, 1 = failure, 130 = cancelled)
- Documented return dictionary structure for programmatic usage
- Included dry-run mode return structure

#### Rate Limiting and Delays
- Documented `delay_between_ops` parameter with default value (0.1s)
- Added guidance on when to adjust delay values
- Documented built-in retry logic for rate limits

---

### 2. `.claude/skills/jira-jsm/SKILL.md`

**Added Sections:**

#### Finding Service Desk IDs
- Method 1: List all service desks (recommended)
- Method 2: From project key
- Method 3: From JIRA URL patterns
- Method 4: From issue key
- Comparison table: Service Desk ID vs Project Key vs Project ID
- Environment variable tips for storing frequently used IDs

#### Rate Limiting Considerations
- JIRA Cloud rate limit reference table
- Built-in rate limit handling documentation
- Best practices for high-volume operations:
  - Batch requests when possible
  - Add delays for bulk operations
  - Use pagination for large result sets
  - Cache static data
- Monitoring rate limit status via response headers
- Error handling guidance for rate limit errors

---

### 3. `.claude/skills/jira-lifecycle/scripts/assign_issue.py`

**Updated:**

#### Module Docstring
- Expanded to explain the three accepted user identifier formats
- Added notes about reliability (account IDs preferred)
- Added guidance on finding account IDs

#### Argparse Help Text
- Enhanced `--user` argument help with detailed format descriptions
- Added multi-line epilog with examples for each usage pattern
- Included tip on finding account IDs via jql_search

---

### 4. `.claude/skills/jira-ops/SKILL.md`

**Added Section:**

#### Troubleshooting
Complete troubleshooting guide covering:

1. **Cache Database Cannot Be Opened**
   - Cache directory doesn't exist
   - Insufficient permissions
   - Corrupted database file
   - Disk full

2. **Cannot Connect to JIRA**
   - Missing JIRA credentials
   - Invalid profile specified
   - Network connectivity issues
   - Expired API token

3. **Cache Warm Takes Too Long**
   - Too many projects/fields
   - Rate limiting from JIRA
   - Large JIRA instance

4. **Cache Not Improving Performance**
   - TTL too short
   - Wrong category being cached
   - Cache invalidation too frequent

5. **Permission Denied Errors**
   - File ownership fixes
   - Permission fixes
   - User mismatch issues

6. **Debug Mode**
   - DEBUG environment variable usage

7. **Reset Everything**
   - Complete cache reset procedure

---

### 5. `.claude/skills/jira-search/SKILL.md`

**Added Section:**

#### Streaming Export for Large Data Sets
- How streaming export works (pagination, memory efficiency, progress tracking)
- Usage examples for large exports
- Performance considerations table by result size
- Optimization strategies:
  - Limiting fields
  - Splitting by date range
  - Scheduling during off-peak hours
- Output format examples (CSV and JSON)

**Updated:**
- Feature list to include streaming export capability
- Export examples section with additional commands

---

## Summary Statistics

| File | Sections Added | Lines Added |
|------|---------------|-------------|
| jira-bulk/SKILL.md | 2 | ~80 |
| jira-jsm/SKILL.md | 2 | ~135 |
| jira-lifecycle/scripts/assign_issue.py | N/A | ~20 |
| jira-ops/SKILL.md | 1 | ~170 |
| jira-search/SKILL.md | 1 | ~110 |

**Total**: 6 major documentation sections added across 5 files.

## Verification

All documentation follows the existing style and formatting conventions of the project:
- Markdown headers and code blocks
- Bash command examples with comments
- Tables for structured data
- Consistent terminology with other skill documentation
