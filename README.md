# Shell Emulator – Stage 1 (Variant 27)

This is a minimal shell emulator implemented in Python for **Stage 1** of the assignment (Variant 27).

## Requirements covered

According to the specification:

- The application is implemented as a **console (CLI)** program.
- The prompt is based on real OS data:  
  `username@hostname:~$`
- The parser correctly handles **quoted arguments** (single and double quotes).
- The program reports an error when:
  - the command is unknown
  - `exit` is called with invalid arguments
- Stub commands:
  - `ls` – prints its name and arguments
  - `cd` – prints its name and arguments
- `exit` command terminates the emulator.
- The shell works in **interactive REPL** mode.

## How to run

```bash
python main.py
