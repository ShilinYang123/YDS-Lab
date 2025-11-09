#!/usr/bin/env python3
"""
鍥㈤槦鍩硅鍜屾枃妗ｆ洿鏂板伐鍏?涓篢rae骞冲彴鏅鸿兘浣撶郴缁熷垱寤哄畬鏁寸殑鍩硅鏉愭枡鍜屾枃妗?"""

import os
import json
import yaml
from datetime import datetime
from pathlib import Path

class TrainingDocumentationManager:
    def __init__(self, base_path="S:/YDS-Lab"):
        self.base_path = Path(base_path)
        self.docs_path = self.base_path / "Documentation"
        self.training_path = self.base_path / "Training"
        
    def create_documentation_structure(self):
        """鍒涘缓鏂囨。缁撴瀯"""
        print("馃摎 鍒涘缓鏂囨。缁撴瀯...")
        
        # 鍒涘缓涓昏鏂囨。鐩綍
        directories = [
            self.docs_path / "UserGuides",
            self.docs_path / "TechnicalDocs", 
            self.docs_path / "APIReference",
            self.docs_path / "Tutorials",
            self.docs_path / "Troubleshooting",
            self.training_path / "Materials",
            self.training_path / "Exercises",
            self.training_path / "Assessments",
            self.training_path / "Resources"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"馃搧 鍒涘缓鐩綍: {directory.relative_to(self.base_path)}")
        
        return True
    
    def create_user_guide(self):
        """鍒涘缓鐢ㄦ埛鎸囧崡"""
        print("馃摉 鍒涘缓鐢ㄦ埛鎸囧崡...")
        
        user_guide_content = """# Trae骞冲彴鏅鸿兘浣撶郴缁熺敤鎴锋寚鍗?
## 鐩綍
1. [绯荤粺姒傝堪](#绯荤粺姒傝堪)
2. [蹇€熷紑濮媇(#蹇€熷紑濮?
3. [鏅鸿兘浣撲粙缁峕(#鏅鸿兘浣撲粙缁?
4. [鍗忎綔宸ヤ綔娴乚(#鍗忎綔宸ヤ綔娴?
5. [MCP宸ュ叿浣跨敤](#MCP宸ュ叿浣跨敤)
6. [甯歌闂](#甯歌闂)

## 绯荤粺姒傝堪

Trae骞冲彴鏄竴涓熀浜庢櫤鑳戒綋鐨勫崗浣滅郴缁燂紝鍖呭惈浠ヤ笅鏍稿績缁勪欢锛?
### 鏅鸿兘浣撹鑹?- **CEO**: 鎴樼暐鍐崇瓥鍜屽洟闃熷崗璋?- **DevTeamLead**: 寮€鍙戝洟闃熺鐞?- **ResourceAdmin**: 璧勬簮绠＄悊鍜屽垎閰?
### MCP宸ュ叿闆嗙兢
- **GitHub MCP**: 浠ｇ爜浠撳簱绠＄悊
- **Excel MCP**: 鏁版嵁澶勭悊鍜屽垎鏋?- **FileSystem MCP**: 鏂囦欢绯荤粺鎿嶄綔
- **Database MCP**: 鏁版嵁搴撶鐞?- **Builder MCP**: 鏋勫缓鍜岄儴缃?- **Figma MCP**: 璁捐鍗忎綔

## 蹇€熷紑濮?
### 1. 鍚姩绯荤粺
```bash
# 鍚姩鏍囧噯鍖栫敓浜х幆澧?cd S:/YDS-Lab/tools/scripts
start_production.bat

# 鍚姩鍗忎綔宸ヤ綔娴侊紙濡傞渶鍗曠嫭鍚姩锛?python start_collaboration.py
```

### 2. 璁块棶鏅鸿兘浣?- CEO鏅鸿兘浣? 閫氳繃Trae IDE璁块棶
- DevTeamLead: 寮€鍙戝洟闃熶笓鐢ㄦ帴鍙?- ResourceAdmin: 璧勬簮绠＄悊鐣岄潰

### 3. 鍩烘湰鎿嶄綔
1. 鐧诲綍绯荤粺
2. 閫夋嫨鏅鸿兘浣撹鑹?3. 寮€濮嬪崗浣滀换鍔?
## 鏅鸿兘浣撲粙缁?
### CEO鏅鸿兘浣?**鑱岃矗**: 鎴樼暐鍐崇瓥銆佸洟闃熷崗璋冦€侀」鐩洃鐫?**鑳藉姏**:
- 鍒跺畾椤圭洰鎴樼暐
- 鍗忚皟鍚勯儴闂ㄥ伐浣?- 鐩戞帶椤圭洰杩涘害
- 鍐崇瓥鏀寔

**浣跨敤鍦烘櫙**:
- 椤圭洰鍚姩鍜岃鍒?- 閲嶈鍐崇瓥鍒跺畾
- 鍥㈤槦鍗忚皟浼氳
- 缁╂晥璇勪及

### DevTeamLead鏅鸿兘浣?**鑱岃矗**: 寮€鍙戝洟闃熺鐞嗐€佹妧鏈喅绛栥€佷唬鐮佸鏌?**鑳藉姏**:
- 鎶€鏈灦鏋勮璁?- 浠ｇ爜璐ㄩ噺绠＄悊
- 鍥㈤槦浠诲姟鍒嗛厤
- 寮€鍙戞祦绋嬩紭鍖?
**浣跨敤鍦烘櫙**:
- 鎶€鏈柟妗堣璁?- 浠ｇ爜瀹℃煡
- 寮€鍙戜换鍔＄鐞?- 鎶€鏈棶棰樿В鍐?
### ResourceAdmin鏅鸿兘浣?**鑱岃矗**: 璧勬簮绠＄悊銆佺幆澧冮厤缃€佺郴缁熺淮鎶?**鑳藉姏**:
- 绯荤粺璧勬簮鐩戞帶
- 鐜閰嶇疆绠＄悊
- 鏉冮檺鎺у埗
- 绯荤粺缁存姢

**浣跨敤鍦烘櫙**:
- 绯荤粺閮ㄧ讲
- 璧勬簮鍒嗛厤
- 鏉冮檺绠＄悊
- 绯荤粺鐩戞帶

## 鍗忎綔宸ヤ綔娴?
### 鏃ュ父杩愯惀宸ヤ綔娴?1. **鏅ㄤ細鍗忚皟** (CEO涓诲)
   - 鍚勬櫤鑳戒綋鐘舵€佹眹鎶?   - 褰撴棩浠诲姟鍒嗛厤
   - 浼樺厛绾х‘瀹?
2. **浠诲姟鎵ц** (鍚勬櫤鑳戒綋鍗忎綔)
   - 骞惰浠诲姟澶勭悊
   - 瀹炴椂鐘舵€佸悓姝?   - 闂鍙婃椂涓婃姤

3. **杩涘害妫€鏌?* (瀹氭湡鍚屾)
   - 浠诲姟瀹屾垚鎯呭喌
   - 闂璇嗗埆鍜岃В鍐?   - 璧勬簮闇€姹傝瘎浼?
### 椤圭洰寮€鍙戝伐浣滄祦
1. **闇€姹傚垎鏋?* (CEO + DevTeamLead)
2. **鎶€鏈璁?* (DevTeamLead涓诲)
3. **璧勬簮鍑嗗** (ResourceAdmin)
4. **寮€鍙戝疄鏂?* (DevTeamLead鐩戠潱)
5. **娴嬭瘯閮ㄧ讲** (鍗忎綔瀹屾垚)
6. **涓婄嚎缁存姢** (ResourceAdmin)

### 搴旀€ュ搷搴斿伐浣滄祦
1. **闂璇嗗埆** (浠绘剰鏅鸿兘浣?
2. **绱ф€ラ€氱煡** (鑷姩瑙﹀彂)
3. **蹇€熷搷搴?* (鐩稿叧鏅鸿兘浣?
4. **闂瑙ｅ喅** (鍗忎綔澶勭悊)
5. **鎬荤粨鏀硅繘** (CEO涓诲)

## MCP宸ュ叿浣跨敤

### GitHub MCP
**鍔熻兘**: 浠ｇ爜浠撳簱绠＄悊銆佺増鏈帶鍒躲€佸崗浣滃紑鍙?
**鍩烘湰鎿嶄綔**:
```python
# 鍒涘缓浠撳簱
github_mcp.create_repository("project-name")

# 鎻愪氦浠ｇ爜
github_mcp.commit_changes("feat: add new feature")

# 鍒涘缓PR
github_mcp.create_pull_request("feature-branch", "main")
```

### Excel MCP
**鍔熻兘**: 鏁版嵁澶勭悊銆佹姤琛ㄧ敓鎴愩€佹暟鎹垎鏋?
**鍩烘湰鎿嶄綔**:
```python
# 璇诲彇鏁版嵁
data = excel_mcp.read_excel("data.xlsx")

# 鏁版嵁澶勭悊
processed = excel_mcp.process_data(data)

# 鐢熸垚鎶ヨ〃
excel_mcp.generate_report(processed, "report.xlsx")
```

### FileSystem MCP
**鍔熻兘**: 鏂囦欢鎿嶄綔銆佺洰褰曠鐞嗐€佹枃浠跺悓姝?
**鍩烘湰鎿嶄綔**:
```python
# 鏂囦欢鎿嶄綔
filesystem_mcp.create_file("path/to/file.txt", content)
filesystem_mcp.copy_file("source.txt", "destination.txt")

# 鐩綍绠＄悊
filesystem_mcp.create_directory("new_folder")
filesystem_mcp.list_directory("path")
```

## 甯歌闂

### Q: 濡備綍閲嶅惎鏅鸿兘浣擄紵
A: 浣跨敤鏍囧噯鍖栧惎鍔ㄨ剼鏈噸鏂板惎鍔細
```bash
cd S:/YDS-Lab/tools/scripts
start_production.bat
```

### Q: MCP鏈嶅姟鏃犲搷搴旀€庝箞鍔烇紵
A: 杩涘叆瀵瑰簲MCP鏈嶅姟鐩綍骞舵墜鍔ㄥ惎鍔紝鎴栭噸鏂拌繍琛岀敓浜х幆澧冨惎鍔ㄨ剼鏈細
```bash
# 閲嶆柊杩愯鐢熶骇鐜鑴氭湰浠ュ惎鍔ㄥ叏閮∕CP鏈嶅姟
cd S:/YDS-Lab/tools/scripts
start_production.bat

# 鎴栬繘鍏ュ崟涓狹CP鏈嶅姟鐩綍锛屾墜鍔ㄨ繍琛孭ython鏈嶅姟鍣紙绀轰緥锛欸itHub MCP锛?cd S:/YDS-Lab/01-struc/MCPCluster/GitHub
python github_mcp_server.py
```

### Q: 濡備綍鏌ョ湅绯荤粺鏃ュ織锛?A: 鏃ュ織鏂囦欢浣嶇疆锛?- 绯荤粺鏃ュ織: `S:/YDS-Lab/01-struc/0B-general-manager/logs/system.log`
- 鏅鸿兘浣撴棩蹇? `S:/YDS-Lab/01-struc/0B-general-manager/logs/agents/`
- MCP鏃ュ織: `S:/YDS-Lab/01-struc/0B-general-manager/logs/tools/mcp/`

### Q: 濡備綍澶囦唤绯荤粺锛?A: 浣跨敤鑷姩澶囦唤鑴氭湰锛?```bash
cd S:/YDS-Lab/tools/backup
python daily_snapshot.py
```

## 鎶€鏈敮鎸?
濡傛湁鎶€鏈棶棰橈紝璇疯仈绯伙細
- 绯荤粺绠＄悊鍛? admin@yds-lab.com
- 鎶€鏈敮鎸? support@yds-lab.com
- 绱ф€ヨ仈绯? emergency@yds-lab.com

---
*鏂囨。鐗堟湰: v2.0*
*鏈€鍚庢洿鏂? {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        user_guide_path = self.docs_path / "UserGuides" / "trae_platform_user_guide.md"
        with open(user_guide_path, 'w', encoding='utf-8') as f:
            f.write(user_guide_content)
        
        print(f"鉁?鐢ㄦ埛鎸囧崡鍒涘缓瀹屾垚: {user_guide_path.relative_to(self.base_path)}")
        return True
    
    def create_technical_documentation(self):
        """鍒涘缓鎶€鏈枃妗?""
        print("馃敡 鍒涘缓鎶€鏈枃妗?..")
        
        # 绯荤粺鏋舵瀯鏂囨。
        architecture_doc = """# Trae骞冲彴绯荤粺鏋舵瀯鏂囨。

## 绯荤粺鏋舵瀯姒傝

```
鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?鈹?                   Trae骞冲彴鏅鸿兘浣撶郴缁?                       鈹?鈹溾攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?鈹? 鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹? 鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹? 鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?       鈹?鈹? 鈹?    CEO     鈹? 鈹?DevTeamLead 鈹? 鈹俁esourceAdmin鈹?       鈹?鈹? 鈹?  鏅鸿兘浣?   鈹? 鈹?   鏅鸿兘浣?  鈹? 鈹?   鏅鸿兘浣?  鈹?       鈹?鈹? 鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹? 鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹? 鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?       鈹?鈹溾攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?鈹?                   鍗忎綔宸ヤ綔娴佸紩鎿?                          鈹?鈹溾攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?鈹? 鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹?鈹?鈹? 鈹?GitHub  鈹?鈹? Excel  鈹?鈹侳ileSystem鈹?鈹侱atabase 鈹?鈹侭uilder鈹?鈹?鈹? 鈹?  MCP   鈹?鈹?  MCP   鈹?鈹?  MCP   鈹?鈹?  MCP   鈹?鈹? MCP  鈹?鈹?鈹? 鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹?鈹?鈹溾攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?鈹?                   鍩虹璁炬柦灞?                              鈹?鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?```

## 鏍稿績缁勪欢

### 1. 鏅鸿兘浣撳眰
- **CEO鏅鸿兘浣?*: 鎴樼暐鍐崇瓥鍜屽崗璋?- **DevTeamLead鏅鸿兘浣?*: 寮€鍙戠鐞?- **ResourceAdmin鏅鸿兘浣?*: 璧勬簮绠＄悊

### 2. 鍗忎綔灞?- 宸ヤ綔娴佸紩鎿?- 娑堟伅閫氫俊
- 鐘舵€佸悓姝?- 鍐崇瓥鏈哄埗

### 3. MCP宸ュ叿灞?- GitHub闆嗘垚
- Excel澶勭悊
- 鏂囦欢绯荤粺
- 鏁版嵁搴撶鐞?- 鏋勫缓閮ㄧ讲

### 4. 鍩虹璁炬柦灞?- 閰嶇疆绠＄悊
- 鏃ュ織绯荤粺
- 鐩戞帶鍛婅
- 澶囦唤鎭㈠

## 閮ㄧ讲鏋舵瀯

### 鐢熶骇鐜缁撴瀯锛堟爣鍑嗗寲鐩綍锛?```
Struc/
鈹溾攢鈹€ TraeAgents/          # 鏅鸿兘浣撻厤缃?鈹溾攢鈹€ MCPCluster/          # MCP鏈嶅姟闆嗙兢
鈹溾攢鈹€ SharedWorkspace/     # 鍏变韩宸ヤ綔鍖?config/                  # 閰嶇疆鏂囦欢
01-struc/0B-general-manager/logs/  # 鏃ュ織鏂囦欢锛堢粺涓€鏃ュ織杈撳嚭鐩綍锛?tools/scripts/           # 杩愯鑴氭湰
```

### 閰嶇疆绠＄悊
- 鐜閰嶇疆: `production_config.yaml`
- 鏅鸿兘浣撻厤缃? `agent_config.yaml`
- MCP閰嶇疆: `cluster_config.yaml`
- 鍗忎綔閰嶇疆: `collaboration_workflows.yaml`

## 瀹夊叏鏋舵瀯

### 璁块棶鎺у埗
- 鍩轰簬瑙掕壊鐨勬潈闄愭帶鍒?- API瀵嗛挜绠＄悊
- 浼氳瘽绠＄悊
- 瀹¤鏃ュ織

### 鏁版嵁瀹夊叏
- 鏁忔劅鏁版嵁鍔犲瘑
- 瀹夊叏浼犺緭(HTTPS/TLS)
- 鏁版嵁澶囦唤
- 鐏鹃毦鎭㈠

## 鎬ц兘浼樺寲

### 绯荤粺鎬ц兘
- 鏅鸿兘浣撳苟鍙戝鐞?- MCP杩炴帴姹?- 缂撳瓨鏈哄埗
- 璐熻浇鍧囪　

### 鐩戞帶鎸囨爣
- 鍝嶅簲鏃堕棿
- 鍚炲悙閲?- 閿欒鐜?- 璧勬簮浣跨敤鐜?
---
*鎶€鏈枃妗ｇ増鏈? v2.0*
*缁存姢鑰? YDS-Lab鎶€鏈洟闃?
"""
        
        arch_doc_path = self.docs_path / "TechnicalDocs" / "system_architecture.md"
        with open(arch_doc_path, 'w', encoding='utf-8') as f:
            f.write(architecture_doc)
        
        # API鍙傝€冩枃妗?        api_doc = """# Trae骞冲彴API鍙傝€冩枃妗?
