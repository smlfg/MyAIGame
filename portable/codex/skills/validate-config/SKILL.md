---
name: validate-config
description: "Validate a configuration file before making changes"
argument-hint: "[config file path]"
category: utility
cost-tier: free
dependencies:
  tools: [file_read, shell, research]
tags: [config, validation, safety]
---

# /validate-config -- Config File Validation

Validate a configuration file before making changes. This is the #1 friction reducer.

## Target: $ARGUMENTS

## Steps:

1. **Read the current config file** via {{read_file(config_path)}}
   - Note the format (JSON, YAML, TOML, INI)
   - Note the current values

2. **Check syntax validity**
   - JSON: {{shell("python3 -c \"import json; json.load(open('file'))\"")}}
   - YAML: {{shell("python3 -c \"import yaml; yaml.safe_load(open('file'))\"")}}
   - TOML: {{shell("python3 -c \"import tomllib; tomllib.load(open('file', 'rb'))\"")}}

3. **Backup the file**
   {{shell("cp <file> <file>.backup-$(date +%Y%m%d-%H%M%S)")}}

4. **Research valid options**
   - For known config files: check which keys are valid
   - For unknown config files: {{research("valid options for [config type]")}}
   - NEVER guess at config schemas

5. **Report findings**:
   ```
   ## Config Validation: <filename>
   **Format:** JSON/YAML/TOML
   **Syntax:** Valid / Invalid (with error details)
   **Backup:** Created at <path>
   ### Current values:
   ### Proposed changes:
   ### Risks:
   ```

6. **Wait for user approval** before making any changes

## Important:
- NEVER modify a config file without validating it first
- NEVER modify a config file without backing it up first
- NEVER guess at config schemas -- read documentation
