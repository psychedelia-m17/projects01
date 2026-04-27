import re
import yaml
import argparse
from marko import Markdown


def to_camel_case(text):
    """Converts 'Pascal Case With Spaces' to 'camelCase'."""
    s = re.sub(r'[^a-zA-Z0-9 ]', '', text)
    words = s.split()
    if not words:
        return ""
    return words[0].lower() + "".join(word.capitalize() for word in words[1:])


def parse_table(table_node):
    """Extracts data from a Marko table node into a list of lists."""
    data = []
    for row in table_node.children:
        cells = [cell.children[0].children if cell.children else "" for cell in row.children]
        data.append(cells)
    return data


def convert(md_content):
    mk = Markdown(extensions=['table'])
    document = mk.parse(md_content)

    result = []
    current_group = None
    current_account = None

    for node in document.children:
        # H1 -> groupName
        if node.get_type() == "Heading" and node.level == 1:
            current_group = {"groupName": node.children[0].children, "accounts": []}
            result.append(current_group)

        # H2 -> accountName
        elif node.get_type() == "Heading" and node.level == 2:
            current_account = {
                "accountName": node.children[0].children,
                "accountDetails": {},
                "addresses": {"billing": [], "shipping": []},
                "users": []
            }
            if current_group:
                current_group["accounts"].append(current_account)

        # H3 Sections
        elif node.get_type() == "Heading" and node.level == 3:
            current_h3 = node.children[0].children

            # Find the next node (which should be a table)
            next_node = document.children[document.children.index(node) + 1]
            if next_node.get_type() != "Table":
                continue

            table_data = parse_table(next_node)

            if "Account details" in current_h3:
                for row in table_data:
                    if len(row) >= 2:
                        key = to_camel_case(row[0])
                        current_account["accountDetails"][key] = row[1]

            elif "Addresses" in current_h3:
                # Assuming table columns: Type, Street, City, etc.
                headers = [to_camel_case(h) for h in table_data[0]]
                for row in table_data[1:]:
                    addr_obj = dict(zip(headers[1:], row[1:]))
                    addr_type = row[0].lower()  # 'billing' or 'shipping'
                    if addr_type in current_account["addresses"]:
                        current_account["addresses"][addr_type].append(addr_obj)

            elif "Users" in current_h3:
                headers = [to_camel_case(h) for h in table_data[0]]
                for row in table_data[1:]:
                    user_obj = dict(zip(headers, row))
                    current_account["users"].append(user_obj)

    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source", required=True)
    parser.add_argument("-t", "--target", required=True)
    args = parser.parse_args()

    with open(args.source, 'r') as f:
        data = convert(f.read())

    with open(args.target, 'w') as f:
        yaml.dump(data, f, sort_keys=False, indent=2)


if __name__ == "__main__":
    main()

