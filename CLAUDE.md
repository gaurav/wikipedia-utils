When creating a Python script, create or update the corresponding CLAUDE.md file explaining the script.
All Python scripts should be runnable with `uv run`.
Use click to provide a simple CLI.
Use logging to provide progress information.
Use tqdm to provide progress bars and completion estimates on long-running loops.
Input and output files should be stored in the `data/` subdirectory.
When running scripts, use tee to write the output into `data/last-run.log`.
