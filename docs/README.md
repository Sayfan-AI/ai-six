# AI-6 Documentation Guide

This README provides all the information you need to work with the AI-6 Python documentation, including manual builds, ReadTheDocs integration, structure, and tips.

---

## TODOs

 1. [ ] Populate missing module docstrings
 2. [ ] Add info on building docs on Windows
 3. [ ] Find a better approach to customize the sidebar

---

## ⚙️ Setting Up the Documentation Environment

1. **Create a virtual environment** (recommended):

```
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. **Install project dependencies**:

```
pip install -r py/requirements.txt
```

3. **Install documentation dependencies**:

```
pip install -r docs/requirements-docs.txt
```

> Optional: you can also install the package in editable mode to simplify imports:

```
pip install -e py
```

---

## 🏗 Manual Build

1. Build HTML:

```
make html  # Linux/Mac
# TODO(2): Windows support
```

3. Open the generated docs:

```
open _build/html/index.html  # Mac
xdg-open _build/html/index.html  # Linux
```

---

## 📖 Sphinx Configuration

Key settings in `docs/conf.py`:

- **Markdown support**: `myst_parser` extension  
- **Autodoc**: Automatically generates API docs from Python code  
- **Theme**: `furo` for modern, clean appearance  

If using editable installs, you can remove the `sys.path.insert` hack:

```
sys.path.insert(0, os.path.abspath("../py"))
```

---

## 🖥 Sidebar Module Name Customization

The documentation uses the Furo theme, which displays fully qualified module names (FQNs) in the sidebar by default. To simplify navigation, we trim the sidebar labels to show only the module name itself while keeping the full FQN in page headers and URLs.

This is done using a small JavaScript snippet in `docs/_static/custom_sidebar.js`, which is referenced in `conf.py`.

**If the theme is changed, it's likely that this JS snippet will need to be modified.**

> TODO(3): Find a better approach to modify the sidebar module names

---

## 🌐 ReadTheDocs Integration

The project uses `.readthedocs.yaml` to configure RTD

Steps to connect:

1. Push your repo to GitHub/GitLab/Bitbucket.  
2. Log in to [ReadTheDocs](https://readthedocs.org/).  
3. Import the repository and select the main branch.  
4. RTD will automatically build and host the documentation whenever you push updates.  

---

## 🔧 Docstring Style

- Supports **mixed docstring styles**: Google, NumPy, and plain.  
- Napoleon parses structured docstrings to render clean HTML in the docs.  
- Plain docstrings are rendered as-is.  

Example:

**Google-style**
```
def example(x: int) -> int:
    """
    Args:
        x: input value
    Returns:
        squared value
    """
```

**NumPy-style**
```
def example(x: int) -> int:
    """
    Parameters
    ----------
    x : int
        input value
    Returns
    -------
    int
        squared value
    """
```

---

## 💡 Tips

- Keep project dependencies and doc dependencies separate (`py/requirements.txt` vs `docs/requirements-docs.txt`).  
- Markdown pages (`.md`) are supported via `myst_parser`, but auto-generated API pages are `.rst`. Mixed usage is fine.  
