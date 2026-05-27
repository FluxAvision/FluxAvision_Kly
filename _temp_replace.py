import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open(r'D:\FluxAvision\FluxAvision_Kly\frontend-vue\src\components\large-screen\designer\PropertyPanel.vue', encoding='utf-8') as f:
    content = f.read()

# === Section 1: 背景 - 背景颜色 (template edit mode) ===
old1 = '''          <div>
            <label class="block text-xs text-[#5a6a80] mb-1">背景颜色</label>
            <div class="flex items-center gap-2">
              <div class="relative w-8 h-8 rounded cursor-pointer overflow-hidden border border-[#1e293b]">
                <div class="absolute inset-0 rounded" :style="{ backgroundColor: localCanvasBg }"></div>
                <input
                  type="color"
                  :value="localCanvasBg"
                  @input="handleColorInput($event, v => { localCanvasBg = v; applyCanvasConfig() })"
                  class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
              </div>
              <input
                :value="localCanvasBg"
                @input="handleColorInput($event, v => { localCanvasBg = v; applyCanvasConfig() })"
                class="flex-1 h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white font-mono outline-none focus:border-[#00d9ff] transition-colors"
              />
            </div>
          </div>'''

new1 = '''          <div>
            <label class="block text-xs text-[#5a6a80] mb-1">背景颜色</label>
            <div class="flex items-center gap-0 rounded-md border border-[#1e293b] overflow-hidden">
              <input
                type="color"
                :value="localCanvasBg"
                @input="handleColorInput($event, v => { localCanvasBg = v; applyCanvasConfig() })"
                class="w-10 h-8 cursor-pointer border-0 p-0.5 bg-transparent"
                style="flex-shrink: 0; min-width: 40px;"
              />
              <input
                :value="localCanvasBg"
                @input="handleColorInput($event, v => { localCanvasBg = v; applyCanvasConfig() })"
                class="flex-1 h-8 px-2.5 text-xs text-white font-mono outline-none bg-[#112240]"
                style="border: none !important;"
              />
            </div>
          </div>'''

# === Section 2: 排版 - 颜色 ===
old2 = '''              <div>
                <label class="block text-xs text-[#5a6a80] mb-1">颜色</label>
                <div class="flex items-center gap-2">
                  <div class="relative w-8 h-8 rounded cursor-pointer overflow-hidden border border-[#1e293b]">
                    <div class="absolute inset-0 rounded" :style="{ backgroundColor: localStyles.color || '#ffffff' }"></div>
                    <input
                      type="color"
                      :value="localStyles.color || '#ffffff'"
                      @input="handleColorInput($event, v => { localStyles.color = v; applyStyles() })"
                      class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />
                  </div>
                  <input
                    :value="localStyles.color || ''"
                    @input="handleColorInput($event, v => { localStyles.color = v; applyStyles() })"
                    class="flex-1 h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white font-mono outline-none focus:border-[#00d9ff] transition-colors"
                    placeholder="#ffffff"
                  />
                </div>
              </div>'''

new2 = '''              <div>
                <label class="block text-xs text-[#5a6a80] mb-1">颜色</label>
                <div class="flex items-center gap-0 rounded-md border border-[#1e293b] overflow-hidden">
                  <input
                    type="color"
                    :value="localStyles.color || '#ffffff'"
                    @input="handleColorInput($event, v => { localStyles.color = v; applyStyles() })"
                    class="w-10 h-8 cursor-pointer border-0 p-0.5 bg-transparent"
                    style="flex-shrink: 0; min-width: 40px;"
                  />
                  <input
                    :value="localStyles.color || ''"
                    @input="handleColorInput($event, v => { localStyles.color = v; applyStyles() })"
                    class="flex-1 h-8 px-2.5 text-xs text-white font-mono outline-none bg-[#112240]"
                    style="border: none !important;"
                    placeholder="#ffffff"
                  />
                </div>
              </div>'''

