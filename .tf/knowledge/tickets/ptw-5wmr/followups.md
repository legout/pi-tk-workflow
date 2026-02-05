# Follow-ups: ptw-5wmr

## Created Tickets

### ptw-a6h2 - Add tests for tf doctor version check
**Tags**: tf, testing, ptw-5wmr-followup

Add automated tests for the doctor module, specifically for the version consistency check functionality. Test cases should cover:
- Normal version matching
- VERSION file mismatch
- Empty VERSION file
- Missing version field in package.json
- Invalid version types in package.json

### ptw-ffbq - Add tf --version CLI flag to expose version
**Tags**: tf, feature, ptw-5wmr-followup

As mentioned in the seed vision "Expose version to users", add a `--version` CLI flag to the `tf` command itself. The current implementation only checks consistency but doesn't expose the version for user queries.

### ptw-1t5q - Consider version normalization for VERSION file
**Tags**: tf, enhancement, ptw-5wmr-followup

Consider adding version normalization (stripping leading 'v' prefix) to avoid false mismatches like VERSION="v1.0.0" vs package.json="1.0.0".

### ptw-5pax - Consider tf doctor --fix to auto-sync VERSION file
**Tags**: tf, feature, ptw-5wmr-followup

Consider adding a `--fix` flag to `tf doctor` that could automatically sync the VERSION file to match package.json when a mismatch is detected.

## Summary
Created 4 follow-up tickets from review warnings and suggestions.
