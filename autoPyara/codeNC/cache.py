
# This is deprecated, don't use!
def evaluate_rule(yara_file, rule_name):
    yara_file = yara_file['output']

    if isinstance(yara_file, str):
        print("rule eval for", rule_name)
        print(yara_file)
        return

    if len(yara_file.rules) <= 0:
        print("rule eval for", rule_name, "... has no rule!")
        return

    rule = yara_file.rules[0]  # Since you have one rule per object

    print("rule eval for", rule_name, yara_file.text)
    print({
        'total_rules': 1,
        'string_count': len(rule.strings),
        'condition_text': rule.condition.text
    })
