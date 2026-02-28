Validate a configuration file before making changes. This is the #1 friction reducer — ALWAYS validate before modifying configs.

## Target: $ARGUMENTS

## Steps:

1. **Read the current config file**
   - Read it completely — don't skip sections
   - Note the format (JSON, YAML, TOML, INI)
   - Note the current values

2. **Check syntax validity**
   - JSON: `python3 -c "import json; json.load(open('file'))"`
   - YAML: `python3 -c "import yaml; yaml.safe_load(open('file'))"`
   - TOML: `python3 -c "import tomllib; tomllib.load(open('file', 'rb'))"`
   - Report any syntax errors

3. **Backup the file**
   ```
   cp <file> <file>.backup-$(date +%Y%m%d-%H%M%S)
   ```

4. **Research valid options**
   - For known config files (package.json, tsconfig.json, pyproject.toml, etc.):
     check which keys are valid and what values they accept
   - For unknown config files: look at the application's documentation
   - NEVER guess at config schemas

5. **Report findings**:
   ```
   ## Config Validation: <filename>

   **Format:** JSON/YAML/TOML
   **Syntax:** Valid ✓ / Invalid ✗ (with error details)
   **Backup:** Created at <path>

   ### Current values:
   - key1: value1
   - key2: value2

   ### Proposed changes:
   - key1: value1 → new_value1 (reason)

   ### Risks:
   - Any backwards-compatibility concerns
   - Any dependent services that might break
   ```

6. **Wait for user approval** before making any changes

## Important:
- NEVER modify a config file without validating it first
- NEVER modify a config file without backing it up first
- NEVER guess at config schemas — read documentation
- If unsure about a key/value, say so and ask the user
