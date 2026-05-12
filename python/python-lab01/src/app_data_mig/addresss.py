import re


def parse_addresses(lines):
    in_addresses_section = False
    current_mode = None  # Can be 'billing' or 'shipping'

    addresses = {"billing": [], "shipping": []}
    temp_address = []
    is_capturing = False

    for line in lines:
        clean_line = line.strip()

        # 1. Detect the H3 Header to start parsing
        if "### Addresses" in clean_line or "Addresses" in clean_line:
            in_addresses_section = True
            continue

        if not in_addresses_section:
            continue

        # 2. Identify the type of address following
        if "Billing Address" in clean_line:
            current_mode = "billing"
            continue
        elif "Shipping Address" in clean_line:
            current_mode = "shipping"
            continue

        # 3. Detect the start of an address block (contains **...**)
        # Regex looks for text surrounded by double asterisks
        if re.search(r"\*\*.*?\*\*", clean_line):
            is_capturing = True
            temp_address.append(clean_line)
            continue

        # 4. Detect the end of an address block (blank line)
        if is_capturing and not clean_line:
            if current_mode:
                addresses[current_mode].append("\n".join(temp_address))
            temp_address = []
            is_capturing = False
            continue

        # 5. Capture lines if we are inside a block
        if is_capturing:
            temp_address.append(clean_line)

    return addresses

# Example usage:
# data = open('invoice.md').readlines()
# result = parse_addresses(data)