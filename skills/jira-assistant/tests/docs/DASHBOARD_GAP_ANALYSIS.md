# Grafana Dashboard Gap Analysis

**Document Version:** 1.0
**Date:** 2026-01-01
**Author:** Claude Code Analysis
**Status:** Draft - Pending Stakeholder Review

---

## Executive Summary

This document provides a comprehensive gap analysis of the four Grafana dashboards for JIRA Assistant Skills routing tests. It compares current implementation against the needs of four key audiences: Executives, QA Engineers, LLM Skills Engineers, and Site Reliability Engineers.

**Key Findings:**
- Current dashboards provide solid foundational observability
- Critical gaps exist in SKILL.md change correlation (Skills Engineers)
- ROI metrics and trend deltas missing (Executives)
- Flaky test detection and disambiguation validation needed (QA)
- API health and worker utilization metrics missing (SRE)

---

## Table of Contents

1. [Current Implementation Overview](#current-implementation-overview)
2. [Clarifying Questions](#clarifying-questions)
3. [Gap Analysis by Audience](#gap-analysis-by-audience)
   - [Executives](#1-executives)
   - [QA Engineers](#2-qa-engineers)
   - [LLM Skills Engineers](#3-llm-skills-engineers)
   - [Site Reliability Engineers](#4-site-reliability-engineers)
4. [Priority Matrix](#priority-matrix)
5. [Recommendations](#recommendations)

---

## Current Implementation Overview

### OpenTelemetry Instrumentation (otel_metrics.py)

#### Metrics Exported
| Metric Name | Type | Description |
|-------------|------|-------------|
| `routing_test_total` | Counter | Total tests with labels (category, result, expected_skill, actual_skill, model, routing_correct, clarification_asked, error_type) |
| `routing_test_duration_seconds` | Histogram | Test duration distribution |
| `routing_test_cost_usd` | Histogram | API cost per test |
| `routing_accuracy_percent` | Gauge | Current accuracy percentage |
| `tool_use_accuracy_percent` | Gauge | Tool use accuracy percentage |

#### Trace Span Attributes
| Category | Attributes |
|----------|------------|
| **Test Identification** | test.id, test.category, test.name |
| **Input Context** | test.input, test.input.length, test.input.hash, test.input.word_count |
| **Routing Context** | test.expected_skill, test.actual_skill, test.routing_correct, test.asked_clarification, test.disambiguation_options |
| **Result Context** | test.passed, test.result, test.duration_ms, test.cost_usd |
| **Claude Context** | claude.session_id, claude.model, claude.tokens.input, claude.tokens.output, claude.retry_count |
| **Error Context** | error.type, error.message |
| **Version Context** | skill.version, vcs.branch, vcs.commit.sha |
| **Tool Use Context** | tool_use.accuracy, tool_use.matched_patterns, tool_use.total_patterns |

#### Resource Attributes
- service.name, service.version, service.namespace
- deployment.environment
- host.name, os.type, os.version
- python.version, otel.sdk.version
- vcs.commit.sha, vcs.branch
- skill.version, golden_set.version, claude.cli.version

#### Span Hierarchy
```
routing_test_suite (session-level)
├── worker_gw0 (pytest-xdist worker)
│   ├── routing_test_TC001
│   ├── routing_test_TC002
│   └── ...
├── worker_gw1
│   ├── routing_test_TC003
│   └── ...
└── ...
```

### Dashboard Summary

| Dashboard | UID | Primary Audience | Refresh Rate | Time Range |
|-----------|-----|------------------|--------------|------------|
| Executive Summary | `routing-executive` | Leadership | 5m | 7d |
| QA Engineer | `routing-qa-engineer` | QA Team | 30s | 6h |
| Skills Engineer A/B | `routing-skills-ab` | ML/Skills Team | 1m | 24h |
| SRE Operations | `routing-sre-ops` | SRE Team | 30s | 24h |

---

## Clarifying Questions

Before implementing enhancements, the following questions need stakeholder input:

### Data Retention & Historical Analysis
1. What is the desired retention period for metrics? (Currently queries use 24h-7d windows)
2. Do you need comparative analysis against historical baselines (e.g., "accuracy vs. last release")?
3. Should we maintain a "golden baseline" snapshot for regression comparison?

### Alerting Requirements
4. Are these dashboards for passive monitoring, or should they trigger alerts?
5. What SLOs/SLIs exist for routing accuracy, latency, and cost?
6. Who should receive alerts (Slack channel, PagerDuty, email)?

### CI/CD Integration
7. Should dashboards show PR-specific metrics (e.g., "how did this branch compare to main")?
8. Is there automated quality gate decision-making based on these metrics?
9. Should failed tests block merges automatically?

### Token Economics
10. Is token count tracking important for cost attribution?
11. Do you need breakdown by input vs output tokens?
12. Are there budget caps per model or per run?

### Multi-Instance Support
13. Will tests run against multiple JIRA profiles/environments?
14. Need environment-level filtering (dev/staging/prod)?
15. Should different environments have different SLOs?

---

## Gap Analysis by Audience

### 1. EXECUTIVES

#### Currently Implemented ✅
| Feature | Panel ID | Description |
|---------|----------|-------------|
| Overall accuracy gauge | 2 | Shows current routing accuracy % |
| Total tests, passed, failed | 3, 4, 5 | Count statistics |
| Total cost (7d) | 6 | Cumulative API spend |
| Accuracy trend (7 days) | 11 | Time series of accuracy |
| Status indicator | 12 | HEALTHY/ACCEPTABLE/NEEDS WORK/CRITICAL |
| Model comparison | 15 | Bar chart by model |
| Top issues | 16 | Most failed tests |

#### Gaps Identified ❌

| Gap | Description | Business Impact | Priority |
|-----|-------------|-----------------|----------|
| **ROI Metrics** | No "cost per successful user interaction" or business value correlation | Executives can't justify spend or measure value | HIGH |
| **Week-over-Week Trends** | No delta indicators (+5% vs last week) | No sense of momentum or improvement velocity | HIGH |
| **Release Comparison** | No "before/after this release" comparison | Can't correlate development effort to results | MEDIUM |
| **Budget Burn Rate** | No projected monthly cost or budget tracking | Hard to forecast or set budget expectations | MEDIUM |
| **Skill Coverage Heatmap** | Which skills are tested most/least | Risk visibility into untested areas | LOW |
| **Executive Summary Text** | No AI-generated summary paragraph | Quick understanding without chart interpretation | LOW |

#### Recommended Additions
```yaml
New Panels:
  - name: "Improvement Delta"
    type: stat
    description: "+X% vs previous period with trend arrow"

  - name: "Projected Monthly Cost"
    type: gauge
    description: "Extrapolated cost with budget threshold lines"

  - name: "Release Comparison"
    type: barchart
    description: "Current vs previous release accuracy side-by-side"

  - name: "Skills Coverage"
    type: treemap
    description: "Test distribution across skills, sized by test count"
```

---

### 2. QA ENGINEERS

#### Currently Implemented ✅
| Feature | Panel ID | Description |
|---------|----------|-------------|
| Test suite summary | 2-7 | Total, passed, failed, pass rate, avg duration, last run |
| Results by category | 9 | Stacked bar chart |
| Pass rate by category | 10 | Bar gauge per category |
| Failed tests detail | 12 | Table with test IDs and failure counts |
| Routing mismatches | 13 | Pie chart of misrouted skills |
| Test results over time | 15 | Time series of pass/fail |
| Recent test traces | 17 | Tempo trace list |
| Duration distribution | 19 | Histogram |
| Slowest tests | 20 | Bar gauge |
| Tool use accuracy | 22-25 | Gauge and breakdowns |
| Response analysis | 26 | Trace viewer |

#### Gaps Identified ❌

| Gap | Description | Impact | Priority |
|-----|-------------|--------|----------|
| **Flaky Test Detection** | No identification of tests that pass/fail intermittently | Wasted debug time chasing non-deterministic issues | HIGH |
| **Test Stability Score** | No historical pass rate per individual test | Hard to prioritize which tests to fix first | HIGH |
| **Disambiguation Validation** | No specific panel for `expected_skill=null` tests | Core test category behavior obscured | HIGH |
| **Input Pattern Analysis** | No clustering of similar failed inputs | Root cause patterns remain hidden | MEDIUM |
| **Response Content Search** | Can't search/filter by response keywords | Debugging is slow and manual | MEDIUM |
| **Expected vs Actual Diff** | No visual comparison when routing fails | Manual correlation between expected and actual needed | MEDIUM |
| **Test Case Metadata** | No link to test definition or expected clarification question | Context missing for debugging | LOW |

#### Recommended Additions
```yaml
New Panels:
  - name: "Flaky Tests"
    type: table
    description: "Tests with 30-70% pass rate over 7 days"
    query: |
      Tests where: 0.3 < pass_rate < 0.7
      Columns: Test ID, Pass Rate, Run Count, Last Failure

  - name: "Test Stability Trend"
    type: timeseries
    description: "Per-test mini sparklines showing stability"

  - name: "Disambiguation Tests Section"
    type: row
    panels:
      - "Disambiguation Pass Rate" (gauge)
      - "Clarification Rate" (expected vs actual clarifications)
      - "Disambiguation Options Validation" (table)

  - name: "Failed Input Patterns"
    type: wordcloud OR clustering
    description: "Common words/phrases in failed test inputs"

  - name: "Response Diff Viewer"
    type: custom
    description: "Side-by-side expected vs actual skill comparison"
```

---

### 3. LLM SKILLS ENGINEERS (A/B Testing)

#### Currently Implemented ✅
| Feature | Panel ID | Description |
|---------|----------|-------------|
| Pass rate by model | 2 | Bar gauge |
| Avg duration by model | 3 | Bar gauge |
| Model performance over time | 4 | Time series |
| Pass rate by skill version | 6 | Bar gauge |
| Tests run by skill version | 7 | Pie chart |
| Pass rate by branch | 9 | Bar gauge |
| Pass rate by commit | 10 | Bar gauge |
| Routing accuracy by target skill | 12 | Table |
| Misroute confusion matrix | 13 | Table (expected vs actual) |
| Category pass rate by model | 15 | Grouped bar chart |
| Regression detection | 17 | Time series with thresholds |

#### Gaps Identified ❌

| Gap | Description | Impact | Priority |
|-----|-------------|--------|----------|
| **SKILL.md Change Correlation** | No link between file changes and accuracy delta | Can't attribute improvements to specific changes | CRITICAL |
| **A/B Experiment Isolation** | Can't define cohorts or run controlled experiments | No rigorous statistical comparison | HIGH |
| **Prompt Effectiveness Analysis** | No analysis of which SKILL.md sections influence routing | Blind optimization without insights | HIGH |
| **Semantic Similarity Clustering** | No grouping of similar test inputs to find patterns | Pattern discovery limited | MEDIUM |
| **Skill Description Diff Viewer** | No side-by-side SKILL.md comparison between versions | Manual git inspection required | MEDIUM |
| **Confidence Score Tracking** | Routing certainty not captured in metrics | Can't optimize for high-confidence routing | MEDIUM |
| **Token Efficiency by Skill** | Which skills cost more to route correctly | Cost optimization blocked | LOW |

#### Recommended Additions
```yaml
New Panels:
  - name: "Change Impact Analysis"
    type: custom_panel
    description: |
      - Git diff of SKILL.md
      - Before/after accuracy comparison
      - Affected test cases list
      - Statistical significance indicator

  - name: "Skill Routing Patterns"
    type: table
    description: |
      - Which keywords route to which skills
      - Keyword frequency in failed vs passed tests
      - Routing decision factors

  - name: "Confidence Distribution"
    type: histogram
    description: |
      - Track routing certainty when available
      - Correlate low confidence with failures
      - Flag tests needing disambiguation

New Dashboard:
  - name: "Experiment Dashboard"
    description: |
      - Define experiment cohorts (control/treatment)
      - Statistical significance calculation (chi-square, t-test)
      - Control vs treatment comparison
      - Experiment lifecycle management
```

---

### 4. SITE RELIABILITY ENGINEERS (SRE)

#### Currently Implemented ✅
| Feature | Panel ID | Description |
|---------|----------|-------------|
| Total cost (24h) | 2 | Stat panel |
| Avg cost per test | 3 | Stat panel |
| Tests run (24h) | 4 | Stat panel |
| Cost efficiency | 5 | Cost per passed test |
| Cost over time | 6 | Time series |
| Cost by model | 7 | Pie chart |
| Latency percentiles | 9 | p50, p90, p95, p99 time series |
| Duration heatmap | 10 | Heatmap |
| Test throughput | 11 | Tests per minute |
| Duration by model | 12 | Bar gauge |
| Error rate | 14 | Time series with thresholds |
| Failures by error type | 15 | Pie chart |
| OTLP collector health | 17-19 | Spans, metrics, errors |
| Session summary table | 21 | Table by version/model/commit |

#### Gaps Identified ❌

| Gap | Description | Impact | Priority |
|-----|-------------|--------|----------|
| **API Rate Limit Tracking** | No 429 retry count visibility | Capacity issues hidden until failures | HIGH |
| **Claude API Health** | No external API latency/error tracking | Can't distinguish test issues from API issues | HIGH |
| **Parallel Worker Utilization** | No worker efficiency metrics | Resource optimization blocked | HIGH |
| **Queue Depth / Backpressure** | No waiting test visibility | Bottleneck detection difficult | MEDIUM |
| **Cost Anomaly Detection** | No auto-alerting on cost spikes | Surprise bills possible | MEDIUM |
| **Token Usage Trends** | No input/output token breakdown | Cost attribution incomplete | MEDIUM |
| **Session Duration vs Test Count** | Efficiency correlation missing | Resource planning difficult | LOW |
| **Collector Memory/CPU** | No OTel collector resource usage | Infrastructure health blind spot | LOW |

#### Recommended Additions
```yaml
New Panels:
  - name: "API Health"
    type: row
    panels:
      - "Claude API Latency" (from retry timing)
      - "429/5xx Error Rates"
      - "Retry Count Distribution"

  - name: "Worker Efficiency"
    type: row
    panels:
      - "Tests per Worker" (distribution)
      - "Worker Idle Time"
      - "Parallel Utilization %" (actual vs theoretical)

  - name: "Token Economics"
    type: row
    panels:
      - "Input vs Output Tokens" (stacked area)
      - "Tokens per Test Category"
      - "Token Cost Breakdown by Model"

New Alerting Rules:
  - "Daily cost exceeds $X"
  - "Per-test cost spike > 2x average"
  - "Error rate exceeds SLO (default 20%)"
  - "API 429 rate exceeds threshold"
  - "Worker utilization below 50%"
```

---

## Priority Matrix

| Priority | Executive | QA Engineer | Skills Engineer | SRE |
|----------|-----------|-------------|-----------------|-----|
| **CRITICAL** | - | - | SKILL.md change correlation | - |
| **HIGH** | ROI metrics, WoW trends | Flaky detection, Stability score, Disambiguation panel | A/B isolation, Prompt effectiveness | Rate limit tracking, API health, Worker utilization |
| **MEDIUM** | Release comparison, Budget burn | Input patterns, Response search, Diff viewer | Semantic similarity, Skill diff, Confidence | Queue depth, Cost anomaly, Token usage |
| **LOW** | Coverage heatmap, AI summary | Test metadata | Token efficiency | Session duration, Collector resources |

---

## Recommendations

### Immediate Actions (Week 1)
1. Address CRITICAL gap: Implement SKILL.md change correlation for Skills Engineers
2. Add flaky test detection for QA (high-value, low-effort)
3. Extend OTel instrumentation to capture retry counts and API latency

### Short-Term (Weeks 2-4)
1. Implement HIGH priority items across all dashboards
2. Add Grafana alerting rules for SRE
3. Create disambiguation validation panel for QA

### Medium-Term (Weeks 5-8)
1. Build experiment dashboard for A/B testing
2. Implement MEDIUM priority items
3. Add executive trend delta indicators

### Long-Term (Weeks 9-12)
1. LOW priority items
2. Custom visualizations (word cloud, diff viewer)
3. AI-generated executive summaries

---

## Appendix

### A. Dashboard File Locations
```
skills/jira-assistant/tests/dashboards/
├── executive-summary.json
├── qa-test-engineer.json
├── skills-engineer-ab.json
└── sre-operations.json
```

### B. OTel Configuration
```
skills/jira-assistant/tests/
├── otel_metrics.py          # Instrumentation
├── conftest.py              # pytest hooks for OTel
└── otel-collector-config.yaml  # Collector configuration
```

### C. Related Documentation
- `FAST_ITERATION.md` - Test runner documentation
- `CLAUDE.md` - Project overview
- `routing_golden.yaml` - Golden test set definitions
