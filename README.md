# Shell Emulator – Variant 27   
Stages 1, 2, and 3 (Python Implementation)

This project is an educational shell emulator developed according to the Variant №27 specification.  
It is implemented in **Python 3** and grows in complexity across stages.

---

## 📌 Stage 1 — Basic REPL Prototype

### Features implemented
- Console-based application (**CLI**).
- Interactive REPL:
  - Displays prompt: `username@hostname:~$`
  - Reads user input
  - Parses and executes commands
  - Loops until `exit` is called
- Parser supports:
  - Arguments in quotes (`"..."`)
  - Error handling for invalid syntax (e.g., missing quotes).
- Stub commands:
  - `ls` → prints its name and arguments
  - `cd` → prints its name and arguments
- Real command:
  - `exit` → terminates the emulator  
    - If arguments are provided → error message.

### Example interaction
