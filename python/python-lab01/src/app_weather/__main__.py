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
