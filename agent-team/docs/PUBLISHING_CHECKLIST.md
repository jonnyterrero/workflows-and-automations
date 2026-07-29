# Publishing Checklist

## Private Claude workspace release
- [ ] Review `AUDIT_REPORT.md`.
- [ ] Run `python scripts/build_skills.py`.
- [ ] Verify all SHA-256 checksums.
- [ ] Upload all 13 focused skills individually.
- [ ] Run positive, boundary, and freshness evals for every skill.
- [ ] Create Managed Agents with least-privilege tools.
- [ ] Keep Bash/write/edit as confirmation-required until proven safe.
- [ ] Attach only required MCP servers and vault credentials.
- [ ] Create coordinator after specialist tests pass.
- [ ] Pin accepted skill and agent versions.
- [ ] Configure cost limits, logging, and session retention.

## Public distribution release
- [ ] Choose and add a license.
- [ ] Remove or document all personal/operator-specific context.
- [ ] Add changelog, support contact, vulnerability-reporting process, and privacy statement.
- [ ] Publish source and checksums in a versioned repository.
- [ ] Document required tools, network access, and data handling.
- [ ] Disclose that legal, tax, financial, trading, and health outputs are informational and require qualified human review.
- [ ] Do not market a Skill ZIP as a standalone autonomous agent; publish the Managed Agent configuration separately.