# === Section 3: 边框与圆角 - 背景色 ===
old3 = '''              <div>
                <label class="block text-xs text-[#5a6a80] mb-1">背景色</label>
                <div class="flex items-center gap-2">
                  <div class="relative w-8 h-8 rounded cursor-pointer overflow-hidden border border-[#1e293b]">
                    <div class="absolute inset-0 rounded" :style="{ backgroundColor: localStyles.backgroundColor || 'transparent' }"></div>
                    <input
                      type="color"
                      :value="localStyles.backgroundColor || 'transparent'"
                      @input="handleColorInput($event, v => { localStyles.backgroundColor = v; applyStyles() })"
                      class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />
                  </div>
                  <input
                    :value="localStyles.backgroundColor || ''"
                    @input="handleColorInput($event, v => { localStyles.backgroundColor = v || undefined; applyStyles() })"
                    class="flex-1 h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white font-mono outline-none focus:border-[#00d9ff] transition-colors"
                    placeholder="transparent"
                  />
                </div>
              </div>'''

new3 = '''              <div>
                <label class="block text-xs text-[#5a6a80] mb-1">背景色</label>
                <div class="flex items-center gap-0 rounded-md border border-[#1e293b] overflow-hidden">
                  <input
                    type="color"
                    :value="localStyles.backgroundColor || 'transparent'"
                    @input="handleColorInput($event, v => { localStyles.backgroundColor = v; applyStyles() })"
                    class="w-10 h-8 cursor-pointer border-0 p-0.5 bg-transparent"
                    style="flex-shrink: 0; min-width: 40px;"
                  />
                  <input
                    :value="localStyles.backgroundColor || ''"
                    @input="handleColorInput($event, v => { localStyles.backgroundColor = v || undefined; applyStyles() })"
                    class="flex-1 h-8 px-2.5 text-xs text-white font-mono outline-none bg-[#112240]"
                    style="border: none !important;"
                    placeholder="transparent"
                  />
                </div>
              </div>'''

# === Section 4: 边框与圆角 - 边框颜色 ===
old4 = '''              <div>
                <label class="block text-xs text-[#5a6a80] mb-1">边框颜色</label>
                <div class="flex items-center gap-2">
                  <div class="relative w-8 h-8 rounded cursor-pointer overflow-hidden border border-[#1e293b]">
                    <div class="absolute inset-0 rounded" :style="{ backgroundColor: localStyles.borderColor || 'transparent' }"></div>
                    <input
                      type="color"
                      :value="localStyles.borderColor || 'transparent'"
                      @input="handleColorInput($event, v => { localStyles.borderColor = v; applyStyles() })"
                      class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />
                  </div>
                  <input
                    :value="localStyles.borderColor || ''"
                    @input="handleColorInput($event, v => { localStyles.borderColor = v || undefined; applyStyles() })"
                    class="flex-1 h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white font-mono outline-none focus:border-[#00d9ff] transition-colors"
                    placeholder="transparent"
                  />
                </div>
              </div>'''

new4 = '''              <div>
                <label class="block text-xs text-[#5a6a80] mb-1">边框颜色</label>
                <div class="flex items-center gap-0 rounded-md border border-[#1e293b] overflow-hidden">
                  <input
                    type="color"
                    :value="localStyles.borderColor || 'transparent'"
                    @input="handleColorInput($event, v => { localStyles.borderColor = v; applyStyles() })"
                    class="w-10 h-8 cursor-pointer border-0 p-0.5 bg-transparent"
                    style="flex-shrink: 0; min-width: 40px;"
                  />
                  <input
                    :value="localStyles.borderColor || ''"
                    @input="handleColorInput($event, v => { localStyles.borderColor = v || undefined; applyStyles() })"
                    class="flex-1 h-8 px-2.5 text-xs text-white font-mono outline-none bg-[#112240]"
                    style="border: none !important;"
                    placeholder="transparent"
                  />
                </div>
              </div>'''

count = 0
for i, (old_text, new_text) in enumerate([(old1, new1), (old2, new2), (old3, new3), (old4, new4)]):
    if old_text in content:
        content = content.replace(old_text, new_text, 1)
        count += 1
        print("[OK] Section {} replaced".format(i+1))
    else:
        print("[FAIL] Section {} not found!".format(i+1))

if count > 0:
    with open(r'D:\FluxAvision\FluxAvision_Kly\frontend-vue\src\components\large-screen\designer\PropertyPanel.vue', 'w', encoding='utf-8', newline='') as f:
        f.write(content)
    print("\nFile written. {} replacements done.".format(count))
else:
    print("\nNo replacements done - file unchanged.")
