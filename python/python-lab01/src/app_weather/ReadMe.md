# Package and Module Sample

## Objective

Python module and package samples.

## Structure

```text
src/                         # Root directory (where you run commands)
└── app_weather/             # The Package directory
    ├── __init__.py          # Marks directory as a package
    ├── __main__.py          # Entry point for "python -m weather_app"
    ├── engine.py            # Logic module
    └── formatter.py         # Utility module
```

## How to run

To run this correctly, you must be in the `src` directory (the folder above `app_weather`).

```bash
python -m app_weather Wasseypur
```

> 1. Python adds the current directory i.e. `src` to `sys.path`.  
> 2. Python finds the `app_weather` package.
> 3. Python executes `__main__.py` contained in the package.

To run this app from another Python program, it can be imported as:  

```python
import app_weather

data = app_weather.get_weather("Agra")
print(app_weather.format_output(data))
```
