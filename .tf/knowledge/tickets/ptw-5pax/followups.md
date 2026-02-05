# Follow-ups: ptw-5pax

## Created Follow-up Tickets

### From Warnings
1. **ptw-g8z8** - Add error handling for VERSION file read errors
   - get_version_file_version() silently returns None on exceptions
   - Should warn when VERSION file exists but can't be read

2. **ptw-guj5** - Add version checking to legacy bash doctor
   - Legacy bash doctor doesn't have version checking
   - Feature gap between `tf doctor` and `tf new doctor`

### From Suggestions
3. **ptw-9ze6** - Add --dry-run flag to tf doctor
   - Preview fixes without making changes
   - Useful for CI pipelines

4. **ptw-u01e** - Extend version check to support git tags
   - Verify package.json version matches git tag
   - Release validation

5. **ptw-rd6r** - Extend version check for multi-language projects
   - Support pyproject.toml, Cargo.toml, etc.
   - Cross-manifest version consistency

## Summary
- 2 tickets from Warnings
- 3 tickets from Suggestions
- All tagged with: tf, enhancement/feature, ptw-5pax-followup