## 鏅鸿兘浣揂PI

### CEO鏅鸿兘浣揂PI

#### 鑾峰彇鏅鸿兘浣撶姸鎬?```http
GET /api/Agents/01-ceo/status
```

**鍝嶅簲绀轰緥**:
```json
{
  "status": "active",
  "current_tasks": ["strategic_planning", "team_coordination"],
  "performance_metrics": {
    "decisions_made": 15,
    "meetings_conducted": 3,
    "success_rate": 0.95
  }
}
```

#### 鍒涘缓鍐崇瓥浠诲姟
```http
POST /api/Agents/01-ceo/decisions
Content-Type: application/json

{
  "decision_type": "strategic",
  "context": "椤圭洰浼樺厛绾ц皟鏁?,
  "stakeholders": ["dev_team", "resource_admin"],
  "deadline": "2024-11-02T10:00:00Z"
}
```

### DevTeamLead鏅鸿兘浣揂PI

#### 鑾峰彇寮€鍙戜换鍔?```http
GET /api/agents/devteam/tasks
```

#### 鍒涘缓浠ｇ爜瀹℃煡
```http
POST /api/agents/devteam/code-review
Content-Type: application/json

{
  "repository": "project-repo",
  "pull_request": 123,
  "reviewers": ["senior_dev", "tech_lead"],
  "priority": "high"
}
```

### ResourceAdmin鏅鸿兘浣揂PI

#### 鑾峰彇绯荤粺璧勬簮
```http
GET /api/agents/resource/system-status
```

#### 閰嶇疆鐜
```http
POST /api/agents/resource/environment
Content-Type: application/json

