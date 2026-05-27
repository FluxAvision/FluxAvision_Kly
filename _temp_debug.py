import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'D:\FluxAvision\FluxAvision_Kly\frontend-vue\src\components\large-screen\designer\PropertyPanel.vue', encoding='utf-8') as f:
    content = f.read()

# Find first occurrence of 'type="color"'
idx = content.find('type="color"')
print("First 'type=\"color\"' at index:", idx)
# Show 50 chars before and 50 after
start = max(0, idx - 200)
end = min(len(content), idx + 200)
print(repr(content[start:end]))
print("---")

# Also check line endings
print("Line ending check:")
print("Has \\r\\n:", '\\r\\n' in content[0:10000])
print("Has \\n only:", '\\n' in content[0:10000] and '\\r\\n' not in content[0:10000])
