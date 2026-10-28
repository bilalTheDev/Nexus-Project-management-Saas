# Reports

All chart data is aggregated on the server. The frontend never totals raw issue lists.

| Chart | Endpoint | Query notes |
| --- | --- | --- |
| Burndown | `GET .../sprints/{id}/burndown/` | Remaining points/day from start snapshot vs ideal line; dates in workspace TZ |
| Velocity | `GET .../reports/velocity/` | Last 6 completed sprints: committed vs completed points |
| Sprint report | `GET .../sprints/{id}/report/` | Completed / not completed / added / removed + stacked counts |
| CFD | `GET .../reports/cfd/?from=&to=` | Count per status per day (stacked areas) |
| Created vs resolved | `GET .../reports/created-vs-resolved/` | Weekly TruncWeek buckets |
| Breakdown | `GET .../reports/breakdown/?by=` | `priority` \| `assignee` \| `type` |
| Summary | `GET .../reports/summary/` | Open, done, overdue, due this week |

UI rules: title, one-line description, empty/loading/error+retry, table toggle, token colours.
