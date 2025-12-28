# JSM Troubleshooting Guide

**Quick Navigation**:
- Need to get started? See [QUICK_START.md](QUICK_START.md)
- Looking for examples? See [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md)
- Want best practices? See [BEST_PRACTICES.md](BEST_PRACTICES.md)

---

Common issues and solutions when working with jira-jsm scripts.

## Authentication Errors

### "Authentication failed" (Exit Code 3)

**Problem**: Invalid or expired API token

**Solutions**:
1. Verify environment variables are set:
   ```bash
   echo $JIRA_URL
   echo $JIRA_EMAIL
   echo $JIRA_API_TOKEN
   ```

2. Generate new API token at [id.atlassian.com](https://id.atlassian.com/manage-profile/security/api-tokens)

3. Update your environment:
   ```bash
   export JIRA_API_TOKEN="your-new-token"
   ```

---

## Service Desk Errors

### "Service desk not found" (Exit Code 5)

**Problem**: Service desk ID or key is incorrect

**Solution**:
```bash
# List all service desks to find correct ID
python list_service_desks.py
```

### "Request type not found" (Exit Code 5)

**Problem**: Request type ID doesn't exist for service desk

**Solution**:
```bash
# List request types for service desk
python list_request_types.py --service-desk 1
```

---

## Customer Errors

### "Customer does not have permission"

**Problem**: User is not a customer of the service desk

**Solution**:
```bash
# Add user as customer first
python add_customer.py --service-desk 1 --user user@example.com
```

### "Customer already exists" (Exit Code 6)

**Problem**: Attempting to add a customer who is already registered

**Solution**: The customer is already added; no action needed.

---

## SLA Errors

### "SLA information not available"

**Problem**: Request doesn't have SLA configured or SLA feature disabled

**Solutions**:
- Verify SLA is configured in JSM project settings
- Check request type has SLA goals defined
- Ensure JSM license includes SLA features

---

## Assets Errors

### "Assets API not available" (403 Forbidden)

**Problem**: JSM Assets/Insight app not installed or licensed

**Solutions**:
- Install "Assets - For Jira Service Management" app from Atlassian Marketplace
- Verify Assets license is active
- Alternative: Use standard JIRA custom fields for asset tracking

---

## Approval Errors

### "Approval not found"

**Problem**: Request doesn't have approval workflow configured

**Solutions**:
- Verify request type has approval step in workflow
- Check automation rules for approval creation
- Manually add approvers if needed

---

## Rate Limit Errors

### HTTP 429 Too Many Requests (Exit Code 7)

**Problem**: API rate limit exceeded after retries

**Solutions**:
1. Reduce request frequency
2. Add delays between operations:
   ```bash
   for issue in SD-{100..200}; do
       python transition_request.py $issue --status "Resolved"
       sleep 0.5  # 500ms delay
   done
   ```
3. Spread operations over time
4. See [Rate Limits Reference](../references/RATE_LIMITS.md) for detailed guidance

---

## Permission Errors (Exit Code 4)

### "User lacks required JIRA permissions"

**Problem**: Your user doesn't have the necessary permissions

**Solutions**:
- Verify you have agent or admin access to the service desk
- Check project permissions in JIRA settings
- Contact your JIRA administrator

---

## Validation Errors (Exit Code 2)

### "Invalid input parameters"

**Problem**: Bad issue key, missing required field, or invalid format

**Common Issues**:
- Issue key format: Must be `PROJ-123` format
- Email format: Must be valid email for customer operations
- Date format: Use ISO format `YYYY-MM-DD`

**Solution**: Check script help for valid parameters:
```bash
python create_request.py --help
```

---

## Quick Diagnosis

### Check Exit Code

```bash
python get_request.py SD-123
echo $?  # 0 = success, non-zero = error
```

### Exit Code Reference

| Code | Meaning | Common Cause |
|------|---------|--------------|
| 0 | Success | Operation completed |
| 1 | General Error | Unspecified error |
| 2 | Validation Error | Invalid input |
| 3 | Authentication Error | Bad token |
| 4 | Permission Error | Missing permissions |
| 5 | Not Found | Resource doesn't exist |
| 6 | Conflict Error | Duplicate or state conflict |
| 7 | Rate Limit Error | API limit exceeded |

### Handle Errors in Scripts

```bash
python create_request.py --service-desk 1 --request-type 10 --summary "Test"
if [ $? -eq 3 ]; then
    echo "Authentication failed - check API token"
elif [ $? -eq 5 ]; then
    echo "Service desk not found"
fi
```

---

## Getting Help

### Script Documentation

All scripts support `--help`:
```bash
python create_request.py --help
python get_sla.py --help
```

### Verbose Output

Use JSON output for debugging:
```bash
python get_request.py SD-123 --output json
```

### Related Documentation

- [QUICK_START.md](QUICK_START.md) - Setup and first steps
- [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) - Working examples
- [../references/API_REFERENCE.md](../references/API_REFERENCE.md) - API endpoints
- [../references/CONFIG_REFERENCE.md](../references/CONFIG_REFERENCE.md) - Configuration

---

*Last updated: December 2025*
