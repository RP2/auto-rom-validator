# TODO

- Package the script as a standalone executable using PyInstaller and upload it under GitHub Releases.
- Automated tests & CI:
  - Write unit tests for parsing, hashing, and renaming logic.
  - Setup GitHub Actions to run linting and tests on every push.
- Packaging & distribution:
  - Publish to PyPI for easy `pip install auto-rom-validator`.
  - Provide an official Docker image for headless usage.
- Configuration & extensibility:
  - Support a config file for custom extension maps, skip rules, and output paths.
  - Re-evaluate and reimplement folder-name-based platform guessing logic (currently reverted).
- Performance & UX:
  - Parallelize file hashing across CPU cores.
  - Enhance progress reporting with overall ETA and summary metrics.
