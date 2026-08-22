# Dataset Profiling Summary: `case_management_raw.csv`

**Generated:** 2026-08-22T23:35:03.834868

## 1. High-Level Dataset Dimensions

| Metric | Value |
| :--- | :--- |
| **Total Rows** | 120 |
| **Total Columns** | 12 |
| **Total Memory Usage** | 83.49 KB |
| **Exact Duplicate Rows** | 0 (0.0%) |

## 2. Column-Level Attribute Summary

| Column Name | Inferred Type | Missing Count | Missing % | Unique Values | Cardinality Ratio | Memory (KB) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `case_id` | text | 1 | 0.83% | 119 | 0.9917 | 6.68 KB |
| `client_name` | categorical | 0 | 0.0% | 47 | 0.3917 | 7.6 KB |
| `category` | categorical | 1 | 0.83% | 15 | 0.1250 | 7.35 KB |
| `priority` | categorical | 0 | 0.0% | 6 | 0.0500 | 6.42 KB |
| `intake_date` | datetime | 0 | 0.0% | 114 | 0.9500 | 7.04 KB |
| `closure_date` | datetime | 2 | 1.67% | 109 | 0.9083 | 7.02 KB |
| `triage_date` | datetime | 43 | 35.83% | 74 | 0.6167 | 6.62 KB |
| `triaged` | boolean | 0 | 0.0% | 5 | 0.0417 | 6.18 KB |
| `contact_count` | numeric | 0 | 0.0% | 14 | 0.1167 | 6.0 KB |
| `assigned_agent` | categorical | 0 | 0.0% | 5 | 0.0417 | 7.19 KB |
| `status` | categorical | 0 | 0.0% | 3 | 0.0250 | 6.58 KB |
| `resolution_notes` | text | 0 | 0.0% | 117 | 0.9750 | 10.23 KB |

## 3. Value Distributions & Top Frequencies

### Column: `case_id` (text)
| Value | Count |
| :--- | :--- |
| `CS-1001` | 1 |
| `CS-1002` | 1 |
| `CS-1003` | 1 |
| `CS-1004` | 1 |
| `CS-1005` | 1 |

### Column: `client_name` (categorical)
| Value | Count |
| :--- | :--- |
| `Apex Solutions` | 5 |
| `BlueStar Logistics` | 4 |
| `Cascade Media` | 4 |
| `Epsilon Health` | 4 |
| `Delta Dynamics` | 4 |

### Column: `category` (categorical)
| Value | Count |
| :--- | :--- |
| `Technical Support` | 38 |
| `Billing` | 21 |
| `Hardware` | 20 |
| `General Inquiry` | 14 |
| `Security Alert` | 11 |

### Column: `priority` (categorical)
| Value | Count |
| :--- | :--- |
| `High` | 43 |
| `Medium` | 32 |
| `Low` | 32 |
| `Critical` | 11 |
| `HIGH` | 1 |

### Column: `intake_date` (datetime)
| Value | Count |
| :--- | :--- |
| `2024-01-05` | 2 |
| `01/08/2024` | 2 |
| `2024-03-10` | 2 |
| `2024-04-10` | 2 |
| `2025-02-20` | 2 |

### Column: `closure_date` (datetime)
| Value | Count |
| :--- | :--- |
| `2024-04-15` | 3 |
| `01/14/2024` | 2 |
| `2024-02-15` | 2 |
| `2024-05-08` | 2 |
| `2024-01-08` | 2 |

### Column: `triage_date` (datetime)
| Value | Count |
| :--- | :--- |
| `2024-01-05` | 2 |
| `01/08/2024` | 2 |
| `2024-04-10` | 2 |
| `2024-01-15` | 1 |
| `2024-01-26` | 1 |

### Column: `triaged` (boolean)
| Value | Count |
| :--- | :--- |
| `Yes` | 73 |
| `No` | 43 |
| `Y` | 2 |
| `1` | 1 |
| `TRUE` | 1 |

### Column: `contact_count` (numeric)
| Value | Count |
| :--- | :--- |
| `3` | 21 |
| `2` | 20 |
| `4` | 17 |
| `5` | 14 |
| `6` | 14 |

### Column: `assigned_agent` (categorical)
| Value | Count |
| :--- | :--- |
| `Agent_Smith` | 31 |
| `Agent_Johnson` | 24 |
| `Agent_Taylor` | 23 |
| `Agent_Lee` | 22 |
| `Agent_Davis` | 20 |

### Column: `status` (categorical)
| Value | Count |
| :--- | :--- |
| `Closed` | 117 |
| `Open` | 2 |
| `UNKNOWN_STATUS` | 1 |

### Column: `resolution_notes` (text)
| Value | Count |
| :--- | :--- |
| `Resolved server connectivity error.` | 2 |
| `Invoice reconciliation completed.` | 2 |
| `Resolved database lock timeout.` | 2 |
| `Configured VPN client credentials.` | 1 |
| `Replaced faulty display panel.` | 1 |
