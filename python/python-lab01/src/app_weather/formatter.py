# formatter.py

def format_output(data: dict):
    return f"Current weather in {data['city']}: {data['temp']}°C, {data['condition']}."
