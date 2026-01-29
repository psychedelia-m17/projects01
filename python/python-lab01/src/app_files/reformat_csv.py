import csv
import argparse
import sys


def main():
    # Setup command line argument parsing
    parser = argparse.ArgumentParser(description="Reformat CSV columns with fixed-width justification.")
    parser.add_argument("input", help="Path to the source .csv file")
    parser.add_argument("output", help="Path to the destination file")

    args = parser.parse_args()

    try:
        with open(args.input, mode='r', newline='', encoding='utf-8') as infile:
            reader = csv.reader(infile)

            with open(args.output, mode='w', encoding='utf-8') as outfile:
                for row in reader:
                    # Ensure row has at least two columns to avoid IndexErrors
                    if len(row) >= 2:
                        # :<50 left-justifies in a 50-char field
                        # :<15 left-justifies in a 15-char field
                        line = f"{row[0]:<50}{row[1]:<15}\n"
                        outfile.write(line)
                    elif len(row) == 1:
                        # Handle single-column rows gracefully
                        outfile.write(f"{row[0]:<50}\n")

        print(f"Success! Reformatted data written to: {args.output}")

    except FileNotFoundError:
        print(f"Error: The file '{args.input}' does not exist.", file=sys.stderr)
    except PermissionError:
        print(f"Error: Permission denied when accessing the files.", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
