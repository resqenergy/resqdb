# ResQDB

Runs energy system simulations for scenarios and keeps their results for analysis and visualization.

## Language

### Results

**Result store**:
A destination where a scenario's simulation results are kept. A run writes to one or more result stores.
_Avoid_: Export, output, backend

**Database store**:
The result store that keeps a scenario's inputs and outputs in the database, where they feed the views used for visualization.
_Avoid_: DB export, upload

**File store**:
The result store that keeps a scenario's outputs as files in a results folder named after the scenario.
_Avoid_: CSV export, results folder
