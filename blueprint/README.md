# Blueprint prototype

A three-lane design view (pipeline, tables, UI) with one section per node, a canvas board over the
same sections, and a wireframe per screen. Imported from the first prototype on 2026-11-10 as the
baseline for a mock build. The goal of the mock build is to get the skills and the tracking right,
not to deploy anything.

| Path | What it is |
| --- | --- |
| `AWS_Batch_Pipeline_Blueprint.md` | The source: a map plus one section per node |
| `AWS_Batch_Pipeline_Blueprint.canvas` | Board view; table and pipeline cards embed sections of the note |
| `wireframes/` | One lo-fi SVG per screen; callout numbers match that screen's Elements table |
| `tools/` | Prototype scripts: `gen_wf.py` (wireframes), `gen_canvas.py` (canvas), `lint_note.py` (checks) |

Run the checks from the repo root:

```bash
python3 blueprint/tools/lint_note.py blueprint/AWS_Batch_Pipeline_Blueprint.md . blueprint/wireframes
```

## Known gaps in this baseline

- The note still links to 13 knowledge-base notes that do not exist in this repo, so the lint
  reports them.
- The worked example (positions, holdings, breaks) is not connected to the models in this project.
- The scripts were written for a one-off prototype: arguments are positional and paths are assumed.
