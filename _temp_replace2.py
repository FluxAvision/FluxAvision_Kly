import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'D:\FluxAvision\FluxAvision_Kly\frontend-vue\src\components\large-screen\designer\PropertyPanel.vue', encoding='utf-8') as f:
    content = f.read()

# === Section 1: 背景 - 背景颜色 (lines 289-307) ===
indent_8 = '        '
indent_10 = '          '
indent_12 = '            '
indent_14 = '              '
indent_16 = '                '

old1 = (
    indent_8 + '<div>\n'
    + indent_10 + '<label class="block text-xs text-[#5a6a80] mb-1">背景颜色</label>\n'
    + indent_10 + '<div class="flex items-center gap-2">\n'
    + indent_12 + '<div class="relative w-8 h-8 rounded cursor-pointer overflow-hidden border border-[#1e293b]">\n'
    + indent_14 + '<div class="absolute inset-0 rounded" :style="{ backgroundColor: localCanvasBg }"></div>\n'
    + indent_14 + '<input\n'
    + indent_16 + 'type="color"\n'
    + indent_16 + ':value="localCanvasBg"\n'
    + indent_16 + '@input="handleColorInput($event, v => { localCanvasBg = v; applyCanvasConfig() })"\n'
    + indent_16 + 'class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"\n'
    + indent_14 + '/>\n'
    + indent_12 + '</div>\n'
    + indent_12 + '<input\n'
    + indent_14 + ':value="localCanvasBg"\n'
    + indent_14 + '@input="handleColorInput($event, v => { localCanvasBg = v; applyCanvasConfig() })"\n'
    + indent_14 + 'class="flex-1 h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white font-mono outline-none focus:border-[#00d9ff] transition-colors"\n'
    + indent_12 + '/>\n'
    + indent_10 + '</div>\n'
    + indent_8 + '</div>'
)

new1 = (
    indent_8 + '<div>\n'
    + indent_10 + '<label class="block text-xs text-[#5a6a80] mb-1">背景颜色</label>\n'
    + indent_10 + '<div class="flex items-center gap-0 rounded-md border border-[#1e293b] overflow-hidden">\n'
    + indent_12 + '<input\n'
    + indent_14 + 'type="color"\n'
    + indent_14 + ':value="localCanvasBg"\n'
    + indent_14 + '@input="handleColorInput($event, v => { localCanvasBg = v; applyCanvasConfig() })"\n'
    + indent_14 + 'class="w-10 h-8 cursor-pointer border-0 p-0.5 bg-transparent"\n'
    + indent_14 + 'style="flex-shrink: 0; min-width: 40px;"\n'
    + indent_12 + '/>\n'
    + indent_12 + '<input\n'
    + indent_14 + ':value="localCanvasBg"\n'
    + indent_14 + '@input="handleColorInput($event, v => { localCanvasBg = v; applyCanvasConfig() })"\n'
    + indent_14 + 'class="flex-1 h-8 px-2.5 text-xs text-white font-mono outline-none bg-[#112240]"\n'
    + indent_14 + 'style="border: none !important;"\n'
    + indent_12 + '/>\n'
    + indent_10 + '</div>\n'
    + indent_8 + '</div>'
)

# === Section 2: 排版 - 颜色 (lines 483-500) ===
old2_inner = indent_14 + '<div>\n'
old2_inner += indent_16 + '<label class="block text-xs text-[#5a6a80] mb-1">颜色</label>\n'
old2_inner += indent_16 + '<div class="flex items-center gap-2">\n'
old2_inner += indent_18 + '<div class="relative w-8 h-8 rounded cursor-pointer overflow-hidden border border-[#1e293b]">\n'
old2_inner += indent_20 + '<div class="absolute inset-0 rounded" :style="{ backgroundColor: localStyles.color || \'#ffffff\' }"></div>\n'
old2_inner += indent_20 + '<input\n'
old2_inner += indent_22 + 'type="color"\n'
old2_inner += indent_22 + ':value="localStyles.color || \'#ffffff\'"\n'
old2_inner += indent_22 + '@input="handleColorInput($event, v => { localStyles.color = v; applyStyles() })"\n'
old2_inner += indent_22 + 'class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"\n'
old2_inner += indent_20 + '/>\n'
old2_inner += indent_18 + '</div>\n'
old2_inner += indent_18 + '<input\n'
old2_inner += indent_20 + ':value="localStyles.color || \'\'"\n'
old2_inner += indent_20 + '@input="handleColorInput($event, v => { localStyles.color = v; applyStyles() })"\n'
old2_inner += indent_20 + 'class="flex-1 h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white font-mono outline-none focus:border-[#00d9ff] transition-colors"\n'
old2_inner += indent_20 + 'placeholder="#ffffff"\n'
old2_inner += indent_18 + '/>\n'
old2_inner += indent_16 + '</div>\n'
old2_inner += indent_14 + '</div>'

