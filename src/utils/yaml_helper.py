import os
import yaml

def save_yaml_with_type(fpath, raw_data):
    orig_data = {}
    if os.path.exists(fpath):
        with open(fpath, "r", encoding="utf-8") as f:
            try:
                orig_data = yaml.safe_load(f) or {}
            except Exception:
                orig_data = {}
    data = {}
    for k, v in raw_data.items():
        orig_val = orig_data.get(k, None)
        if isinstance(orig_val, bool):
            data[k] = v == "是" or v == "True" or v is True
        elif isinstance(orig_val, int):
            try:
                data[k] = int(v)
            except Exception:
                data[k] = v
        elif isinstance(orig_val, float):
            try:
                data[k] = float(v)
            except Exception:
                data[k] = v
        else:
            data[k] = v
    with open(fpath, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False) 