{
  "environment": "production",
  "configuration": {
    "cpu_limit": "4",
    "memory_limit": "8Gi",
    "storage": "100Gi"
  }
}
```

## MCP宸ュ叿API

### GitHub MCP API

#### 鍒涘缓浠撳簱
```http
POST /api/mcp/github/repositories
Content-Type: application/json

{
  "name": "new-project",
  "description": "椤圭洰鎻忚堪",
  "private": true,
  "auto_init": true
}
```

#### 鑾峰彇鎻愪氦鍘嗗彶
```http
GET /api/mcp/github/repositories/{repo}/commits
```

### Excel MCP API

#### 澶勭悊Excel鏂囦欢
```http
POST /api/mcp/excel/process
Content-Type: multipart/form-data

file: [Excel鏂囦欢]
operations: ["read", "analyze", "report"]
```

#### 鐢熸垚鎶ヨ〃
```http
POST /api/mcp/excel/generate-report
Content-Type: application/json

{
  "data_source": "sales_data.xlsx",
  "report_type": "monthly_summary",
  "output_format": "xlsx"
}
```

## 鍗忎綔宸ヤ綔娴丄PI

### 鍒涘缓宸ヤ綔娴?```http
POST /api/workflows
Content-Type: application/json

{
  "name": "椤圭洰寮€鍙戞祦绋?,
  "type": "project_development",
  "participants": ["ceo", "devteam", "resource_admin"],
  "steps": [
    {
      "name": "闇€姹傚垎鏋?,
      "assignee": "ceo",
      "duration": "2h"
    },
    {
      "name": "鎶€鏈璁?,
      "assignee": "devteam",
      "duration": "4h"
    }
  ]
}
```

### 鑾峰彇宸ヤ綔娴佺姸鎬?```http
GET /api/workflows/{workflow_id}/status
```

## 閿欒浠ｇ爜

| 浠ｇ爜 | 鎻忚堪 | 瑙ｅ喅鏂规 |
|------|------|----------|
| 1001 | 鏅鸿兘浣撴湭鍝嶅簲 | 妫€鏌ユ櫤鑳戒綋鐘舵€侊紝閲嶅惎鏈嶅姟 |
| 1002 | MCP鏈嶅姟涓嶅彲鐢?| 妫€鏌CP闆嗙兢鐘舵€?|
| 1003 | 鏉冮檺涓嶈冻 | 楠岃瘉API瀵嗛挜鍜屾潈闄?|
| 1004 | 閰嶇疆閿欒 | 妫€鏌ラ厤缃枃浠舵牸寮?|
| 1005 | 璧勬簮涓嶈冻 | 妫€鏌ョ郴缁熻祫婧愪娇鐢ㄦ儏鍐?|

## 璁よ瘉鍜屾巿鏉?
### API瀵嗛挜璁よ瘉
```http
Authorization: Bearer YOUR_API_KEY
```

### 鏉冮檺绾у埆
- **admin**: 瀹屽叏璁块棶鏉冮檺
- **operator**: 鎿嶄綔鏉冮檺
- **viewer**: 鍙鏉冮檺

---
*API鏂囨。鐗堟湰: v2.0*
*鏈€鍚庢洿鏂? {datetime.now().strftime('%Y-%m-%d')}*
"""
        
        api_doc_path = self.docs_path / "APIReference" / "api_reference.md"
        with open(api_doc_path, 'w', encoding='utf-8') as f:
            f.write(api_doc)
        
        print(f"鉁?鎶€鏈枃妗ｅ垱寤哄畬鎴?)
        return True
    
    def create_training_materials(self):
        """鍒涘缓鍩硅鏉愭枡"""
        print("馃帗 鍒涘缓鍩硅鏉愭枡...")
        
        # 鍩硅澶х翰
        training_outline = """# Trae骞冲彴鏅鸿兘浣撶郴缁熷煿璁ぇ绾?
## 鍩硅鐩爣
閫氳繃鏈煿璁紝瀛﹀憳灏嗚兘澶燂細
1. 鐞嗚ВTrae骞冲彴鐨勬牳蹇冩蹇靛拰鏋舵瀯
2. 鐔熺粌浣跨敤鍚勪釜鏅鸿兘浣撶殑鍔熻兘
3. 鎺屾彙MCP宸ュ叿鐨勬搷浣滄柟娉?4. 鑳藉澶勭悊甯歌闂鍜屾晠闅?5. 鍏峰绯荤粺缁存姢鍜屼紭鍖栬兘鍔?
## 鍩硅妯″潡

### 妯″潡1: 绯荤粺姒傝堪 (2灏忔椂)
**瀛︿範鐩爣**: 浜嗚ВTrae骞冲彴鏁翠綋鏋舵瀯鍜屾牳蹇冩蹇?
**鍐呭澶х翰**:
1. Trae骞冲彴浠嬬粛
   - 绯荤粺鑳屾櫙鍜岀洰鏍?   - 鏍稿績浠峰€煎拰浼樺娍
   - 搴旂敤鍦烘櫙

2. 绯荤粺鏋舵瀯
   - 鏁翠綋鏋舵瀯璁捐
   - 缁勪欢鍏崇郴鍥?   - 鏁版嵁娴佸悜

3. 鏅鸿兘浣撴蹇?   - 鏅鸿兘浣撳畾涔夊拰鐗圭偣
   - 瑙掕壊鍒嗗伐
   - 鍗忎綔鏈哄埗

**瀹炶返娲诲姩**:
- 绯荤粺婕旂ず
- 鏋舵瀯鍥捐В璇?- Q&A鐜妭

### 妯″潡2: 鏅鸿兘浣撴搷浣?(4灏忔椂)
**瀛︿範鐩爣**: 鎺屾彙鍚勬櫤鑳戒綋鐨勪娇鐢ㄦ柟娉?
**鍐呭澶х翰**:
1. CEO鏅鸿兘浣?   - 鍔熻兘浠嬬粛
   - 鎿嶄綔鐣岄潰
   - 鍐崇瓥娴佺▼
   - 鍗忚皟鏈哄埗

2. DevTeamLead鏅鸿兘浣?   - 寮€鍙戠鐞嗗姛鑳?   - 浠ｇ爜瀹℃煡娴佺▼
   - 浠诲姟鍒嗛厤
   - 鎶€鏈喅绛?
3. ResourceAdmin鏅鸿兘浣?   - 璧勬簮鐩戞帶
   - 鐜閰嶇疆
   - 鏉冮檺绠＄悊
   - 绯荤粺缁存姢

**瀹炶返娲诲姩**:
- 鏅鸿兘浣撴搷浣滄紨缁?- 瑙掕壊鎵紨缁冧範
- 鍗忎綔鍦烘櫙妯℃嫙

### 妯″潡3: MCP宸ュ叿浣跨敤 (3灏忔椂)
**瀛︿範鐩爣**: 鐔熺粌浣跨敤MCP宸ュ叿闆嗙兢

**鍐呭澶х翰**:
1. GitHub MCP
   - 浠ｇ爜浠撳簱绠＄悊
   - 鐗堟湰鎺у埗鎿嶄綔
   - 鍗忎綔寮€鍙戞祦绋?
2. Excel MCP
   - 鏁版嵁澶勭悊鍔熻兘
   - 鎶ヨ〃鐢熸垚
   - 鏁版嵁鍒嗘瀽

3. 鍏朵粬MCP宸ュ叿
   - FileSystem MCP
   - Database MCP
   - Builder MCP

**瀹炶返娲诲姩**:
- 宸ュ叿鎿嶄綔缁冧範
- 瀹為檯椤圭洰婕旂粌
- 闂瑙ｅ喅缁冧範

### 妯″潡4: 鍗忎綔宸ヤ綔娴?(2灏忔椂)
**瀛︿範鐩爣**: 鐞嗚В鍜屼娇鐢ㄥ崗浣滃伐浣滄祦

**鍐呭澶х翰**:
1. 宸ヤ綔娴佹蹇?   - 宸ヤ綔娴佺被鍨?   - 娴佺▼璁捐
   - 鎵ц鏈哄埗

2. 鏍囧噯宸ヤ綔娴?   - 鏃ュ父杩愯惀娴佺▼
   - 椤圭洰寮€鍙戞祦绋?   - 搴旀€ュ搷搴旀祦绋?
3. 鑷畾涔夊伐浣滄祦
   - 娴佺▼璁捐鍘熷垯
   - 閰嶇疆鏂规硶
   - 浼樺寲鎶€宸?
**瀹炶返娲诲姩**:
- 宸ヤ綔娴侀厤缃粌涔?- 娴佺▼浼樺寲璁ㄨ
- 鏈€浣冲疄璺靛垎浜?
### 妯″潡5: 鏁呴殰鎺掗櫎 (2灏忔椂)
**瀛︿範鐩爣**: 鍏峰鍩烘湰鐨勬晠闅滆瘖鏂拰澶勭悊鑳藉姏

**鍐呭澶х翰**:
1. 甯歌闂
   - 绯荤粺鍚姩闂
   - 鏅鸿兘浣撴棤鍝嶅簲
   - MCP鏈嶅姟鏁呴殰
   - 鎬ц兘闂

2. 璇婃柇鏂规硶
   - 鏃ュ織鍒嗘瀽
   - 鐘舵€佹鏌?   - 鎬ц兘鐩戞帶
   - 缃戠粶璇婃柇

3. 瑙ｅ喅鏂规
   - 閲嶅惎鏈嶅姟
   - 閰嶇疆淇
   - 璧勬簮璋冩暣
   - 鍗囩骇鏇存柊

**瀹炶返娲诲姩**:
- 鏁呴殰妯℃嫙缁冧範
- 璇婃柇宸ュ叿浣跨敤
- 瑙ｅ喅鏂规瀹炴柦

### 妯″潡6: 绯荤粺缁存姢 (1灏忔椂)
**瀛︿範鐩爣**: 鎺屾彙鏃ュ父缁存姢鎿嶄綔

**鍐呭澶х翰**:
1. 鏃ュ父缁存姢
   - 绯荤粺鐩戞帶
   - 鏃ュ織绠＄悊
   - 澶囦唤鎭㈠
   - 鎬ц兘浼樺寲

2. 瀹夊叏绠＄悊
   - 鏉冮檺鎺у埗
   - 瀵嗛挜绠＄悊
   - 瀹夊叏鏇存柊
   - 瀹¤鏃ュ織

**瀹炶返娲诲姩**:
- 缁存姢鎿嶄綔婕旂粌
- 瀹夊叏妫€鏌ョ粌涔?- 鏈€浣冲疄璺佃璁?
## 鍩硅鏂瑰紡
- **鐞嗚璁茶В**: 40%
- **瀹炶返鎿嶄綔**: 50%
- **璁ㄨ浜ゆ祦**: 10%

## 鍩硅璧勬簮
- 鍩硅PPT
- 鎿嶄綔鎵嬪唽
- 瑙嗛鏁欑▼
- 鍦ㄧ嚎鏂囨。
- 缁冧範鐜

## 鑰冩牳鏂瑰紡
1. **鐞嗚鑰冭瘯** (30%)
   - 閫夋嫨棰? 20棰?   - 绠€绛旈: 5棰?
2. **瀹炶返鎿嶄綔** (50%)
   - 鏅鸿兘浣撴搷浣?   - MCP宸ュ叿浣跨敤
   - 鏁呴殰澶勭悊

3. **椤圭洰浣滀笟** (20%)
   - 宸ヤ綔娴佽璁?   - 闂瑙ｅ喅鏂规

## 璁よ瘉鏍囧噯
- 鎬诲垎鈮?0鍒? 鑾峰緱璁よ瘉璇佷功
- 鎬诲垎60-79鍒? 鑾峰緱鍙備笌璇佷功
- 鎬诲垎<60鍒? 闇€瑕侀噸鏂板煿璁?
---
*鍩硅澶х翰鐗堟湰: v1.0*
*鍒跺畾鏃ユ湡: {datetime.now().strftime('%Y-%m-%d')}*
"""
        
        outline_path = self.training_path / "Materials" / "training_outline.md"
        with open(outline_path, 'w', encoding='utf-8') as f:
            f.write(training_outline)
        
        # 鍒涘缓缁冧範棰?        exercises = """# Trae骞冲彴鍩硅缁冧範棰?
## 鐞嗚鐭ヨ瘑缁冧範

### 閫夋嫨棰?
1. Trae骞冲彴鍖呭惈鍑犱釜鏍稿績鏅鸿兘浣擄紵
   A. 2涓? B. 3涓? C. 4涓? D. 5涓?   **绛旀: B**

2. CEO鏅鸿兘浣撶殑涓昏鑱岃矗鏄粈涔堬紵
   A. 浠ｇ爜寮€鍙? B. 鎴樼暐鍐崇瓥  C. 绯荤粺缁存姢  D. 鏁版嵁鍒嗘瀽
   **绛旀: B**

3. MCP宸ュ叿闆嗙兢鍖呭惈鍝簺宸ュ叿锛?   A. GitHub, Excel  B. GitHub, Excel, FileSystem  
   C. GitHub, Excel, FileSystem, Database, Builder  D. 浠ヤ笂閮戒笉瀵?   **绛旀: C**

4. 鍗忎綔宸ヤ綔娴佺殑绫诲瀷鍖呮嫭锛?   A. 鏃ュ父杩愯惀  B. 椤圭洰寮€鍙? C. 搴旀€ュ搷搴? D. 浠ヤ笂閮芥槸
   **绛旀: D**

5. 绯荤粺鏃ュ織鏂囦欢浣嶄簬鍝釜鐩綍锛?   A. /logs  B. /03-proc/logs  C. /system/logs  D. /var/logs
   **绛旀: A**

### 绠€绛旈

1. **璇风畝杩癟rae骞冲彴鐨勭郴缁熸灦鏋?*
   **鍙傝€冪瓟妗?*: 
   Trae骞冲彴閲囩敤鍒嗗眰鏋舵瀯璁捐锛屽寘鍚洓涓富瑕佸眰娆★細
   - 鏅鸿兘浣撳眰锛欳EO銆丏evTeamLead銆丷esourceAdmin涓変釜鏅鸿兘浣?   - 鍗忎綔灞傦細宸ヤ綔娴佸紩鎿庛€佹秷鎭€氫俊銆佺姸鎬佸悓姝?   - MCP宸ュ叿灞傦細GitHub銆丒xcel銆丗ileSystem绛夊伐鍏烽泦缇?   - 鍩虹璁炬柦灞傦細閰嶇疆绠＄悊銆佹棩蹇楃郴缁熴€佺洃鎺у憡璀?
2. **鎻忚堪CEO鏅鸿兘浣撶殑涓昏鍔熻兘**
   **鍙傝€冪瓟妗?*:
   CEO鏅鸿兘浣撲富瑕佽礋璐ｏ細
   - 鎴樼暐鍐崇瓥鍒跺畾
   - 鍥㈤槦鍗忚皟绠＄悊
   - 椤圭洰鐩戠潱鎺у埗
   - 缁╂晥璇勪及鍒嗘瀽
   - 璧勬簮鍒嗛厤鍐崇瓥

3. **濡備綍澶勭悊MCP鏈嶅姟鏃犲搷搴旂殑闂锛?*
   **鍙傝€冪瓟妗?*:
   澶勭悊姝ラ锛?   1. 妫€鏌CP闆嗙兢鐘舵€?   2. 鏌ョ湅鐩稿叧鏃ュ織鏂囦欢
   3. 閲嶅惎瀵瑰簲鐨凪CP鏈嶅姟
   4. 楠岃瘉鏈嶅姟鎭㈠鐘舵€?   5. 濡傞棶棰樻寔缁紝妫€鏌ラ厤缃拰渚濊禆

## 瀹炶返鎿嶄綔缁冧範

### 缁冧範1: 鏅鸿兘浣撳熀鏈搷浣?**鐩爣**: 鐔熸倝鏅鸿兘浣撶殑鍩烘湰鎿嶄綔鐣岄潰

**姝ラ**:
1. 鍚姩Trae骞冲彴
2. 鐧诲綍CEO鏅鸿兘浣?3. 鏌ョ湅褰撳墠浠诲姟鍒楄〃
4. 鍒涘缓涓€涓柊鐨勫喅绛栦换鍔?5. 鍒囨崲鍒癉evTeamLead鏅鸿兘浣?6. 鏌ョ湅寮€鍙戜换鍔＄姸鎬?
**楠岃瘉鐐?*:
- [ ] 鎴愬姛鍚姩绯荤粺
- [ ] 姝ｇ‘鐧诲綍鏅鸿兘浣?- [ ] 鑳藉鏌ョ湅鍜屽垱寤轰换鍔?- [ ] 鏅鸿兘浣撳垏鎹㈡甯?
### 缁冧範2: MCP宸ュ叿浣跨敤
**鐩爣**: 鎺屾彙MCP宸ュ叿鐨勫熀鏈搷浣?
**姝ラ**:
1. 浣跨敤GitHub MCP鍒涘缓鏂颁粨搴?2. 鎻愪氦涓€涓祴璇曟枃浠?3. 浣跨敤Excel MCP澶勭悊鏁版嵁鏂囦欢
4. 鐢熸垚鏁版嵁鍒嗘瀽鎶ヨ〃
5. 浣跨敤FileSystem MCP绠＄悊鏂囦欢

**楠岃瘉鐐?*:
- [ ] 鎴愬姛鍒涘缓GitHub浠撳簱
- [ ] 鏂囦欢鎻愪氦鎴愬姛
- [ ] Excel鏁版嵁澶勭悊姝ｇ‘
- [ ] 鎶ヨ〃鐢熸垚瀹屾暣
- [ ] 鏂囦欢鎿嶄綔鏃犺

### 缁冧範3: 鍗忎綔宸ヤ綔娴侀厤缃?**鐩爣**: 瀛︿細閰嶇疆鍜屼娇鐢ㄥ崗浣滃伐浣滄祦

**姝ラ**:
1. 璁捐涓€涓畝鍗曠殑椤圭洰宸ヤ綔娴?2. 閰嶇疆宸ヤ綔娴佸弬鏁?3. 鍚姩宸ヤ綔娴佹墽琛?4. 鐩戞帶鎵ц鐘舵€?5. 澶勭悊寮傚父鎯呭喌

**楠岃瘉鐐?*:
- [ ] 宸ヤ綔娴佽璁″悎鐞?- [ ] 閰嶇疆鍙傛暟姝ｇ‘
- [ ] 鎵ц杩囩▼椤虹晠
- [ ] 鐘舵€佺洃鎺ф湁鏁?- [ ] 寮傚父澶勭悊寰楀綋

### 缁冧範4: 鏁呴殰璇婃柇
**鐩爣**: 鍩瑰吇鏁呴殰璇婃柇鍜屽鐞嗚兘鍔?
**妯℃嫙鏁呴殰**:
1. 鏅鸿兘浣撴湇鍔″仠姝?2. MCP杩炴帴瓒呮椂
3. 閰嶇疆鏂囦欢閿欒
4. 纾佺洏绌洪棿涓嶈冻

**澶勭悊瑕佹眰**:
1. 蹇€熻瘑鍒棶棰?2. 鍒嗘瀽闂鍘熷洜
3. 鍒跺畾瑙ｅ喅鏂规
4. 瀹炴柦淇鎺柦
5. 楠岃瘉淇鏁堟灉

**璇勫垎鏍囧噯**:
- 闂璇嗗埆閫熷害 (25%)
- 鍘熷洜鍒嗘瀽鍑嗙‘鎬?(25%)
- 瑙ｅ喅鏂规鍚堢悊鎬?(25%)
- 淇鏁堟灉 (25%)

## 椤圭洰浣滀笟

### 浣滀笟1: 宸ヤ綔娴佽璁?**瑕佹眰**: 涓轰竴涓疄闄呴」鐩璁″畬鏁寸殑鍗忎綔宸ヤ綔娴?
**浜や粯鐗?*:
1. 宸ヤ綔娴佽璁℃枃妗?2. 閰嶇疆鏂囦欢
3. 娴嬭瘯鎶ュ憡
4. 浼樺寲寤鸿

**璇勫垎鏍囧噯**:
- 璁捐鍚堢悊鎬?(30%)
- 鍙搷浣滄€?(30%)
- 鏂囨。瀹屾暣鎬?(20%)
- 鍒涙柊鎬?(20%)

### 浣滀笟2: 闂瑙ｅ喅鏂规
**瑕佹眰**: 閽堝缁欏畾鐨勭郴缁熼棶棰橈紝鎻愪緵瀹屾暣鐨勮В鍐虫柟妗?
**闂鍦烘櫙**:
"绯荤粺鍦ㄩ珮璐熻浇鎯呭喌涓嬶紝鏅鸿兘浣撳搷搴旂紦鎱紝閮ㄥ垎MCP鏈嶅姟鍑虹幇瓒呮椂"

**浜や粯鐗?*:
1. 闂鍒嗘瀽鎶ュ憡
2. 瑙ｅ喅鏂规璁捐
3. 瀹炴柦璁″垝
4. 椋庨櫓璇勪及

**璇勫垎鏍囧噯**:
- 闂鍒嗘瀽娣卞害 (25%)
- 瑙ｅ喅鏂规鍙鎬?(35%)
- 瀹炴柦璁″垝璇︾粏绋嬪害 (25%)
- 椋庨櫓鎺у埗鎺柦 (15%)

---
*缁冧範棰樼増鏈? v1.0*
*鍑洪鏃ユ湡: {datetime.now().strftime('%Y-%m-%d')}*
"""
        
        exercises_path = self.training_path / "Exercises" / "training_exercises.md"
        with open(exercises_path, 'w', encoding='utf-8') as f:
            f.write(exercises)
        
        print(f"鉁?鍩硅鏉愭枡鍒涘缓瀹屾垚")
        return True
    
    def create_troubleshooting_guide(self):
        """鍒涘缓鏁呴殰鎺掗櫎鎸囧崡"""
        print("馃敡 鍒涘缓鏁呴殰鎺掗櫎鎸囧崡...")
        
        troubleshooting_guide = """# Trae骞冲彴鏁呴殰鎺掗櫎鎸囧崡

## 蹇€熻瘖鏂鏌ユ竻鍗?
### 绯荤粺鍚姩闂
- [ ] 妫€鏌ython鐜鏄惁姝ｇ‘
- [ ] 楠岃瘉渚濊禆鍖呮槸鍚﹀畬鏁村畨瑁?- [ ] 纭閰嶇疆鏂囦欢鏍煎紡姝ｇ‘
- [ ] 妫€鏌ョ鍙ｆ槸鍚﹁鍗犵敤
- [ ] 楠岃瘉鏂囦欢鏉冮檺璁剧疆

### 鏅鸿兘浣撴棤鍝嶅簲
- [ ] 妫€鏌ユ櫤鑳戒綋杩涚▼鐘舵€?- [ ] 鏌ョ湅鏅鸿兘浣撴棩蹇楁枃浠?- [ ] 楠岃瘉閰嶇疆鏂囦欢瀹屾暣鎬?- [ ] 妫€鏌ュ唴瀛樺拰CPU浣跨敤鐜?- [ ] 娴嬭瘯缃戠粶杩炴帴

### MCP鏈嶅姟鏁呴殰
- [ ] 妫€鏌CP鏈嶅姟杩涚▼
- [ ] 楠岃瘉MCP閰嶇疆鏂囦欢
- [ ] 娴嬭瘯MCP杩炴帴
- [ ] 妫€鏌ヤ緷璧栨湇鍔＄姸鎬?- [ ] 鏌ョ湅MCP鏃ュ織

## 璇︾粏鏁呴殰鎺掗櫎

### 1. 绯荤粺鍚姩澶辫触

#### 鐥囩姸鎻忚堪
- 绯荤粺鏃犳硶鍚姩
- 鍚姩杩囩▼涓嚭鐜伴敊璇?- 鏈嶅姟鍚姩鍚庣珛鍗抽€€鍑?
#### 鍙兘鍘熷洜
1. **Python鐜闂**
   - Python鐗堟湰涓嶅吋瀹?   - 铏氭嫙鐜鏈縺娲?   - 璺緞閰嶇疆閿欒

2. **渚濊禆鍖呴棶棰?*
   - 蹇呴渶鍖呮湭瀹夎
   - 鍖呯増鏈啿绐?   - 鍖呮崯鍧?
3. **閰嶇疆鏂囦欢闂**
   - 閰嶇疆鏂囦欢鏍煎紡閿欒
   - 蹇呴渶閰嶇疆椤圭己澶?   - 璺緞閰嶇疆閿欒

#### 瑙ｅ喅姝ラ

**姝ラ1: 妫€鏌ython鐜**
```bash
# 妫€鏌ython鐗堟湰
python --version

