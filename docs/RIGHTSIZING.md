# Peak-aware rightsizing: design (2026-10-18)
Implements DEV-PRINCIPLES R10 (use peaks, not averages) from the owner's tip of 2026-10-18. Statements marked VERIFIED were read on Microsoft Learn on 2026-10-18; thresholds marked PROPOSAL are my judgement and are configurable.

## What Azure itself does (VERIFIED)
Advisor VM/VMSS cost recommendations (https://learn.microsoft.com/azure/advisor/advisor-cost-recommendations):
- Resize look-back is 7 days by default, configurable to 7, 14, 21, 30, 60 or 90 days; recommendations can take up to 48 hours to update.
- Metrics are sampled every 30 s, aggregated to 1 min, then to 30 min "taking the max of average values". So a spike shorter than about 30 minutes is averaged away before Advisor sees it.
- Resize targets: user-facing workloads need P95 CPU and outbound network at or below 40% and P99 memory at or below 60% on the recommended SKU; non user-facing 80% and 80%.
- Shutdown: P95 of maximum CPU summed over cores below 3%, P100 of average CPU over the last 3 days at or below 2%, outbound network below 2% over 7 days. Memory is not considered.
- Advisor decides user-facing versus not by its own model; the documentation does not say how (DON'T KNOW).
Azure Migrate sizing (https://learn.microsoft.com/azure/migrate/target-right-sizing): percentile of the performance history (P95 default, P99 to keep outliers) multiplied by a comfort factor.
Azure Monitor metrics (https://learn.microsoft.com/azure/azure-monitor/metrics/data-platform-metrics): platform metrics are kept 93 days; the portal shows at most 30 days per chart (whether the REST API has the same limit: UNVERIFIED, so queries are chunked to 30 days). Stopped VMs emit no metrics. VM platform metrics include Available Memory Percentage and Available Memory Bytes (default aggregation Average, one-minute grain; which other aggregations are accepted for them: UNVERIFIED). B-series VMs have CPU Credits Consumed/Remaining.

## Why averages are not enough
A VM at 8% average CPU with a nightly job that hits 95% for 20 minutes is not an idle VM. Advisor's 30-minute max-of-averages smooths such a job to roughly a third of its real height (arithmetic, not a measurement). Peak-aware means we judge the busy moments the VM must survive, with the window and statistic shown so the reader can disagree.

## Our rule (PROPOSAL)
Inputs per VM: hourly points, each with the maximum CPU in that hour and the average CPU, for a window of 30 days where retention allows (B-series: also credits). Hourly maximum is requested with aggregation Maximum on the one-minute metric, so it keeps spikes.
Computed: coverage (points present / points expected while the VM was running), window length, P99 and maximum of the hourly maxima, P95 of the hourly averages.
Projection: to move from N to M vCPUs, utilisation scales by N/M (assumes the same CPU family; different families need benchmarks: DON'T KNOW how to scale across them, so the first version only compares within one family).
Verdicts: `candidate` only if window >= 14 days, coverage >= 90%, and projected P99 of hourly maxima <= limit (default 60%, my judgement, lower than Microsoft's 80% for non user-facing). `keep` if a limit is exceeded. `insufficient_data` otherwise. Confidence: high is never assigned before live validation (QUALITY rule); `medium` needs window >= 30 days; thin data caps at `low`.
Memory: only judged if a memory series exists; otherwise the finding says memory was not assessed, because the platform metric may be absent or guest-level (UNVERIFIED which VMs emit it).
Burstable (B-series): if CPU Credits Remaining reached zero in the window, never `candidate` (the VM is already starved).
Business cycles: a 30-day window covers one month-end; if the owner or customer says there is a quarterly or yearly peak, the report must say a longer history is needed and metrics only reach back 93 days.

## Data access
GET `https://management.azure.com/{vmId}/providers/Microsoft.Insights/metrics?...` is a GET on an allowed host, so no allowlist change. One call per VM per metric per 30-day chunk; throttling limits for these reads are UNVERIFIED, so candidates are pre-filtered (Advisor flagged, or large sizes) and calls counted in the manifest. The batch metrics API uses another host and would need a new decision record (not drafted).
Price and savings need the retail price list (another host, prices.azure.com, UNVERIFIED allowlisting need) and cost data (ADR 0006). Until then findings carry no savings figure; actual versus list pricing stays demarcated when they arrive.

## Tests (offline)
Pure function with synthetic series: steady low load -> candidate; low average with a short 95% spike -> keep; fewer than 14 days or low coverage -> insufficient_data; scaling and ordering invariants; zero-credit B-series never candidate. Implemented in src/fcat/rightsize.py and tests/test_rightsize.py (2026-10-18). The collector and the check that calls it are NOT built.

## Sources
- https://learn.microsoft.com/azure/advisor/advisor-cost-recommendations (read 2026-10-18)
- https://learn.microsoft.com/azure/migrate/target-right-sizing (read 2026-10-18)
- https://learn.microsoft.com/azure/azure-monitor/metrics/data-platform-metrics (read 2026-10-18)
- https://learn.microsoft.com/azure/virtual-machines/monitor-vm-reference (read 2026-10-18)
