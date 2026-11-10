# AWS Batch Pipeline Blueprint

> **One-line:** A three-lane design view of the standard AWS batch pipeline: the steps that run, the tables they produce, and the screens that read them, with one section per node and a wireframe per screen.

- **Status**: prototype of the format, built 2026-11-10; the worked example is illustrative, not a production design
- **Companions**:
	- [[AWS_Batch_Pipeline_Blueprint.canvas]]: the same sections on a board with exact placement
	- [[AWS_Batch_Pipeline.canvas]]: the original service-level diagram this extends
- **Worked example**: daily positions from an accounting system (ABOR) and a custodian, reconciled and served to three screens

## Map

```mermaid
swimlane-beta LR
  subgraph ui [UI]
    run_monitor["#Run monitor"]
    holdings_grid["#Holdings grid"]
    position_break_report["#Break report"]
  end
  subgraph tables [Tables]
    ops_pipeline_runs[("#ops_pipeline_runs")]
    raw_positions[("#raw_positions")]
    stg_positions[("#stg_positions")]
    fct_holdings[("#fct_holdings")]
    fct_position_breaks[("#fct_position_breaks")]
  end
  subgraph pipeline [Pipeline]
    orchestrate["#Orchestrate"]
    sources["#Sources"]
    ingest["#Ingest and validate"]
    stage["#Stage positions"]
    build["#Build marts"]
  end
  orchestrate --> ops_pipeline_runs
  ops_pipeline_runs --> run_monitor
  sources --> ingest
  ingest --> raw_positions
  raw_positions --> stage
  stage --> stg_positions
  stg_positions --> build
  build --> fct_holdings
  build --> fct_position_breaks
  fct_holdings --> holdings_grid
  fct_position_breaks --> position_break_report
  class run_monitor,holdings_grid,position_break_report,ops_pipeline_runs,raw_positions,stg_positions,fct_holdings,fct_position_breaks,orchestrate,sources,ingest,stage,build internal-link
```