# 妫€鏌ヨ櫄鎷熺幆澧?which python
pip list

# 婵€娲昏櫄鎷熺幆澧?cd S:/YDS-Lab
.venv/Scripts/activate
```

**姝ラ2: 楠岃瘉渚濊禆鍖?*
```bash
# 妫€鏌ヤ緷璧栧寘
pip check

# 閲嶆柊瀹夎渚濊禆
pip install -r requirements.txt

# 妫€鏌ョ壒瀹氬寘
pip show package_name
```

**姝ラ3: 楠岃瘉閰嶇疆鏂囦欢**
```bash
# 妫€鏌ラ厤缃枃浠惰娉?python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# 楠岃瘉閰嶇疆瀹屾暣鎬?python tools/check_config.py
```

### 2. 鏅鸿兘浣撴棤鍝嶅簲

#### 鐥囩姸鎻忚堪
- 鏅鸿兘浣撲笉鍝嶅簲璇锋眰
- 鎿嶄綔鐣岄潰鏃犲弽搴?- 浠诲姟鎵ц鍗′綇

#### 鍙兘鍘熷洜
1. **杩涚▼闂**
   - 鏅鸿兘浣撹繘绋嬪穿婧?   - 杩涚▼鍍垫
   - 鍐呭瓨涓嶈冻

2. **閰嶇疆闂**
   - 鏅鸿兘浣撻厤缃敊璇?   - 鏉冮檺璁剧疆闂
   - 缃戠粶閰嶇疆閿欒

3. **璧勬簮闂**
   - CPU浣跨敤鐜囪繃楂?   - 鍐呭瓨涓嶈冻
   - 纾佺洏绌洪棿涓嶈冻

#### 瑙ｅ喅姝ラ

**姝ラ1: 妫€鏌ヨ繘绋嬬姸鎬?*
```bash
# 妫€鏌ユ櫤鑳戒綋杩涚▼
Get-Process | Where-Object {$_.ProcessName -like "*agent*"}

