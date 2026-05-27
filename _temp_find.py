with open(r'D:\FluxAvision\FluxAvision_Kly\frontend-vue\src\components\large-screen\designer\PropertyPanel.vue', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'type="color"' in line:
        print(f'Line {i+1}: {repr(line)}')