new2_inner = indent_14 + '<div>\n'
new2_inner += indent_16 + '<label class="block text-xs text-[#5a6a80] mb-1">颜色</label>\n'
new2_inner += indent_16 + '<div class="flex items-center gap-0 rounded-md border border-[#1e293b] overflow-hidden">\n'
new2_inner += indent_18 + '<input\n'
new2_inner += indent_20 + 'type="color"\n'
new2_inner += indent_20 + ':value="localStyles.color || \'#ffffff\'"\n'
new2_inner += indent_20 + '@input="handleColorInput($event, v => { localStyles.color = v; applyStyles() })"\n'
new2_inner += indent_20 + 'class="w-10 h-8 cursor-pointer border-0 p-0.5 bg-transparent"\n'
new2_inner += indent_20 + 'style="flex-shrink: 0; min-width: 40px;"\n'
new2_inner += indent_18 + '/>\n'
new2_inner += indent_18 + '<input\n'
new2_inner += indent_20 + ':value="localStyles.color || \'\'"\n'
new2_inner += indent_20 + '@input="handleColorInput($event, v => { localStyles.color = v; applyStyles() })"\n'
new2_inner += indent_20 + 'class="flex-1 h-8 px-2.5 text-xs text-white font-mono outline-none bg-[#112240]"\n'
new2_inner += indent_20 + 'style="border: none !important;"\n'
new2_inner += indent_20 + 'placeholder="#ffffff"\n'
new2_inner += indent_18 + '/>\n'
new2_inner += indent_16 + '</div>\n'
new2_inner += indent_14 + '</div>'

# === Section 3: 边框与圆角 - 背景色 (lines 538-555) ===
old3_inner = indent_14 + '<div>\n'
old3_inner += indent_16 + '<label class="block text-xs text-[#5a6a80] mb-1">背景色</label>\n'
old3_inner += indent_16 + '<div class="flex items-center gap-2">\n'
old3_inner += indent_18 + '<div class="relative w-8 h-8 rounded cursor-pointer overflow-hidden border border-[#1e293b]">\n'
old3_inner += indent_20 + '<div class="absolute inset-0 rounded" :style="{ backgroundColor: localStyles.backgroundColor || \'transparent\' }"></div>\n'
old3_inner += indent_20 + '<input\n'
old3_inner += indent_22 + 'type="color"\n'
old3_inner += indent_22 + ':value="localStyles.backgroundColor || \'transparent\'"\n'
old3_inner += indent_22 + '@input="handleColorInput($event, v => { localStyles.backgroundColor = v; applyStyles() })"\n'
old3_inner += indent_22 + 'class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"\n'
old3_inner += indent_20 + '/>\n'
old3_inner += indent_18 + '</div>\n'
old3_inner += indent_18 + '<input\n'
old3_inner += indent_20 + ':value="localStyles.backgroundColor || \'\'"\n'
old3_inner += indent_20 + '@input="handleColorInput($event, v => { localStyles.backgroundColor = v || undefined; applyStyles() })"\n'
old3_inner += indent_20 + 'class="flex-1 h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white font-mono outline-none focus:border-[#00d9ff] transition-colors"\n'
old3_inner += indent_20 + 'placeholder="transparent"\n'
old3_inner += indent_18 + '/>\n'
old3_inner += indent_16 + '</div>\n'
old3_inner += indent_14 + '</div>'

new3_inner = indent_14 + '<div>\n'
new3_inner += indent_16 + '<label class="block text-xs text-[#5a6a80] mb-1">背景色</label>\n'
new3_inner += indent_16 + '<div class="flex items-center gap-0 rounded-md border border-[#1e293b] overflow-hidden">\n'
new3_inner += indent_18 + '<input\n'
new3_inner += indent_20 + 'type="color"\n'
new3_inner += indent_20 + ':value="localStyles.backgroundColor || \'transparent\'"\n'
new3_inner += indent_20 + '@input="handleColorInput($event, v => { localStyles.backgroundColor = v; applyStyles() })"\n'
new3_inner += indent_20 + 'class="w-10 h-8 cursor-pointer border-0 p-0.5 bg-transparent"\n'
new3_inner += indent_20 + 'style="flex-shrink: 0; min-width: 40px;"\n'
new3_inner += indent_18 + '/>\n'
new3_inner += indent_18 + '<input\n'
new3_inner += indent_20 + ':value="localStyles.backgroundColor || \'\'"\n'
new3_inner += indent_20 + '@input="handleColorInput($event, v => { localStyles.backgroundColor = v || undefined; applyStyles() })"\n'
new3_inner += indent_20 + 'class="flex-1 h-8 px-2.5 text-xs text-white font-mono outline-none bg-[#112240]"\n'
new3_inner += indent_20 + 'style="border: none !important;"\n'
new3_inner += indent_20 + 'placeholder="transparent"\n'
new3_inner += indent_18 + '/>\n'
new3_inner += indent_16 + '</div>\n'
new3_inner += indent_14 + '</div>'

