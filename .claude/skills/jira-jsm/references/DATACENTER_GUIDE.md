# JSM Data Center Integration Guide

Notes for using jira-jsm with JIRA Data Center instead of Cloud.

## Overview

This skill is optimized for **JSM Cloud**. Data Center support is partial and may require configuration adjustments.

---

## API Endpoint Differences

| Feature | Cloud Endpoint | Data Center Endpoint |
|---------|----------------|---------------------|
| Service Desk API | `/rest/servicedeskapi/*` | `/rest/servicedesk/1/*` |
| Customer API | Uses email addresses | May use usernames |
| Assets/Insight | Separate app required | Built-in (version dependent) |
| Request create | `/rest/servicedeskapi/request` | `/rest/servicedesk/1/request` |

---

## Customer/User Identification

### Cloud

Uses email addresses for customer identification:

```bash
python add_customer.py --service-desk 1 --user user@example.com
python create_request.py --on-behalf-of user@example.com
```

### Data Center

May require usernames instead of email addresses:

```bash
python add_customer.py --service-desk 1 --user jdoe
python create_request.py --on-behalf-of jdoe
```

---

## Assets/Insight Integration

### Cloud

- Requires separate "Assets - For Jira Service Management" app
- API: `/rest/insight/1.0/*` or newer `/gateway/api/jsm/assets/*`
- Free tier available (up to 100 assets)

### Data Center

- May be built-in depending on version (8.x vs 9.x)
- API paths may differ: `/rest/insight/1.0/*`
- Full functionality included with JSM license

---

## Version Compatibility

| Version | Notes |
|---------|-------|
| Data Center 8.x | Limited JSM API support, some endpoints differ |
| Data Center 9.0+ | Better API parity with Cloud |
| Cloud | Primary target, all features supported |

---

## Migration Checklist

When adapting scripts for Data Center:

1. **Update API endpoint paths** in shared library configuration
2. **Change customer identifiers** from email to username (or vice versa)
3. **Verify Assets API availability** and endpoint paths
4. **Test SLA APIs** as response formats may differ slightly
5. **Check approval workflow APIs** for differences in approval state handling

---

## Profile-Based Configuration

Use separate profiles for Cloud and Data Center instances:

```bash
# Cloud instance
python list_service_desks.py --profile cloud-prod

# Data Center instance
python list_service_desks.py --profile dc-prod
```

### Profile Configuration Example

```json
{
  "profiles": {
    "cloud-prod": {
      "url": "https://company.atlassian.net",
      "use_service_management": true
    },
    "dc-prod": {
      "url": "https://jira.company.internal",
      "use_service_management": true,
      "api_path_prefix": "/rest/servicedesk/1"
    }
  }
}
```

---

## Known Limitations

1. **Customer API differences**: Email vs username identification varies
2. **Assets API availability**: Depends on Data Center version and plugins
3. **SLA response format**: May have slight differences in JSON structure
4. **Approval workflows**: State names and transitions may differ

---

*Last updated: December 2025*
