Run batch processing using HTCondor
====================================

Construct a job specification file `config.yaml`:

```yaml
cat > config.yaml << EOF

data:
  repo:     "/datasets/des_sn/repo_Y3/"
  template: "/datasets/des_sn/repo_Y3/templates/"
  db:       "/datasets/des_sn/repo_Y3/registry.sqlite3"
  calib:    "/datasets/des_sn/calib/"
  filter:   "g"
job:
  max_jobs: 4

EOF
```

Launch the jobs:
```bash
bash launch_batch_processing.sh [config.yaml]
```
