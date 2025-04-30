# CodeBatchCopy

A command-line utility for interactively selecting and copying multiple code files with proper formatting for sharing or documentation.

## Quick Start

### Windows
```
cd path\to\your\project
path\to\CodeBatchCopy\code_batch_copy.bat
```

### macOS/Linux
```
cd /path/to/your/project
/path/to/CodeBatchCopy/code_batch_copy.sh
```

Then:
1. Use **spacebar** to select files/directories
2. Press **Enter** to confirm
3. Select "(Fertig / Weiter)" when done with current directory
4. When finished, formatted code will be copied to your clipboard

## Overview

CodeBatchCopy allows you to navigate through your project's directory structure, select specific files and directories, and generate a formatted output of all selected file contents. The tool automatically formats code with appropriate syntax highlighting based on file extensions and copies the result to your clipboard.

## Features

- Interactive directory navigation and file selection
- Syntax highlighting for various programming languages
- Persistent state saving between sessions
- Automatic clipboard copying of formatted output
- Cross-platform support (Windows, macOS, Linux)
- Hierarchical selection validation to ensure path consistency

## Requirements

- Python 3.6+
- Dependencies:
  - questionary (1.10.0)
  - pyperclip (1.9.0)

## Installation

No installation required. The tool automatically sets up a virtual environment and installs its dependencies when first run.

## Usage

### On Windows

```
code_batch_copy.bat [base_directory]
```

### On macOS/Linux

```
./code_batch_copy.sh [base_directory]
```

If no base directory is provided, the current working directory is used.

## How It Works

1. **Directory Navigation**: The tool presents a checkbox interface to select files and directories.
2. **Selection**: Use the spacebar to select/deselect items and Enter to confirm your selection.
3. **Recursive Exploration**: When directories are selected, the tool will recursively explore them.
4. **Consistency Check**: The tool ensures all selected paths form a consistent hierarchy.
5. **Output Generation**: Selected file contents are formatted with appropriate syntax highlighting.
6. **Clipboard Copy**: The formatted output is automatically copied to your clipboard.

## Output Format

The output is formatted as Markdown with code blocks and appropriate syntax highlighting:

```
## ./path/to/file.py
```python
# File contents here
```

## ./another/file.js
```javascript
// Another file contents
```
```

## State Persistence

The tool saves your selection state in a `.code_batch_copy.json` file in the script directory, allowing you to resume your work in subsequent sessions.

## Use Cases

- Sharing code snippets with colleagues
- Preparing code examples for documentation
- Creating code samples for tutorials or presentations
- Generating formatted code for inclusion in Markdown documents

## Notes

- The tool maintains absolute paths internally but displays relative paths for better readability.
- Language detection is based on file extensions, with fallback to plain text for unknown types.
