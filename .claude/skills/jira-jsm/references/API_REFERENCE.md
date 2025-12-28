# JSM API Endpoints Reference

Technical reference for JSM REST API endpoints used by this skill.

## Base URLs

**JSM Cloud**: `/rest/servicedeskapi/`
**Assets Cloud**: `/rest/insight/1.0/` or `/gateway/api/jsm/assets/`

---

## Service Desk APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/servicedesk` | List service desks |
| GET | `/servicedesk/{serviceDeskId}` | Get service desk |
| POST | `/servicedesk` | Create service desk |

---

## Request APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/request` | Create request |
| GET | `/request/{issueKey}` | Get request |
| GET | `/request/{issueKey}/status` | Get request status |
| POST | `/request/{issueKey}/transition` | Transition request |

---

## Customer APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/servicedesk/{id}/customer` | Add customer |
| GET | `/servicedesk/{id}/customer` | List customers |
| DELETE | `/servicedesk/{id}/customer` | Remove customer |

---

## Organization APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/organization` | Create organization |
| GET | `/servicedesk/{id}/organization` | List organizations |
| GET | `/organization/{id}` | Get organization |
| DELETE | `/organization/{id}` | Delete organization |
| POST | `/organization/{id}/user` | Add user to org |
| DELETE | `/organization/{id}/user` | Remove user from org |

---

## SLA APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/request/{issueKey}/sla` | Get SLA information |
| GET | `/request/{issueKey}/sla/{slaId}` | Get specific SLA |

---

## Approval APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/request/{issueKey}/approval` | Get approvals |
| POST | `/request/{issueKey}/approval/{id}` | Approve/decline |

---

## Queue APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/servicedesk/{id}/queue` | List queues |
| GET | `/servicedesk/{id}/queue/{queueId}/issue` | Get queue issues |

---

## Request Type APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/servicedesk/{id}/requesttype` | List request types |
| GET | `/servicedesk/{id}/requesttype/{id}` | Get request type |
| GET | `/servicedesk/{id}/requesttype/{id}/field` | Get request type fields |

---

## Comment APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/request/{issueKey}/comment` | Add comment |
| GET | `/request/{issueKey}/comment` | Get comments |

---

## Participant APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/request/{issueKey}/participant` | Add participant |
| GET | `/request/{issueKey}/participant` | Get participants |
| DELETE | `/request/{issueKey}/participant` | Remove participant |

---

## Assets APIs (JSM Assets License)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/rest/insight/1.0/object/create` | Create asset |
| GET | `/rest/insight/1.0/object/{id}` | Get asset |
| PUT | `/rest/insight/1.0/object/{id}` | Update asset |
| GET | `/rest/insight/1.0/objectschema/list` | List object schemas |
| GET | `/rest/insight/1.0/objecttype/{id}` | Get object type |

---

## Rate Limits

See [RATE_LIMITS.md](RATE_LIMITS.md) for rate limiting details.

---

## Official Documentation

- [JSM Cloud REST API](https://developer.atlassian.com/cloud/jira/service-desk/rest/intro/)
- [JSM Assets REST API](https://developer.atlassian.com/cloud/insight/rest/intro/)

---

*Last updated: December 2025*
