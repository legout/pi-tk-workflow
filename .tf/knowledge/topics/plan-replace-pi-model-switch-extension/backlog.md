# Backlog: plan-replace-pi-model-switch-extension

| ID | Title | Score | Est. Hours | Depends On | Links |
|----|-------|-------|------------|------------|-------|
| pt-o5ca | Decide flag strategy for chain-prompts TF workflow | 0 | 1-2 | - | pt-74hd |
| pt-qmhr | Design retry/escalation handling for chained TF phases | 14 | 1-2 | pt-o5ca | pt-pcd9 |
| pt-74hd | Add phase prompts for TF workflow (research/implement/review/fix/close) | 3 | 1-2 | pt-qmhr | pt-rn2w,pt-o5ca |
| pt-mdl0 | Implement /tf as a /chain-prompts wrapper (keep /tf contract) | 8 | 1-2 | pt-74hd | pt-pcd9,pt-rn2w |
| pt-pcd9 | Update docs/setup to drop pi-model-switch as required extension | 10 | 1-2 | pt-mdl0 | pt-qmhr,pt-mdl0 |
| pt-rn2w | Add smoke test for /tf chain-prompts workflow (interactive + pi -p) | 4 | 1-2 | pt-pcd9 | pt-mdl0,pt-74hd |
