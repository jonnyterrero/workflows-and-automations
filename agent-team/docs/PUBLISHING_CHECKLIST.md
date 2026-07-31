# Publishing Checklist

Current live state is tracked in [`DEPLOYMENT_STATUS.md`](./DEPLOYMENT_STATUS.md).

## Private Claude workspace release
- [x] Review `AUDIT_REPORT.md`.
- [x] Run `python scripts/build_skills.py`.
- [x] Verify all SHA-256 checksums. — written to `dist/skills/SHA256SUMS.txt`
- [x] Upload all 15 focused skills individually. — `upload_skills.py --execute`
- [ ] Run positive, boundary, and freshness evals for every skill. — `run_evals.py`; priority four done, remaining specialists pending
- [x] Create Managed Agents with least-privilege tools. — 14 specialists
- [x] Keep Bash/write/edit as confirmation-required until proven safe. — `bash` is `always_ask`; verified live, it parks the session
- [ ] Attach only required MCP servers and vault credentials. — none attached to Managed Agents yet; Public connector is Claude Code only
- [x] Create coordinator after specialist tests pass. — `--phase specialists` → eval gate → `--phase coordinator`
- [ ] Pin accepted skill and agent versions. — `pin_versions.py --execute`
- [ ] Configure cost limits, logging, and session retention.

## Broker/exchange connector gate
Before any execution scope is enabled:
- [x] Connector runs read-only first. — order-mutating Public tools denied in `.claude/settings.json`
- [x] `trading-agent` `adversarial-1` passes (no carried-over session enable phrase).
- [ ] `trading-agent` `realistic-4` passes (refuses `execute_supervised` when a risk limit is unset).
- [ ] Max position size, max daily loss, and max open risk are all configured.
- [ ] Deny list re-checked against the connector's current tool list — it is explicit, not wildcarded, so a newly added order tool would not be blocked.

## Public distribution release
- [ ] Choose and add a license.
- [ ] Remove or document all personal/operator-specific context.
- [ ] Add changelog, support contact, vulnerability-reporting process, and privacy statement.
- [ ] Publish source and checksums in a versioned repository.
- [ ] Document required tools, network access, and data handling.
- [ ] Disclose that legal, tax, financial, trading, and health outputs are informational and require qualified human review.
- [ ] Do not market a Skill ZIP as a standalone autonomous agent; publish the Managed Agent configuration separately.
