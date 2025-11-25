# Shell Emulator – Variant 27  
MIREA – Configuration Management  
Stages 1, 2, 3 and 4 (Python Implementation)

This repository contains a full shell emulator created according to the requirements of **Variant №27** from the Configuration Management course.  
The project evolves through multiple stages, gradually adding features such as REPL, configuration, logging, virtual file system, and real shell commands.

All code is written in **Python 3**.

---

# 📌 Stage 1 — Basic REPL Prototype

### ✔ Implemented Features
- Console-based CLI application.
- REPL loop:
  - Displays prompt: `username@hostname:~$`
  - Reads user input
  - Parses commands, including quoted arguments
  - Prints errors on invalid syntax
- Commands implemented as **stubs**:
  - `ls` → prints its arguments
  - `cd` → prints its arguments
  - `exit` → terminates the emulator
- Unknown commands show a controlled error.

### Example