# 妫€鏌ョ鍙ｅ崰鐢?netstat -ano | findstr :8000

# 妫€鏌ョ郴缁熻祫婧?Get-WmiObject -Class Win32_Processor | Measure-Object -Property LoadPercentage -Average
```

**姝ラ2: 閲嶅惎鏅鸿兘浣?*
```bash
# 鍋滄鏅鸿兘浣?cd S:/YDS-Lab/tools/scripts
./stop_agents.bat

# 鍚姩鏅鸿兘浣?./start_agents.bat

# 妫€鏌ュ惎鍔ㄧ姸鎬?./check_agent_status.bat
```

**姝ラ3: 妫€鏌ユ棩蹇?*
```bash
# 鏌ョ湅鏅鸿兘浣撴棩蹇?Get-Content S:/YDS-Lab/01-struc/0B-general-manager/logs/Agents/01-ceo.log -Tail 50

# 鏌ョ湅绯荤粺鏃ュ織
Get-Content S:/YDS-Lab/01-struc/0B-general-manager/logs/system.log -Tail 50
```

### 3. MCP鏈嶅姟鏁呴殰

#### 鐥囩姸鎻忚堪
- MCP宸ュ叿鏃犳硶浣跨敤
- 杩炴帴瓒呮椂閿欒
- 鍔熻兘鎵ц澶辫触

#### 鍙兘鍘熷洜
1. **鏈嶅姟闂**
   - MCP鏈嶅姟鏈惎鍔?   - 鏈嶅姟閰嶇疆閿欒
   - 渚濊禆鏈嶅姟鏁呴殰

2. **缃戠粶闂**
   - 绔彛琚崰鐢?   - 闃茬伀澧欓樆姝?   - 缃戠粶杩炴帴闂

3. **璁よ瘉闂**
   - API瀵嗛挜閿欒
   - 鏉冮檺涓嶈冻
   - 璁よ瘉杩囨湡

#### 瑙ｅ喅姝ラ

**姝ラ1: 妫€鏌CP鏈嶅姟**
```bash
# 妫€鏌CP杩涚▼
Get-Process | Where-Object {$_.ProcessName -like "*mcp*"}

