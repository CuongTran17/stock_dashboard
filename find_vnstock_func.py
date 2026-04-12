import vnstock
import inspect
import sys

def search_module(module, query):
    found = []
    # limit depth or just search top level
    for name, obj in inspect.getmembers(module):
        if not name.startswith('_'):
            if query.lower() in name.lower():
                found.append(f"{module.__name__}.{name}")
            try:
                if inspect.isclass(obj):
                    for m_name, m_obj in inspect.getmembers(obj):
                        if not m_name.startswith('_'):
                            if query.lower() in m_name.lower():
                                found.append(f"{module.__name__}.{name}.{m_name}")
            except Exception:
                pass
    return found

import vnai
print("In vnai:")
queries = ['money', 'macro', 'rate', 'interest', 'interbank', 'lai_suat', 'bank']
for q in queries:
    res = search_module(vnai, q)
    if res:
        print(f"Query '{q}':", res)

print("In vnstock:")
for q in queries:
    res = search_module(vnstock, q)
    if res:
        print(f"Query '{q}':", res)

print("In vnstock.Vnstock:")
for q in queries:
    try:
        res = search_module(vnstock.Vnstock, q)
        if res:
            print(f"Query '{q}':", res)
    except: pass
