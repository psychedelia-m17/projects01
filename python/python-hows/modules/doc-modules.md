# Python Modules

# PYTHONPATH, __init__.py and -m

> Explain python module loading using PYTHONPATH, the necessity of __init__.py in packages and  how python locates modules using the -m option

Understanding how Python finds and executes code is the difference between a project that runs smoothly and one that is plagued by `ImportError` or `ModuleNotFoundError`.

Here is the breakdown of the three pillars of Python module resolution.

---

## 1. The Module Search Path and `PYTHONPATH`

When you type `import my_module`, Python doesn't look everywhere on your hard drive. It follows a specific "shopping list" of directories stored in `sys.path`.

### How `sys.path` is built:

1. **The Home Directory:** The directory containing the script being run (or the current directory if using the interactive shell).
2. **`PYTHONPATH`:** This is an environment variable you can set. It contains a list of directory paths that Python should check **before** the standard library.
3. **Standard Library:** The built-in modules that come with Python (e.g., `os`, `sys`, `json`).
4. **Site-Packages:** Where third-party libraries installed via `pip` reside.

### Why use `PYTHONPATH`?

It is a "shortcut" for developers. If you are working on a project with a custom folder structure and want to import modules from a directory that isn't naturally in the search path, you add that directory to `PYTHONPATH`.

> **Tip:** You can see your current search path by running:
> ```python
> import sys
> print(sys.path)
> 
> ```
> 
> 

---

## 2. Is `__init__.py` Required?

The answer changed with Python 3.3. There are now two types of packages:

### Regular Packages (Require `__init__.py`)

To Python, a directory is a "Regular Package" if it contains an `__init__.py` file.

* **Role:** It executes code upon the first import of the package. It is used to initialize state or "hoist" specific functions to the package level.
* **Requirement:** If you want to use the directory as a standard, self-contained unit, you **should** include this file.

### Namespace Packages (Do NOT require `__init__.py`)

Introduced in PEP 420, these allow a single package to be spread across multiple directories.

* **Role:** They allow developers to distribute parts of a library separately (e.g., `company.core` and `company.auth` in different zip files).
* **Requirement:** Python 3.3+ will recognize a directory as a package even without the file, provided it's found in `sys.path`.

**Recommendation:** Always use `__init__.py` unless you are specifically building a complex, split-directory library. It makes your intent clear to other developers and tools.

---

## 3. How Python Locates Modules using `-m`

The `-m` (module) option tells Python to run a library module as a script. This changes the search behavior in a subtle but critical way.

### The `-m` Mechanism:

1. **Search:** Python searches `sys.path` for the module name provided (just like a standard import).
2. **Current Directory:** Unlike running a script by file path (`python path/to/script.py`), using `-m` adds the **current working directory** to the beginning of `sys.path`.
3. **The Entry Point:** If you point to a package (e.g., `python -m my_package`), Python looks for a file named **`__main__.py`** inside that package and executes it.

### Why use `-m`?

It solves the "Relative Import" headache.

* If you run `python my_package/script.py`, Python treats `script.py` as a standalone file. It has no idea it's inside a package, so `from .other_module import x` will fail.
* If you run `python -m my_package.script`, Python knows the full context of the package, allowing relative imports to work perfectly.

---

### Summary Table

| Feature | `PYTHONPATH` | `__init__.py` | `python -m` |
| --- | --- | --- | --- |
| **Primary Goal** | Add custom search paths. | Identify a directory as a package. | Run a package as a script with context. |
| **User Controlled?** | Yes, via Env Var. | Yes, by creating the file. | Yes, via CLI flag. |
| **Critical File** | N/A | `__init__.py` | `__main__.py` |

**Would you like to see a sample project structure that demonstrates how to set up `__init__.py` and `__main__.py` to work correctly with `-m`?**

----------------------------------------------------------------------------

# Python modules and packages

To set up a professional Python project that functions correctly as a library and a runnable script, you need to understand the relationship between the directory structure and these special files.

Here is a complete sample project called **`weather_app`**.

---

## 1. Project Structure

```text
my_workspace/                # Root directory (where you run commands)
└── weather_app/             # The Package directory
    ├── __init__.py          # Marks directory as a package
    ├── __main__.py          # Entry point for "python -m weather_app"
    ├── engine.py            # Logic module
    └── formatter.py         # Utility module

```

---

## 2. File Implementation

### `weather_app/engine.py` (The Logic)

This is a standard module. Notice it doesn't know about the CLI or the package structure yet.

```python
def get_weather(city: str):
    # Simulated weather data
    return {"city": city, "temp": 22, "condition": "Sunny"}

```

### `weather_app/formatter.py` (The Utility)

```python
def format_output(data: dict):
    return f"Current weather in {data['city']}: {data['temp']}°C, {data['condition']}."

```

### `weather_app/__init__.py` (The Package Gatekeeper)

We use this to "hoist" functions so users can import them easily without knowing the internal file names.

```python
# Simplify imports for external users
from .engine import get_weather
from .formatter import format_output

__version__ = "1.0.0"

```

### `weather_app/__main__.py` (The Entry Point)

This file is only executed when you run the package with the `-m` flag. It handles command-line arguments.

```python
import sys
from .engine import get_weather
from .formatter import format_output

def main():
    # Basic CLI handling
    if len(sys.argv) < 2:
        print("Error: Please provide a city name.")
        sys.exit(1)

    city = sys.argv[1]
    data = get_weather(city)
    print(format_output(data))

if __name__ == "__main__":
    main()

```

---

## 3. How to Execute

To run this correctly, you must be in the `my_workspace` directory (the folder **above** `weather_app`).

### Running as a Module

```bash
python -m weather_app London

```

**What happens:** 1. Python adds the current directory (`my_workspace`) to `sys.path`.
2. It finds the `weather_app` package.
3. It executes `__main__.py` inside that package.
4. **Result:** `Current weather in London: 22°C, Sunny.`

### Importing as a Library

Because of our `__init__.py`, an external script can use the package very cleanly:

```python
import weather_app

data = weather_app.get_weather("Paris")
print(weather_app.format_output(data))

```

---

## Key Takeaways

* **`__init__.py`** is for **Programmers**: It defines what people see when they `import` your code.
* **`__main__.py`** is for **Users**: It defines what happens when someone runs your code from the **Terminal**.
* **Relative Imports:** Inside a package, always use `from .module import ...` (the dot represents the current package). This only works correctly when the package is loaded via `-m` or as a regular import.

Would you like me to show you how to package this structure into a distributable `.whl` file so others can install it via `pip`?