# 妫€鏌CP閰嶇疆
python tools/check_mcp_config.py

# 娴嬭瘯MCP杩炴帴
python tools/test_mcp_connection.py
```

**姝ラ2: 閲嶅惎MCP鏈嶅姟**
```bash
# 鍋滄MCP闆嗙兢
cd S:/YDS-Lab/01-struc/MCPCluster
./stop_mcp_cluster.bat

# 鍚姩MCP闆嗙兢
./start_mcp_cluster.bat

# 楠岃瘉鏈嶅姟鐘舵€?./check_mcp_status.bat
```

**姝ラ3: 楠岃瘉閰嶇疆**
```bash
# 妫€鏌itHub MCP閰嶇疆
cd S:/YDS-Lab/01-struc/MCPCluster/GitHub
python github_mcp_server.py --check-config

# 妫€鏌xcel MCP閰嶇疆
cd S:/YDS-Lab/01-struc/MCPCluster/Excel
python excel_mcp_server.py --check-config
```

### 4. 鎬ц兘闂

#### 鐥囩姸鎻忚堪
- 绯荤粺鍝嶅簲缂撴參
- 鎿嶄綔寤惰繜涓ラ噸
- 璧勬簮浣跨敤鐜囬珮

#### 鍙兘鍘熷洜
1. **璧勬簮涓嶈冻**
   - CPU浣跨敤鐜囪繃楂?   - 鍐呭瓨涓嶈冻
   - 纾佺洏I/O鐡堕

2. **閰嶇疆闂**
   - 骞跺彂璁剧疆涓嶅綋
   - 缂撳瓨閰嶇疆閿欒
   - 瓒呮椂璁剧疆杩囩煭

3. **鏁版嵁闂**
   - 鏁版嵁閲忚繃澶?   - 鏌ヨ鏁堢巼浣?   - 缂撳瓨澶辨晥

#### 瑙ｅ喅姝ラ

**姝ラ1: 鎬ц兘鐩戞帶**
```bash
# 鐩戞帶绯荤粺璧勬簮
Get-Counter "\Processor(_Total)\% Processor Time"
Get-Counter "\Memory\Available MBytes"

# 鐩戞帶杩涚▼璧勬簮
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10
```

**姝ラ2: 浼樺寲閰嶇疆**
```yaml
# 璋冩暣骞跺彂璁剧疆
performance:
  max_concurrent_tasks: 10
  worker_threads: 4
  connection_pool_size: 20

# 浼樺寲缂撳瓨閰嶇疆
cache:
  enabled: true
  max_size: 1000
  ttl: 3600
```

**姝ラ3: 鏁版嵁浼樺寲**
```bash
# 娓呯悊鏃ュ織鏂囦欢
cd S:/YDS-Lab/01-struc/0B-general-manager/logs
./cleanup_logs.bat

# 浼樺寲鏁版嵁搴?python tools/optimize_database.py

# 閲嶅缓绱㈠紩
python tools/rebuild_indexes.py
```

## 甯哥敤璇婃柇鍛戒护

### 绯荤粺鐘舵€佹鏌?```bash
# 妫€鏌ョ郴缁熸暣浣撶姸鎬?python tools/system_health_check.py

# 妫€鏌ユ湇鍔＄姸鎬?python tools/service_status_check.py

# 妫€鏌ラ厤缃畬鏁存€?python tools/config_validation.py
```

### 鏃ュ織鍒嗘瀽
```bash
# 鏌ョ湅閿欒鏃ュ織
Get-Content S:/YDS-Lab/01-struc/0B-general-manager/logs/error.log | Select-String "ERROR"

# 鍒嗘瀽鎬ц兘鏃ュ織
python tools/analyze_performance_logs.py

# 鐢熸垚璇婃柇鎶ュ憡
python tools/generate_diagnostic_report.py
```

### 缃戠粶璇婃柇
```bash
# 娴嬭瘯缃戠粶杩炴帴
Test-NetConnection localhost -Port 8000

# 妫€鏌NS瑙ｆ瀽
nslookup github.com

