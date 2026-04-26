import json

data = json.load(open('data/artifacts/f6c8e2b797aad2f7e45a56e8745b04852d9850b8/doc_requests.json'))

print(f"Total requests: {len(data)}")
print("\nFirst 5 requests:")
for i, r in enumerate(data[:5]):
    if 'insertText' in r:
        print(f"  {i}: insertText at index {r['insertText']['location']['index']}: '{r['insertText']['text'][:40]}...'")
    elif 'insertTable' in r:
        print(f"  {i}: insertTable: {r['insertTable']['rows']} rows, {r['insertTable']['columns']} cols")
    elif 'insertSectionBreak' in r:
        print(f"  {i}: insertSectionBreak")
    else:
        print(f"  {i}: {list(r.keys())[0]}")

print("\nLast 5 requests:")
for i, r in enumerate(data[-5:], len(data)-5):
    if 'insertText' in r:
        print(f"  {i}: insertText at index {r['insertText']['location']['index']}: '{r['insertText']['text'][:40]}...'")
    elif 'insertTable' in r:
        print(f"  {i}: insertTable: {r['insertTable']['rows']} rows")
    elif 'insertSectionBreak' in r:
        print(f"  {i}: insertSectionBreak")
    else:
        print(f"  {i}: {list(r.keys())[0]}")

# Check for any potential issues
indices = []
for r in data:
    if 'insertText' in r:
        indices.append(('insertText', r['insertText']['location']['index']))
    elif 'insertTable' in r:
        indices.append(('insertTable', r['insertTable']['location']['index']))

print(f"\nIndex range: {min(i[1] for i in indices)} to {max(i[1] for i in indices)}")
