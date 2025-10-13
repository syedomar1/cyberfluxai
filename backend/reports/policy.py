# reports/policy.py
def can_autorun(action, asset_context):
    if action['type'] == 'isolate_host' and asset_context.get('critical', False):
        return False
    if action['impact_estimate'] > 5:
        return False
    return True
