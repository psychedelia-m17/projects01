import re
import yaml
import argparse
from marko import Markdown
from marko.ext.gfm import GFM

def to_camel_case(text):
    """Converts 'Name With Spaces' to 'camelCase'."""
    s = re.sub(r'[^a-zA-Z0-9 ]', '', text)
    words = s.split()
    if not words: return ""
    return words[0].lower() + "".join(word.capitalize() for word in words[1:])


def parse_details_table(table_node):
    """Parses the Name/Value table in Account Details."""
    details = {}
    for row in table_node.children:
        # Skip header if it contains 'Name' and 'Value'
        cells = [cell.children[0].children for cell in row.children]
        if "Name" in cells and "Value" in cells:
            continue
        if len(cells) >= 2:
            details[to_camel_case(cells[0])] = cells[1]
    return details


def parse_users_table(table_node):
    """Parses the Users table into a list of camelCase objects."""
    users = []
    # Extract headers from first row
    header_row = table_node.children[0]
    headers = [to_camel_case(cell.children[0].children) for cell in header_row.children]

    # Process data rows
    for row in table_node.children[1:]:
        cells = [cell.children[0].children if cell.children else "" for cell in row.children]
        users.append(dict(zip(headers, cells)))
    return users


def convert(md_content):
    # mk = Markdown(extensions=['table'])
    mk = Markdown(extensions=[GFM])
    document = mk.parse(md_content)

    result = []
    current_group = None
    current_account = None
    current_h3 = None

    # We iterate through the children of the document
    for node in document.children:
        ntype = node.get_type()
        print(f"--- Node Type: {ntype}")

        # H1 -> groupName
        if ntype == "Heading" and node.level == 1:
            current_group = {"groupName": node.children[0].children, "accounts": []}
            result.append(current_group)

        # H2 -> accountName
        elif ntype == "Heading" and node.level == 2:
            current_account = {
                "accountName": node.children[0].children,
                "accountDetails": {},
                "addresses": {"billing": [], "shipping": []},
                "users": []
            }
            if current_group:
                current_group["accounts"].append(current_account)

        # H3 -> Set context for subsequent nodes
        elif ntype == "Heading" and node.level == 3:
            current_h3 = node.children[0].children

        # Handle Paragraphs (where addresses live)
        elif ntype == "Paragraph" and current_h3 and "Addresses" in current_h3:
            # We look for the raw text in the paragraph
            # Marko stores paragraph lines in node.children
            full_text = ""
            for child in node.children:
                if hasattr(child, 'children'):  # Handle Bold/Emphasis
                    full_text += str(child.children[0])
                else:
                    full_text += str(child)

            # Split by the bold markers to isolate addresses
            # Regex captures everything after the marker until the next marker
            # billing_match = re.search(r"\*\*Billing Address:\*\*\s*(.*?)(?=\*\*Shipping|$)", full_text, re.DOTALL)
            billing_match = re.search(r"^\*\*Billing Address:\*\*.*?(?=\n\s*\n|\Z)", full_text, re.DOTALL)

            # shipping_match = re.search(r"\*\*Shipping Addresses\s*\(\d+\):\*\*\s*(.*)", full_text, re.DOTALL)
            shipping_match = re.search(r"^\*\*Shipping Address:\*\*.*?(?=\n\s*\n|\Z)", full_text, re.DOTALL)

            if billing_match:
                addr = billing_match.group(1).strip()
                if addr: current_account["addresses"]["billing"].append(addr)

            if shipping_match:
                # If there are multiple shipping addresses, you can split by newline
                addr_lines = [line.strip() for line in shipping_match.group(1).strip().split('\n') if line.strip()]
                current_account["addresses"]["shipping"].extend(addr_lines)

        # Handle Tables (Account Details or Users)
        elif ntype == "Table":
            if current_h3 and "Account Details" in current_h3:
                current_account["accountDetails"].update(parse_details_table(node))
            elif current_h3 and "Users" in current_h3:
                current_account["users"].extend(parse_users_table(node))

    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source", required=True)
    parser.add_argument("-t", "--target", required=True)
    args = parser.parse_args()

    with open(args.source, 'r', encoding='utf-8') as f:
        data = convert(f.read())

    with open(args.target, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, sort_keys=False, indent=2, default_flow_style=False)


if __name__ == "__main__":
    main()
