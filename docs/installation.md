---
title: Installation
---

# Installation

Requirements:

- Python 3.8+
- `paho-mqtt` (installed automatically when installing the package)

## Robot Library Installation

```bash
git clone git@github.com:Pera-Swarm/robot-library-python.git
cd robot-library-python
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -U pip
pip install -e .
```

## Building Docs locally

From the repository root:

```bash
pip install -r docs/requirements.txt
sphinx-apidoc -o docs/api src/robot
python -m sphinx -b html docs docs/_build/html
```

Or from inside the `docs/` directory:

```bash
pip install -r requirements.txt
make apidoc
make html
```

Use the below command to serve the docs with live reload:

```bash
make livehtml
```