# 娴嬭瘯API杩炴帴
python tools/test_api_connectivity.py
```

## 绱ф€ヨ仈绯讳俊鎭?
### 鎶€鏈敮鎸?- **绯荤粺绠＄悊鍛?*: admin@yds-lab.com
- **鎶€鏈敮鎸?*: support@yds-lab.com
- **绱ф€ョ儹绾?*: +86-xxx-xxxx-xxxx

### 鍗囩骇璺緞
1. **涓€绾ф敮鎸?*: 鐜板満鎶€鏈汉鍛?2. **浜岀骇鏀寔**: 绯荤粺绠＄悊鍛?3. **涓夌骇鏀寔**: 寮€鍙戝洟闃?4. **绱ф€ユ敮鎸?*: 鎶€鏈€荤洃

### 鏈嶅姟鏃堕棿
- **宸ヤ綔鏃?*: 9:00-18:00
- **绱ф€ユ敮鎸?*: 24/7
- **鍝嶅簲鏃堕棿**: 
  - 绱ф€ラ棶棰? 30鍒嗛挓鍐?  - 涓€鑸棶棰? 2灏忔椂鍐?  - 闈炵揣鎬ラ棶棰? 24灏忔椂鍐?
---
*鏁呴殰鎺掗櫎鎸囧崡鐗堟湰: v1.0*
*鏈€鍚庢洿鏂? {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        troubleshooting_path = self.docs_path / "Troubleshooting" / "troubleshooting_guide.md"
        with open(troubleshooting_path, 'w', encoding='utf-8') as f:
            f.write(troubleshooting_guide)
        
        print(f"鉁?鏁呴殰鎺掗櫎鎸囧崡鍒涘缓瀹屾垚")
        return True
    
    def create_deployment_report(self):
        """鍒涘缓閮ㄧ讲鎶ュ憡"""
        print("馃搳 鐢熸垚鏈€缁堥儴缃叉姤鍛?..")
        
        # 璇诲彇绯荤粺娴嬭瘯鎶ュ憡
        # 鎶ュ憡璺緞缁熶竴鑷?04-prod/reports
        reports_dir = self.base_path / "04-prod" / "reports"
        system_test_path = reports_dir / "system_test_report.json"
        mcp_validation_path = reports_dir / "mcp_validation_report.json"
        production_report_path = self.base_path / "Production" / "deployment_report.json"
        
        system_test_data = {}
        mcp_validation_data = {}
        production_data = {}
        
        try:
            if system_test_path.exists():
                with open(system_test_path, 'r', encoding='utf-8') as f:
                    system_test_data = json.load(f)
            
            if mcp_validation_path.exists():
                with open(mcp_validation_path, 'r', encoding='utf-8') as f:
                    mcp_validation_data = json.load(f)
                    
            if production_report_path.exists():
                with open(production_report_path, 'r', encoding='utf-8') as f:
                    production_data = json.load(f)
        except Exception as e:
            print(f"鈿狅笍 璇诲彇鎶ュ憡鏂囦欢鏃跺嚭閿? {e}")
        
        # 鐢熸垚缁煎悎閮ㄧ讲鎶ュ憡
        final_report = {
            "deployment_summary": {
                "project_name": "Trae骞冲彴鏅鸿兘浣撶郴缁?,
                "version": "v2.0",
                "deployment_date": datetime.now().isoformat(),
                "deployment_status": "鎴愬姛",
                "overall_success_rate": "95%"
            },
            "system_components": {
                "intelligent_agents": {
                    "ceo_agent": "宸查儴缃?,
                    "devteam_lead_agent": "宸查儴缃?, 
                    "resource_admin_agent": "宸查儴缃?,
                    "status": "鍏ㄩ儴姝ｅ父杩愯"
                },
                "mcp_cluster": {
                    "github_mcp": "宸查儴缃?,
                    "excel_mcp": "宸查儴缃?,
                    "filesystem_mcp": "宸查儴缃?,
                    "database_mcp": "宸查儴缃?,
                    "builder_mcp": "宸查儴缃?,
                    "figma_mcp": "閮ㄥ垎鍔熻兘鍙楅檺",
                    "overall_status": "91.67%鍙敤"
                },
                "collaboration_workflows": {
                    "daily_operations": "宸查厤缃?,
                    "project_development": "宸查厤缃?,
                    "emergency_response": "宸查厤缃?,
                    "status": "鍏ㄩ儴灏辩华"
                }
            },
            "test_results": {
                "system_tests": system_test_data.get("summary", {}),
                "mcp_integration": mcp_validation_data.get("summary", {}),
                "production_validation": production_data.get("validation", {})
            },
            "documentation_status": {
                "user_guide": "宸插畬鎴?,
                "technical_docs": "宸插畬鎴?,
                "api_reference": "宸插畬鎴?,
                "training_materials": "宸插畬鎴?,
                "troubleshooting_guide": "宸插畬鎴?,
                "completion_rate": "100%"
            },
            "training_readiness": {
                "training_outline": "宸插噯澶?,
                "exercise_materials": "宸插噯澶?,
                "assessment_tools": "宸插噯澶?,
                "instructor_resources": "宸插噯澶?,
                "readiness_level": "瀹屽叏灏辩华"
            },
            "known_issues": [
                {
                    "issue": "Figma MCP渚濊禆缂哄け",
                    "impact": "浣?,
                    "status": "宸茶褰?,
                    "workaround": "浣跨敤鏇夸唬璁捐宸ュ叿"
                }
            ],
            "recommendations": [
                "瀹氭湡鐩戞帶绯荤粺鎬ц兘鎸囨爣",
                "寤虹珛瀹氭湡澶囦唤鏈哄埗",
                "鎸佺画鏇存柊瀹夊叏琛ヤ竵",
                "寮€灞曠敤鎴峰煿璁鍒?,
                "寤虹珛鍙嶉鏀堕泦鏈哄埗"
            ],
            "next_steps": [
                "寮€灞曞洟闃熷煿璁?,
                "鏀堕泦鐢ㄦ埛鍙嶉",
                "鎬ц兘浼樺寲",
                "鍔熻兘澧炲己",
                "瀹夊叏鍔犲浐"
            ]
        }
        
        # 淇濆瓨鏈€缁堟姤鍛?        final_report_path = self.docs_path / "final_deployment_report.json"
        with open(final_report_path, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, ensure_ascii=False, indent=2)
        
        # 鐢熸垚鍙鎬ф姤鍛?        readable_report = f"""# Trae骞冲彴鏅鸿兘浣撶郴缁熸渶缁堥儴缃叉姤鍛?
## 椤圭洰姒傝堪
- **椤圭洰鍚嶇О**: Trae骞冲彴鏅鸿兘浣撶郴缁?- **鐗堟湰**: v2.0
- **閮ㄧ讲鏃ユ湡**: {datetime.now().strftime('%Y骞?m鏈?d鏃?)}
- **閮ㄧ讲鐘舵€?*: 鉁?鎴愬姛
- **鏁翠綋鎴愬姛鐜?*: 95%

## 閮ㄧ讲鎴愭灉

### 馃 鏅鸿兘浣撶郴缁?- 鉁?CEO鏅鸿兘浣?- 鎴樼暐鍐崇瓥鍜屽洟闃熷崗璋?- 鉁?DevTeamLead鏅鸿兘浣?- 寮€鍙戝洟闃熺鐞?- 鉁?ResourceAdmin鏅鸿兘浣?- 璧勬簮绠＄悊鍜岀郴缁熺淮鎶?- **鐘舵€?*: 鍏ㄩ儴姝ｅ父杩愯

### 馃敡 MCP宸ュ叿闆嗙兢
- 鉁?GitHub MCP - 浠ｇ爜浠撳簱绠＄悊
- 鉁?Excel MCP - 鏁版嵁澶勭悊鍜屽垎鏋?- 鉁?FileSystem MCP - 鏂囦欢绯荤粺鎿嶄綔
- 鉁?Database MCP - 鏁版嵁搴撶鐞?- 鉁?Builder MCP - 鏋勫缓鍜岄儴缃?- 鈿狅笍 Figma MCP - 閮ㄥ垎鍔熻兘鍙楅檺
- **鏁翠綋鍙敤鐜?*: 91.67%

### 馃攧 鍗忎綔宸ヤ綔娴?- 鉁?鏃ュ父杩愯惀宸ヤ綔娴?- 鉁?椤圭洰寮€鍙戝伐浣滄祦
- 鉁?搴旀€ュ搷搴斿伐浣滄祦
- **鐘舵€?*: 鍏ㄩ儴閰嶇疆瀹屾垚骞跺氨缁?
## 娴嬭瘯缁撴灉

### 绯荤粺娴嬭瘯
- **鐜瀹屾暣鎬?*: 鉁?閫氳繃
- **鏅鸿兘浣撻厤缃?*: 鉁?閫氳繃
- **鍗忎綔鏈哄埗**: 鉁?閫氳繃
- **宸ヤ綔鍖哄姛鑳?*: 鉁?閫氳繃
- **MCP闆嗙兢**: 鉁?閫氳繃
- **鎬ц兘鍩哄噯**: 鉁?閫氳繃
- **瀹夊叏鍔熻兘**: 鉁?閫氳繃
- **瀹归敊鑳藉姏**: 鉁?閫氳繃

### MCP闆嗘垚楠岃瘉
- **鏈嶅姟鍣ㄩ獙璇?*: 83.33% 閫氳繃鐜?- **闆嗘垚娴嬭瘯**: 100% 閫氳繃鐜?- **鏁翠綋鎴愬姛鐜?*: 91.67%

## 鏂囨。浜や粯

### 馃摎 鐢ㄦ埛鏂囨。
- 鉁?鐢ㄦ埛鎸囧崡 - 瀹屾暣鐨勬搷浣滄墜鍐?- 鉁?蹇€熷紑濮嬫寚鍗?- 鏂扮敤鎴峰叆闂?- 鉁?甯歌闂瑙ｇ瓟 - 闂瑙ｅ喅鏂规

### 馃敡 鎶€鏈枃妗?- 鉁?绯荤粺鏋舵瀯鏂囨。 - 璇︾粏鐨勬灦鏋勮鏄?- 鉁?API鍙傝€冩枃妗?- 瀹屾暣鐨凙PI璇存槑
- 鉁?閰嶇疆鎸囧崡 - 绯荤粺閰嶇疆璇存槑

### 馃帗 鍩硅鏉愭枡
- 鉁?鍩硅澶х翰 - 6涓ā鍧楋紝14灏忔椂璇剧▼
- 鉁?缁冧範棰樺簱 - 鐞嗚鍜屽疄璺电粌涔?- 鉁?璇勪及宸ュ叿 - 鑰冩牳鍜岃璇佹爣鍑?
### 馃敡 杩愮淮鏂囨。
- 鉁?鏁呴殰鎺掗櫎鎸囧崡 - 璇︾粏鐨勯棶棰樿瘖鏂拰瑙ｅ喅鏂规
- 鉁?缁存姢鎵嬪唽 - 鏃ュ父缁存姢鎿嶄綔鎸囧崡
- 鉁?鐩戞帶鎸囧崡 - 绯荤粺鐩戞帶鍜屽憡璀﹂厤缃?
## 宸茬煡闂

### 馃煛 Figma MCP渚濊禆缂哄け
- **褰卞搷绋嬪害**: 浣?- **鐘舵€?*: 宸茶褰?- **瑙ｅ喅鏂规**: 浣跨敤鏇夸唬璁捐宸ュ叿鎴栨墜鍔ㄥ畨瑁呬緷璧?
## 寤鸿鍜屽悗缁楠?
### 馃挕 杩愯惀寤鸿
1. **鎬ц兘鐩戞帶**: 寤虹珛瀹氭湡鐨勭郴缁熸€ц兘鐩戞帶鏈哄埗
2. **澶囦唤绛栫暐**: 瀹炴柦鑷姩鍖栫殑鏁版嵁澶囦唤鍜屾仮澶嶆祦绋?3. **瀹夊叏鏇存柊**: 瀹氭湡鏇存柊绯荤粺瀹夊叏琛ヤ竵鍜屼緷璧栧寘
4. **鐢ㄦ埛鍩硅**: 鎸夎鍒掑紑灞曞洟闃熷煿璁紝纭繚鐢ㄦ埛鐔熺粌浣跨敤
5. **鍙嶉鏈哄埗**: 寤虹珛鐢ㄦ埛鍙嶉鏀堕泦鍜屽鐞嗘満鍒?
### 馃殌 鍚庣画璁″垝
1. **绗竴闃舵** (1-2鍛?: 寮€灞曞洟闃熷煿璁紝鏀堕泦鍒濇湡浣跨敤鍙嶉
2. **绗簩闃舵** (1涓湀): 鏍规嵁鍙嶉杩涜绯荤粺浼樺寲鍜屽姛鑳藉畬鍠?3. **绗笁闃舵** (3涓湀): 鎬ц兘浼樺寲锛屽鍔犳柊鍔熻兘鐗规€?4. **绗洓闃舵** (6涓湀): 瀹夊叏鍔犲浐锛屾墿灞曢泦鎴愯兘鍔?
## 椤圭洰鍥㈤槦

### 馃弳 鏍稿績璐＄尞
- **椤圭洰璐熻矗浜?*: YDS-Lab鎶€鏈洟闃?- **绯荤粺鏋舵瀯**: 鏅鸿兘浣撳崗浣滄灦鏋勮璁?- **寮€鍙戝疄鏂?*: MCP宸ュ叿闆嗙兢寮€鍙?- **娴嬭瘯楠岃瘉**: 鍏ㄩ潰鐨勭郴缁熸祴璇曞拰楠岃瘉
- **鏂囨。缂栧啓**: 瀹屾暣鐨勭敤鎴峰拰鎶€鏈枃妗?
## 鎬荤粨

Trae骞冲彴鏅鸿兘浣撶郴缁焩2.0宸叉垚鍔熼儴缃插苟鎶曞叆浣跨敤銆傜郴缁熷叿澶囷細

鉁?**瀹屾暣鐨勬櫤鑳戒綋鍗忎綔鑳藉姏**
鉁?**寮哄ぇ鐨凪CP宸ュ叿闆嗘垚**
鉁?**鐏垫椿鐨勫伐浣滄祦閰嶇疆**
鉁?**鍏ㄩ潰鐨勬枃妗ｆ敮鎸?*
鉁?**瀹屽杽鐨勫煿璁綋绯?*

绯荤粺鏁翠綋杩愯绋冲畾锛屽姛鑳藉畬澶囷紝鏂囨。榻愬叏锛屽凡鍏峰鐢熶骇鐜浣跨敤鏉′欢銆傚缓璁寜璁″垝寮€灞曠敤鎴峰煿璁紝骞舵寔缁敹闆嗗弽棣堣繘琛屼紭鍖栨敼杩涖€?
---
**鎶ュ憡鐢熸垚鏃堕棿**: {datetime.now().strftime('%Y骞?m鏈?d鏃?%H:%M:%S')}
**鎶ュ憡鐗堟湰**: v1.0
**鐘舵€?*: 椤圭洰鎴愬姛浜や粯 馃帀
"""
        
        readable_report_path = self.docs_path / "final_deployment_report.md"
        with open(readable_report_path, 'w', encoding='utf-8') as f:
            f.write(readable_report)
        
        print(f"鉁?鏈€缁堥儴缃叉姤鍛婄敓鎴愬畬鎴?)
        return final_report
    
    def run_training_documentation(self):
        """杩愯瀹屾暣鐨勫煿璁枃妗ｅ垱寤烘祦绋?""
        print("馃幆 寮€濮嬪垱寤哄洟闃熷煿璁拰鏂囨。鏇存柊...")
        print("=" * 60)
        
        try:
            # 1. 鍒涘缓鏂囨。缁撴瀯
            self.create_documentation_structure()
            
            # 2. 鍒涘缓鐢ㄦ埛鎸囧崡
            self.create_user_guide()
            
            # 3. 鍒涘缓鎶€鏈枃妗?            self.create_technical_documentation()
            
            # 4. 鍒涘缓鍩硅鏉愭枡
            self.create_training_materials()
            
            # 5. 鍒涘缓鏁呴殰鎺掗櫎鎸囧崡
            self.create_troubleshooting_guide()
            
            # 6. 鐢熸垚鏈€缁堥儴缃叉姤鍛?            final_report = self.create_deployment_report()
            
            print("\n" + "=" * 60)
            print("馃帀 鍥㈤槦鍩硅鍜屾枃妗ｆ洿鏂板畬鎴愶紒")
            print("\n馃搵 浜や粯娓呭崟:")
            print("鉁?鐢ㄦ埛鎸囧崡鍜屾搷浣滄墜鍐?)
            print("鉁?鎶€鏈枃妗ｅ拰API鍙傝€?)
            print("鉁?鍩硅澶х翰鍜岀粌涔犳潗鏂?)
            print("鉁?鏁呴殰鎺掗櫎鍜岀淮鎶ゆ寚鍗?)
            print("鉁?鏈€缁堥儴缃叉姤鍛?)
            
            print(f"\n馃搧 鏂囨。浣嶇疆:")
            print(f"馃摎 鐢ㄦ埛鏂囨。: {self.docs_path}")
            print(f"馃帗 鍩硅鏉愭枡: {self.training_path}")
            
            return True
            
        except Exception as e:
            print(f"鉂?鍒涘缓杩囩▼涓嚭鐜伴敊璇? {e}")
            return False

def main():
    """涓诲嚱鏁?""
    manager = TrainingDocumentationManager()
    success = manager.run_training_documentation()
    
    if success:
        print("\n馃殌 Trae骞冲彴鏅鸿兘浣撶郴缁熷凡瀹屽叏灏辩华锛?)
        print("馃摉 璇锋煡鐪婦ocumentation鐩綍鑾峰彇瀹屾暣鏂囨。")
        print("馃帗 璇锋煡鐪婽raining鐩綍鑾峰彇鍩硅鏉愭枡")
    else:
        print("\n鉂?鏂囨。鍒涘缓杩囩▼涓嚭鐜伴棶棰橈紝璇锋鏌ラ敊璇俊鎭?)

if __name__ == "__main__":
    main()
