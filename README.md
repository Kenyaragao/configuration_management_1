# Shell Emulator – Stage 2 (Variant 27)

This is the Stage 2 implementation of the shell emulator for the course
"Configuration Management".

## New features in Stage 2

- Command-line parameters:
  - `--vfs PATH` – physical location of the VFS (not used yet, only stored)
  - `--log PATH` – XML log file path
  - `--script PATH` – startup script with shell commands
- Debug output of all configuration parameters at startup.
- XML logging of command events:
  - username
  - timestamp
  - command name
  - arguments
  - success / failure
  - optional error message
- Startup script:
  - supports comments starting with `#`
  - during execution, both input and output are printed
  - errors are reported

## How to run

Interactive only:

```bash
python main.py
