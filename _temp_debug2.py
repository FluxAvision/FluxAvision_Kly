import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'D:\FluxAvision\FluxAvision_Kly\frontend-vue\src\components\large-screen\designer\PropertyPanel.vue', encoding='utf-8') as f:
    lines = f.readlines()

targets = [295, 489, 544, 577]
for t in targets:
    print(f"\n=== Around line {t} ===")
    for i in range(max(0,t-15), min(len(lines),t+10)):
        marker = " <-- type=color" if i+1 == t else ""
        # Show exact character repr
        print(f"L{i+1:3d}: {repr(lines[i])}{marker}")
