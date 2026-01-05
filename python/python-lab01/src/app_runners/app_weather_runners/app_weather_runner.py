# app_weather_runner.py

# Print the Python module search path
import sys

print(f"{50 * '-'}", f"\nsys.path: \n{sys.path}",f"\n{50 * '-'}")

# Set environment variable PYTHONPATH to include the path upto .../python-lab01/src
import app_weather

city = "Patna"
weather_data = app_weather.get_weather(city)
print(f"weather_data={weather_data}")
print(app_weather.format_output(weather_data))