# === Section 4: 边框与圆角 - 边框颜色 (lines 571-588) ===
old4_inner = indent_14 + '<div>\n'
old4_inner += indent_16 + '<label class="block text-xs text-[#5a6a80] mb-1">边框颜色</label>\n'
old4_inner += indent_16 + '<div class="flex items-center gap-2">\n'
old4_inner += indent_18 + '<div class="relative w-8 h-8 rounded cursor-pointer overflow-hidden border border-[#1e293b]">\n'
old4_inner += indent_20 + '<div class="absolute inset-0 rounded" :style="{ backgroundColor: localStyles.borderColor || \'transparent\' }"></div>\n'
old4_inner += indent_20 + '<input\n'
old4_inner += indent_22 + 'type="color"\n'
old4_inner += indent_22 + ':value="localStyles.borderColor || \'transparent\'"\n'
old4_inner += indent_22 + '@input="handleColorInput($event, v => { localStyles.borderColor = v; applyStyles() })"\n'
old4_inner += indent_22 + 'class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"\n'
old4_inner += indent_20 + '/>\n'
old4_inner += indent_18 + '</div>\n'
old4_inner += indent_18 + '<input\n'
old4_inner += indent_20 + ':value="localStyles.borderColor || \'\'"\n'
old4_inner += indent_20 + '@input="handleColorInput($event, v => { localStyles.borderColor = v || undefined; applyStyles() })"\n'
old4_inner += indent_20 + 'class="flex-1 h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white font-mono outline-none focus:border-[#00d9ff] transition-colors"\n'
old4_inner += indent_20 + 'placeholder="transparent"\n'
old4_inner += indent_18 + '/>\n'
old4_inner += indent_16 + '</div>\n'
old4_inner += indent_14 + '</div>'

new4_inner = indent_14 + '<div>\n'
new4_inner += indent_16 + '<label class="block text-xs text-[#5a6a80] mb-1">边框颜色</label>\n'
new4_inner += indent_16 + '<div class="flex items-center gap-0 rounded-md border border-[#1e293b] overflow-hidden">\n'
new4_inner += indent_18 + '<input\n'
new4_inner += indent_20 + 'type="color"\n'
new4_inner += indent_20 + ':value="localStyles.borderColor || \'transparent\'"\n'
new4_inner += indent_20 + '@input="handleColorInput($event, v => { localStyles.borderColor = v; applyStyles() })"\n'
new4_inner += indent_20 + 'class="w-10 h-8 cursor-pointer border-0 p-0.5 bg-transparent"\n'
new4_inner += indent_20 + 'style="flex-shrink: 0; min-width: 40px;"\n'
new4_inner += indent_18 + '/>\n'
new4_inner += indent_18 + '<input\n'
new4_inner += indent_20 + ':value="localStyles.borderColor || \'\'"\n'
new4_inner += indent_20 + '@input="handleColorInput($event, v => { localStyles.borderColor = v || undefined; applyStyles() })"\n'
new4_inner += indent_20 + 'class="flex-1 h-8 px-2.5 text-xs text-white font-mono outline-none bg-[#112240]"\n'
new4_inner += indent_20 + 'style="border: none !important;"\n'
new4_inner += indent_20 + 'placeholder="transparent"\n'
new4_inner += indent_18 + '/>\n'
new4_inner += indent_16 + '</div>\n'
new4_inner += indent_14 + '</div>'

pairs = [
    ("背景颜色", old1, new1),
    ("颜色", old2_inner, new2_inner),
    ("背景色", old3_inner, new3_inner),
    ("边框颜色", old4_inner, new4_inner),
]

count = 0
for label, old_text, new_text in pairs:
    if old_text in content:
        content = content.replace(old_text, new_text, 1)
        count += 1
        print("[OK] Section '{}' replaced".format(label))
    else:
        print("[FAIL] Section '{}' NOT FOUND".format(label))
        # Debug: show what we're looking for
        print("  First line: {}".format(repr(old_text.split('\n')[0])))

if count > 0:
    with open(r'D:\FluxAvision\FluxAvision_Kly\frontend-vue\src\components\large-screen\designer\PropertyPanel.vue', 'w', encoding='utf-8', newline='') as f:
        f.write(content)
    print("\nFile written. {} replacements done.".format(count))
else:
    print("\nNo replacements done - file unchanged.")
