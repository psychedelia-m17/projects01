import re
import yaml
import argparse
from marko import Markdown
from marko.ext.gfm import GFM


def to_camel_case(text):
    s = re.sub(r'[^a-zA-Z0-9 ]', '', text)
    words = s.split()
    if not words: return ""
    return words[0].lower() + "".join(word.capitalize() for word in words[1:])


def parse_details_table(table_node):
    details = {}
    for row in table_node.children:
        cells = [cell.children[0].children for cell in row.children]
        if "Name" in cells and "Value" in cells: continue
        if len(cells) >= 2:
            details[to_camel_case(cells[0])] = cells[1]
    return details


def parse_users_table(table_node):
    users = []
    header_row = table_node.children[0]
    headers = [to_camel_case(cell.children[0].children) for cell in header_row.children]
    for row in table_node.children[1:]:
        cells = [cell.children[0].children if cell.children else "" for cell in row.children]
        users.append(dict(zip(headers, cells)))
    return users


def parse_address_section(lines):
    """
    Processes lines within the Addresses H3 node.
    """
    addresses = {"billing": [], "shipping": []}
    current_category = None  # 'billing' or 'shipping'
    current_address_lines = []
    in_address_block = False

    for line in lines:
        clean_line = line.strip()

        # 1. Detect Category
        if "Billing Address" in clean_line:
            current_category = "billing"
            continue
        elif "Shipping Addresses" in clean_line:
            current_category = "shipping"
            continue

        if not current_category:
            continue

        # 2. Detect Address Start (contains text within ** or _1._ **)
        # Matches: **Text**, _1._ **Text**, 1. **Text**
        is_start_marker = bool(re.search(r"\*\*.*?\*\*", clean_line))

        if is_start_marker:
            in_address_block = True
            current_address_lines = [clean_line]
        elif in_address_block:
            if clean_line == "":  # 3. Detect Address End (blank line)
                addresses[current_category].append("\n".join(current_address_lines))
                current_address_lines = []
                in_address_block = False
            else:
                current_address_lines.append(clean_line)

    # Catch last address if file doesn't end in a blank line
    if in_address_block and current_address_lines:
        addresses[current_category].append("\n".join(current_address_lines))

    return addresses


def convert(md_content):
    mk = Markdown(extensions=[GFM])
    document = mk.parse(md_content)

    result = []
    current_group = None
    current_account = None
    current_h3 = None

    for node in document.children:
        ntype = node.get_type()

        if ntype == "Heading" and node.level == 1:
            current_group = {"groupName": node.children[0].children, "accounts": []}
            result.append(current_group)

        elif ntype == "Heading" and node.level == 2:
            current_account = {
                "accountName": node.children[0].children,
                "accountDetails": {},
                "addresses": {"billing": [], "shipping": []},
                "users": []
            }
            if current_group:
                current_group["accounts"].append(current_account)

        elif ntype == "Heading" and node.level == 3:
            current_h3 = node.children[0].children

        elif ntype == "Paragraph" and current_h3 and "Addresses" in current_h3:
            raw_lines = []
            for child in node.children:
                # If it's a 'Strong' (bold) or 'Emphasis' (italic) node
                if hasattr(child, 'children'):
                    # Recursively get text from children if they are objects, else take string
                    inner_text = "".join(
                        c.children if hasattr(c, 'children') else str(c)
                        for c in child.children
                    )

                    # Reconstruct markers based on type
                    if child.get_type() == "Strong":
                        raw_lines.append(f"**{inner_text}**")
                    elif child.get_type() == "Emphasis":
                        raw_lines.append(f"_{inner_text}_")
                    else:
                        raw_lines.append(inner_text)
                else:
                    # It's a plain string
                    raw_lines.append(str(child))

            # Combine into a single string and split into lines for the state machine
            full_text = "".join(raw_lines)
            lines = full_text.splitlines()

            addr_data = parse_address_section(lines)
            current_account["addresses"]["billing"].extend(addr_data["billing"])
            current_account["addresses"]["shipping"].extend(addr_data["shipping"])

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