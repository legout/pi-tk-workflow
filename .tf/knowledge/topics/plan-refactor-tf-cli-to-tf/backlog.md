# Backlog: plan-refactor-tf-cli-to-tf

| ID | Title | Score | Est. Hours | Depends On | Links |
|----|-------|-------|------------|------------|-------|
| pt-mu0s | Define tf_cli shim + deprecation strategy (timeline + warning policy) | 7 | 1-2 | - | pt-hpme |
| pt-hpme | Implement tf_cli compatibility shims (re-export) + optional deprecation warnings | 4 | 1-2 | pt-62g6,pt-ce2e | pt-mu0s,pt-62g6 |
| pt-62g6 | Wire packaging/entrypoints so tf console script uses tf namespace | 1 | 1-2 | pt-mu0s,pt-k2rk | pt-hpme,pt-tupn |
| pt-tupn | Move CLI dispatcher + core modules from tf_cli to tf | 1 | 1-2 | pt-62g6,pt-ce2e | pt-62g6,pt-m06z |
| pt-m06z | Update tests to use tf namespace + add regression test for tf_cli shim | 1 | 1-2 | pt-hpme,pt-tupn | pt-tupn,pt-k2rk |
| pt-k2rk | Inventory current packaging + entrypoints for tf_cli | 0 | 1-2 | - | pt-m06z,pt-ce2e |
| pt-ce2e | Introduce tf package skeleton + module entrypoint (python -m tf) | 0 | 1-2 | pt-mu0s,pt-k2rk | pt-k2rk,pt-7li0 |
| pt-7li0 | Update docs: canonical namespace is tf (migration notes + deprecation timeline) | 0 | 1-2 | pt-hpme,pt-tupn | pt-ce2e |