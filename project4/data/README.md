# Data Directory

The benchmark is generated deterministically by
`tools/generate_incident_dataset.py` or notebook cell `P04-C03`.

Expected generated files:

```text
data/cache/project4_incidents.json
data/cache/project4_incidents.sha256
```

The JSON contains 24 simulated incidents across four services and six root-cause
archetypes. It includes public evidence plus hidden evaluation labels. Planners
receive only the public evidence view.

The initial benchmark and checksum are committed so every fresh clone starts from
the same corpus. Cell `P04-C03` reuses these files and regenerates them only when
one is missing. Final dataset counts and checksum are stored in the result summary.