- **UI**: [[#Run monitor]], [[#Holdings grid]], [[#Break report]]
- **Tables**: [[#ops_pipeline_runs]], [[#raw_positions]], [[#stg_positions]], [[#fct_holdings]], [[#fct_position_breaks]]
- **Pipeline**: [[#Orchestrate]], [[#Sources]], [[#Ingest and validate]], [[#Stage positions]], [[#Build marts]]

## How to read this

- **Lanes**: Pipeline at the bottom does the work, Tables in the middle hold the results, UI on top shows them
- **Edges**: step to table means the step writes it; table to step or screen means it is read
- **Names**: every node label is `#` plus a heading in this note, so the diagram, the links, and an instruction to an agent all use the same name
- **Links**: in Obsidian each node opens its section, the same sections the canvas cards show; the `internal-link` class does this, and it takes the node label as the link target, which is why the labels start with `#`
- **Map grain**: one node per stage in each lane, which keeps the edges untangled in Mermaid proper (it draws a lane as a single row); where a stage holds several tables ([[#raw_positions]]) the node is the group and its section lists the members
- **Screens**: each screen section embeds a wireframe; the numbered callouts match the rows of its Elements table, and the Bound to column names the table columns behind each element
- **Source of truth**: the sections, not the pictures; the map and the wireframes are views that get regenerated when a section changes

## UI

- Three read-only screens in one small app; each screen reads exactly one table, which keeps the map complete
- The path from table to screen is one API endpoint per screen over [[Redshift]], named in each section

### Run monitor

- **Purpose**: answer "did last night's run finish, and if not, where did it stop"
- **Reads**: [[#ops_pipeline_runs]] through `GET /runs`
- **Users**: the on-call data engineer first, operations second

![[AWS_Batch_Blueprint_wf_run_monitor.svg]]

| # | Element | Type | Bound to | Notes |
| --- | --- | --- | --- | --- |
| 1 | Last run banner | Status banner | `run_id`, `business_date`, `status`, `started_at`, `ended_at` | Latest `run_id`; shows the worst status across its steps |
| 2 | Step timeline | Stepper | `step`, `status`, `started_at`, `ended_at`, `rows_out` | One chip per step of the latest run, in run order |
| 3 | Filters | Date range, select | `business_date`, `status` | Default is the last seven days |
| 4 | Run history | Data grid | `run_id`, `business_date`, `step`, `status`, `rows_in`, `rows_out`, `started_at`, `ended_at`, `error_message` | Duration is `ended_at` minus `started_at`; newest first |

- **States**:
	- Running: the banner shows the current step and elapsed time, and the timeline marks the finished steps
	- Failed: the banner names the failed step and shows `error_message`
	- Empty: no runs in the range, offer to widen the range

### Holdings grid

- **Purpose**: answer "what do we hold, in which account, and what is it worth" for one business date
- **Reads**: [[#fct_holdings]] through `GET /holdings`
- **Users**: portfolio operations and anyone checking a position

![[AWS_Batch_Blueprint_wf_holdings_grid.svg]]

| # | Element | Type | Bound to | Notes |
| --- | --- | --- | --- | --- |
| 1 | Freshness badge | Text | `loaded_at`, `load_id` | Latest `loaded_at` for the chosen date |
| 2 | As-of date | Date picker | `business_date` | Defaults to the latest date with data |
| 3 | Account filter | Multi-select | `account_id` | |
| 4 | Asset class filter | Select | `asset_class` | |
| 5 | Summary tiles | Stat tiles | `market_value_usd`, `security_id`, `account_id` | Sum of market value, count of positions, count of distinct accounts, all after filters |
| 6 | Holdings table | Data grid | `account_id`, `security_id`, `security_name`, `asset_class`, `quantity`, `price`, `market_value_usd` | Sorted by account, then market value descending; search matches `security_name` or `security_id` |
| 7 | Export CSV | Button | Same columns as element 6 | Exports the filtered set, not only the page |

- **States**:
	- Empty: no rows for the date, say so and link to the latest date that has data
	- Stale: `loaded_at` is more than one business day behind the date, and the badge becomes a warning
	- Error: the query failed, keep the filters and offer a retry

### Break report

- **Purpose**: answer "where does the accounting book disagree with the custodian, and for how long"
- **Reads**: [[#fct_position_breaks]] through `GET /breaks`
- **Users**: the reconciliation analyst working the break list

![[AWS_Batch_Blueprint_wf_break_report.svg]]

| # | Element | Type | Bound to | Notes |
| --- | --- | --- | --- | --- |
| 1 | As-of date | Date picker | `business_date` | Defaults to the latest date with data |
| 2 | Break type filter | Select | `break_type` | The minimum age input beside it filters on `age_days` |
| 3 | Summary tiles | Stat tiles | `break_type` | Count of breaks, in total and by type |
| 4 | Breaks table | Data grid | `account_id`, `security_id`, `abor_quantity`, `custodian_quantity`, `quantity_diff`, `break_type`, `age_days` | Oldest first; a blank quantity means that side has no row |
| 5 | Break detail | Side panel | `security_name`, `abor_quantity`, `custodian_quantity`, `quantity_diff`, `break_type`, `first_seen_date`, `age_days` | Opens for the selected row |
| 6 | Lineage | Text | `abor_load_id`, `custodian_load_id`, `custodian_source_file` | Enough to find the raw rows in [[#raw_positions]] without a second query |

- **States**:
	- Empty: no breaks for the date, show an explicit "no breaks" result, not a blank table
	- Error: the query failed, keep the filters and offer a retry

## Tables

- Layers follow [[Medallion_Architecture]]: raw is as delivered, stg is clean and conformed, fct is modeled for the screens
- Every data table carries `load_id`, the `run_id` of the run that wrote the row, so any row traces back to its run and file

### ops_pipeline_runs

- **Layer**: operational log on [[Redshift]]
- **Grain**: one row per `run_id` and `step`
- **Written by**: [[#Orchestrate]]
- **Read by**: [[#Run monitor]]
- **Load**: inserted at step start with status `running`, updated at step end; never deleted

| Column | Type | Notes |
| --- | --- | --- |
| `run_id` | varchar | Business date plus attempt number, for example `20261109-01` |
| `business_date` | date | The date being loaded, not the wall-clock date of the run |
| `step` | varchar | `ingest_and_validate`, `stage_positions`, `build_marts` |
| `status` | varchar | `running`, `succeeded`, `failed` |
| `started_at` | timestamp | |
| `ended_at` | timestamp | Null while running |
| `rows_in` | bigint | Rows read by the step |
| `rows_out` | bigint | Rows written by the step |
| `error_message` | varchar | Null unless failed |

### raw_positions

- **Layer**: bronze, Parquet on [[S3]], registered in the [[Glue]] Data Catalog, queryable from [[Athena]]
- **Members**: [[#raw_custodian_positions]] and [[#raw_abor_positions]], one table per source
- **Written by**: [[#Ingest and validate]]
- **Read by**: [[#Stage positions]]
- **Rule**: immutable and as delivered; every source column lands as a string, partitioned by `business_date` and `load_id`, so a rerun adds a partition and never edits one

#### raw_custodian_positions

- **Grain**: one row per line of a custodian position file

| Column | Type | Notes |
| --- | --- | --- |
| `custodian_account` | string | The custodian's account number, mapped to `account_id` in staging |
| `isin` | string | Mapped to the internal `security_id` in staging |
| `quantity` | string | As delivered, including any formatting |
| `price` | string | |
| `position_date` | string | |
| `source_file` | string | Object key of the file |
| `business_date` | string | Partition |
| `load_id` | string | Partition |
| `loaded_at` | timestamp | |

#### raw_abor_positions

- **Grain**: one row per position in the accounting extract

| Column | Type | Notes |
| --- | --- | --- |
| `portfolio_code` | string | Mapped to `account_id` in staging |
| `security_id` | string | Internal id, already conformed |
| `security_name` | string | |
| `asset_class` | string | |
| `quantity` | string | |
| `price` | string | |
| `market_value_usd` | string | |
| `position_date` | string | |
| `business_date` | string | Partition |
| `load_id` | string | Partition |
| `loaded_at` | timestamp | |

### stg_positions

- **Layer**: silver, [[dbt]] model on Redshift
- **Grain**: one row per `source_system`, `business_date`, `account_id`, `security_id`
- **Written by**: [[#Stage positions]]
- **Read by**: [[#Build marts]]
- **Load**: incremental by `business_date`; the day being loaded is deleted and reinserted

| Column | Type | Notes |
| --- | --- | --- |
| `source_system` | varchar | `abor` or `custodian` |
| `business_date` | date | |
| `account_id` | varchar | Internal account id for both sources |
| `security_id` | varchar | Internal security id for both sources |
| `security_name` | varchar | From ABOR; null on custodian rows |
| `asset_class` | varchar | From ABOR; null on custodian rows |
| `quantity` | numeric(28,6) | |
| `price` | numeric(28,8) | |
| `market_value_usd` | numeric(28,2) | From ABOR; null on custodian rows |
| `source_file` | varchar | Custodian rows only |
| `load_id` | varchar | |
| `loaded_at` | timestamp | |

### fct_holdings

- **Layer**: gold, dbt incremental model on Redshift
- **Grain**: one row per `business_date`, `account_id`, `security_id`
- **Written by**: [[#Build marts]]
- **Read by**: [[#Holdings grid]]
- **Source rows**: the `abor` rows of [[#stg_positions]]; the accounting book is the record of holdings
- **Load**: delete and insert for the `business_date` being loaded ([[Idempotent_Ingestion]])

| Column | Type | Notes |
| --- | --- | --- |
| `business_date` | date | Incremental key and sort key |
| `account_id` | varchar | |
| `security_id` | varchar | |
| `security_name` | varchar | Carried from ABOR here; a fuller build joins a security master ([[Security_Master_IBOR_ABOR_Pipeline.canvas]]) |
| `asset_class` | varchar | |
| `quantity` | numeric(28,6) | |
| `price` | numeric(28,8) | |
| `market_value_usd` | numeric(28,2) | |
| `load_id` | varchar | |
| `loaded_at` | timestamp | |

### fct_position_breaks

- **Layer**: gold, dbt incremental model on Redshift
- **Grain**: one row per `business_date`, `account_id`, `security_id` where the two sources disagree
- **Written by**: [[#Build marts]]
- **Read by**: [[#Break report]]
- **Rule**: full outer join of the `abor` and `custodian` rows of [[#stg_positions]] on the grain; a row is kept when one side is missing or the quantities differ ([[Reconciliation]])
- **Load**: delete and insert for the `business_date` being loaded

| Column | Type | Notes |
| --- | --- | --- |
| `business_date` | date | |
| `account_id` | varchar | |
| `security_id` | varchar | |
| `security_name` | varchar | Null when the position exists only at the custodian |
| `abor_quantity` | numeric(28,6) | Null when missing in ABOR |
| `custodian_quantity` | numeric(28,6) | Null when missing at the custodian |
| `quantity_diff` | numeric(28,6) | ABOR minus custodian, with a missing side counted as zero |
| `break_type` | varchar | `quantity_mismatch`, `missing_at_custodian`, `missing_in_abor` |
| `first_seen_date` | date | First `business_date` of the current unbroken run of this break |
| `age_days` | integer | `business_date` minus `first_seen_date` |
| `abor_load_id` | varchar | |
| `custodian_load_id` | varchar | |
| `custodian_source_file` | varchar | |

## Pipeline

- The stages are the ones in [[AWS_Batch_Pipeline.canvas]]: sources, ingestion, bronze, silver, gold, with orchestration over all of them
- Every step is safe to rerun for a `business_date` ([[Idempotent_Ingestion]])

### Orchestrate

- **Service**: a [[Step_Functions]] state machine, started by EventBridge on a schedule
- **Order**: [[#Ingest and validate]], then [[#Stage positions]], then [[#Build marts]]; a failed step stops the run
- **Writes**: [[#ops_pipeline_runs]], one row per step
- **Retries**: transient errors retry with backoff inside the step; a contract failure does not retry, it fails the run
- **Backfill**: start the state machine with an explicit `business_date`; the attempt number in `run_id` increments

### Sources

- **Accounting system (ABOR)**: positions pulled over JDBC after the accounting close; the record of holdings
- **Custodian**: one CSV position file per custodian per business day, delivered to an S3 landing prefix; the independent record the book is reconciled against
- **Read by**: [[#Ingest and validate]]
- **Not owned here**: both are external, and the pipeline never writes back to them

### Ingest and validate

- **Service**: [[Lambda]] for the custodian files (small, one invocation per file), [[Glue]] for the ABOR extract (larger, over JDBC)
- **Reads**: [[#Sources]]
- **Writes**: [[#raw_positions]]
- **Contract**: unknown or missing columns fail the load and quarantine the file; nothing is partially loaded ([[Contract_Driven_Ingestion]])
- **Rerun**: each attempt writes its own `load_id` partition, so nothing is overwritten and staging picks the latest load

### Stage positions

- **Service**: [[dbt]] staging models on [[Redshift]], reading bronze through external tables on the Glue Data Catalog
- **Reads**: [[#raw_positions]]
- **Writes**: [[#stg_positions]]
- **Does**: casts types, renames to conformed names, maps custodian accounts and ISINs to internal ids, keeps the latest load per source and date
- **Tests**: unique and not null on the grain, accepted values on `source_system`, row count against the raw load

### Build marts

- **Service**: dbt incremental models on Redshift
- **Reads**: [[#stg_positions]]
- **Writes**: [[#fct_holdings]] and [[#fct_position_breaks]]
- **Tests**: unique on each grain, `market_value_usd` not null on holdings, exactly one `break_type` per break
- **Rerun**: delete and insert by `business_date`, so a rerun replaces the day in both tables

## Wireframes: how they link and how they are made

- **Where they live**: one SVG per screen in `diagrams/wireframes/`, named `<blueprint>_wf_<screen>.svg`
- **Three links per screen**:
	- The screen section embeds the image, so the picture sits with its spec
	- The callout numbers on the image match the `#` column of the Elements table, and Bound to names the columns, which ties a UI element to a table column
	- The canvas places the same SVG as an image card in the UI lane, directly above the table it reads
- **When they disagree**: the Elements table wins; fix the table, then regenerate the picture
- **Tools by stage**:

| Stage | Tool | Why | What sits in the screen section |
| --- | --- | --- | --- |
| Lo-fi wireframe | SVG written by the agent from the Elements table | No install, plain text, clean diffs, embeds in notes and on the canvas | The SVG |
| Hand sketching | Excalidraw plugin for Obsidian | Only when you want to draw or nudge by hand; needs the plugin | The Excalidraw drawing |
| Layout and interaction questions | Single-file HTML mock, captured with a headless browser | Real layout rules (grid, overflow, responsive) that an SVG only imitates | The screenshot, plus a link to the HTML |
| Built UI | Screenshot of the real component, captured by Playwright from Storybook or the running app | The picture can no longer drift from the code | The screenshot replaces the wireframe |

- **Checks an agent can run on this note**:
	- Every node in the map has a section with the same name, in the right lane
	- Every edge is stated at both ends (Writes and Written by, Reads and Read by)
	- Every Bound to column exists in the table named in Reads
	- Every screen has a wireframe file, and every callout number has a row

## Rendering notes

- **Two renderers, two layouts**: Mermaid 12.1.0 draws each lane as one row, with every table above the step that writes it; Obsidian 1.15 draws Mermaid with its own renderer (Pele), which stacks nodes inside a lane, so the same map looks looser there
- **Links**: only the `internal-link` class opens notes in Obsidian, and the link target is the node label; a `click ... href` statement becomes an external link and cannot open a section
- **Verified outside Obsidian**: this map was run through both renderers (Mermaid 12.1.0, and the Pele 1.8.0 library bundled with Obsidian 1.15.0), and the three wireframes were rasterized and inspected
- **Not verified**: an actual click on a node inside Obsidian
