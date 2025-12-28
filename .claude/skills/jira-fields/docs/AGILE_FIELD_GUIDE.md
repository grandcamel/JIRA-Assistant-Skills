# Agile Field Configuration Guide

Complete guide to configuring Agile fields for Scrum and Kanban boards.

---

## Essential Agile Fields

### Must-Have for Scrum

| Field | Purpose | Required For |
|-------|---------|--------------|
| **Sprint** | Track sprint assignment | Sprint planning, burndown |
| **Story Points** | Estimate effort | Velocity tracking, planning |
| **Epic Link** | Group related stories | Epic progress, roadmaps |

### Nice-to-Have

| Field | Purpose | Required For |
|-------|---------|--------------|
| **Rank** | Manual backlog ordering | Priority visualization |
| **Epic Name** | Visible epic identifier | Board display |
| **Epic Color** | Visual distinction | Quick epic recognition |

---

## Scrum vs Kanban Decision Tree

```
Using sprints for time-boxed iterations?
  |
  +-- Yes (Scrum)
  |    Required fields:
  |    - Sprint (mandatory)
  |    - Story Points (recommended)
  |    - Epic Link (recommended)
  |
  +-- No (Kanban)
       Required fields:
       - Rank (for ordering)
       - Optional: Story Points for metrics
       - Optional: Epic Link for grouping
```

---

## Project Type Configuration

### Company-Managed Projects

Full API support for field configuration:

```bash
# Step 1: Verify project type
python check_project_fields.py PROJ --check-agile

# Step 2: Preview changes
python configure_agile_fields.py PROJ --dry-run

# Step 3: Apply configuration
python configure_agile_fields.py PROJ

# Step 4: Verify
python check_project_fields.py PROJ --type Story
```

### Team-Managed Projects

Limited API support - use JIRA UI:

1. Go to **Project Settings > Features**
2. Enable **Epics** feature
3. Enable **Story Points** under Estimation
4. Configure in **Issue Types** settings

**Note:** Epic Link uses built-in parent link in team-managed projects.

---

## Board Configuration

### Story Points on Board

After field is available:

1. Board > **Configure** > **Estimation**
2. Set **Estimation Statistic** to "Story Points"
3. Select correct custom field (verify ID with `list_fields.py --agile`)
4. Save

### Card Layout

Display key fields on board cards:

1. Board > **Configure** > **Card Layout**
2. Add fields:
   - Story Points (as badge)
   - Assignee
   - Priority
   - Labels
3. Save

---

## Sprint Field Setup

### Automatic Setup (Scrum Template)

When creating a project with Scrum template:
- Sprint field created automatically
- Managed by board configuration
- Available on backlog and active sprints

### Manual Setup (Existing Project)

```bash
# Verify Sprint field exists
python list_fields.py --filter "sprint"

# Check project access
python check_project_fields.py PROJ --check-agile

# Configure if needed
python configure_agile_fields.py PROJ
```

### Sprint Field Behavior

- **Cannot edit directly** on issues
- Managed via backlog operations:
  - Move to sprint
  - Move out of sprint
  - Start/complete sprint

---

## Story Points Configuration

### Step-by-Step Setup

```bash
# Step 1: Find field ID
python list_fields.py --filter "story"
# Output: customfield_10016  Story Points  float  Yes

# Step 2: Check project access
python check_project_fields.py PROJ --type Story

# Step 3: Configure Agile fields
python configure_agile_fields.py PROJ --story-points customfield_10016
```

### Board Configuration

1. Go to Board > Configure
2. Select **Estimation**
3. Choose **Story Point Estimate**
4. Select the correct field from dropdown
5. Save

### Recommended Values (Fibonacci)

| Points | Meaning |
|--------|---------|
| 1 | Trivial change |
| 2 | Small task |
| 3 | Standard work |
| 5 | Complex work |
| 8 | Large task |
| 13 | Very large task |
| 21 | Consider splitting |

---

## Epic Link Configuration

### Company-Managed Projects

```bash
# Verify Epic Link field
python list_fields.py --filter "epic"

# Check if available
python check_project_fields.py PROJ --check-agile

# Configure
python configure_agile_fields.py PROJ
```

Add Epic Link to:
- Story create screen
- Story edit screen
- Task create screen
- Task edit screen
- Bug create screen
- Bug edit screen

### Team-Managed Projects

Uses built-in parent/child linking:

1. Project Settings > Issue Types
2. Enable **Epic** issue type
3. Child issues automatically have parent picker
4. No custom Epic Link field needed

---

## Rank Field Setup

### Purpose
Global ordering on backlogs and boards.

### Configuration
Usually automatic with Agile boards:
- Created when first board is set up
- Managed by drag-and-drop operations
- Read-only in most contexts

### Troubleshooting

```bash
# Find Rank field
python list_fields.py --filter "rank"

# If missing, verify Agile plugin is enabled
# Go to JIRA admin > Applications > JIRA Software
```

---

## Common Workflows

### New Scrum Project Setup

```bash
# 1. Check project type
python check_project_fields.py PROJ --check-agile

# 2. If company-managed, configure fields
python configure_agile_fields.py PROJ --dry-run
python configure_agile_fields.py PROJ

# 3. Verify Story issue type has fields
python check_project_fields.py PROJ --type Story

# 4. Configure board (in JIRA UI)
# Board > Configure > Estimation > Story Points
```

### Kanban-to-Scrum Migration

```bash
# 1. Verify Sprint field exists
python list_fields.py --agile

# 2. Add Sprint field to project
python configure_agile_fields.py PROJ

# 3. Create Scrum board or convert existing
# Board > Configure > Change board type
```

### Missing Field Diagnosis

```bash
# 1. List all Agile fields in instance
python list_fields.py --agile

# 2. Check project availability
python check_project_fields.py PROJ --check-agile

# 3. Compare outputs to identify gaps

# 4. For missing fields:
#    - Company-managed: Use configure_agile_fields.py
#    - Team-managed: Enable in Project Settings > Features
```

---

## Troubleshooting

### "Story Points field not configured"

1. Verify field ID: `python list_fields.py --agile`
2. Check board configuration: Board > Configure > Estimation
3. Ensure correct field selected in board settings

### "Sprint not available"

1. Check project type: `python check_project_fields.py PROJ`
2. Verify Scrum board exists for project
3. For team-managed: Enable Sprints in Project Settings

### "Epic Link not visible"

1. Check field exists: `python list_fields.py --filter "epic"`
2. Check project access: `python check_project_fields.py PROJ --check-agile`
3. Verify field is on issue create screen

---

## Cross-References

- [Agile Field IDs Reference](../assets/agile-field-ids.md) - Field ID lookup
- [Quick Start Guide](QUICK_START.md) - Get started fast
- [Field Types Reference](FIELD_TYPES_REFERENCE.md) - All field types
- [Best Practices](BEST_PRACTICES.md) - Design principles
