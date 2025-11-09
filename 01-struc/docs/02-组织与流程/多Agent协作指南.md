# 澶欰gent鍗忎綔杩愯鎸囧崡锛圷DS-Lab锛?
鏈寚鍗楃敤浜庤鏄庡浣曚娇鐢ㄨ交閲忓崗浣滅紪鎺掑櫒 tools/agents/run_collab.py 鍦ㄤ笉渚濊禆 CrewAI 鐨勬儏鍐典笅锛屽揩閫熺粍缁団€滄瘡鏃ユ櫒浼?绱ф€ヤ細璁€濆苟鑷姩鐢熸垚銆佸綊妗ｆ爣鍑嗗寲浼氳绾銆?
閫傜敤浜虹兢锛氭€荤粡鍔炪€佹妧鏈礋璐ｄ汉銆佽繍缁村悓瀛︼紝浠ュ強闇€瑕侀泦鎴愬閮ㄩ棬 AI Agent 鍗忎綔娴佺▼鐨勫紑鍙戣€呫€?
---

## 1. 鏋舵瀯涓庢枃浠朵綅缃?
- 鍗忎綔缂栨帓鍣細
  - 璺緞锛歵ools/agents/run_collab.py
  - 浣滅敤锛氭寜鍥哄畾椤哄簭璋冨害鍚勯儴闂?Agent锛圕EO/浼佸垝/璐㈠姟/寮€鍙?甯傚満/璧勬簮琛屾斂锛夛紝鐢熸垚浼氳绾骞跺綊妗ｃ€?
- 閮ㄩ棬 Agent Prompt锛?  - CEO锛歋truc/Agents/01-ceo/prompt.py
  - 浼佸垝锛歋truc/Agents/03-planning_director/prompt.py
  - 璐㈠姟锛歋truc/Agents/04-finance_director/prompt.py
  - 寮€鍙戯細Struc/Agents/06-dev_team/dev_director/prompt.py
  - 甯傚満锛歋truc/Agents/07-marketing_director/prompt.py
  - 璧勬簮琛屾斂锛歋truc/Agents/05-resource_admin/prompt.py

- LLM 璺敱锛堝悗绔€傞厤锛夛細
  - 璺緞锛歮odels/services/llm_router.py
  - 璇存槑锛氱粺涓€灏佽妯″瀷璋冪敤锛屽彲璺敱鑷?Shimmy / Ollama / OpenAI 鍏煎鎺ュ彛绛夊悗绔€?
- 鎴樼暐瑙勫垝鎽樿鏉ユ簮锛堜綔涓轰細璁笂涓嬫枃锛夛細
  - 璺緞锛歋truc/GeneralOffice/Docs/YDS-AI-鎴樼暐瑙勫垝/
  - 榛樿璇诲彇锛歒DS AI鍏徃寤鸿涓庨」鐩疄鏂藉畬鏁存柟妗堬紙V1.0锛?md锛堝墠鑻ュ共瀛楃锛?
- 浼氳绾褰掓。锛?  - 褰掓。鍑芥暟锛歋truc/Agents/01-ceo/tools.py::archive_meeting
  - 淇濆瓨浣嶇疆锛?    - Markdown锛歋truc/GeneralOffice/meetings/MTG-YYYYMMDD-HHMM.md
    - JSON锛歋truc/GeneralOffice/meetings/MTG-YYYYMMDD-HHMM.json锛堣嚜鍔ㄥ悓姝ョ敓鎴愶紝鍖呭惈缁撴瀯鍖栧尯鍧椾笌琛ㄦ牸瑙ｆ瀽锛?
鍙傝€冩枃妗ｏ細Struc/GeneralOffice/Docs/LLM璺敱涓庡悗绔€夋嫨锛圫himmy-Ollama锛変娇鐢ㄨ鏄?md

---

## 2. 鍓嶇疆鏉′欢

1) 妯″瀷鍚庣宸插氨缁細
   - 宸插湪鏈満鍚姩 Shimmy / Ollama / 鍏朵粬 OpenAI 鍏煎鎺ㄧ悊鍚庣銆?   - 鎸夌収鈥淟LM 璺敱涓庡悗绔€夋嫨鈥濇枃妗ｅ畬鎴?llm_router 閰嶇疆銆?
2) Python 鐜锛?   - Python 3.10+锛堝缓璁級
   - 鏃犻澶栫涓夋柟渚濊禆锛岃剼鏈€氳繃鍐呴儴璺敱鐩存帴璋冪敤妯″瀷銆?
3) 浠撳簱鐩綍缁撴瀯锛?   - 鏈剼鏈細鍦ㄨ繍琛屾椂鑷姩娉ㄥ叆 REPO_ROOT 鑷?sys.path锛屾敮鎸佷粠浠绘剰宸ヤ綔鐩綍鎵ц銆?
---

## 3. 蹇€熶笂鎵嬶紙Windows PowerShell 绀轰緥锛?
鍦ㄤ粨搴撴牴鐩綍鎵ц锛?
1) 姣忔棩鏅ㄤ細锛堥粯璁ら」鐩悕 DeWatermark AI锛?
```
python tools/agents/run_collab.py --meeting daily --project "DeWatermark AI"
```

2) 绱ф€ヤ細璁紙蹇呴』鎻愪緵鍘熷洜 --reason锛?
```
python tools/agents/run_collab.py --meeting emergency --reason "寮€鍙戣繘搴﹀欢杩?澶? --project "DeWatermark AI"
```

3) 鎸囧畾榛樿妯″瀷锛堜笌 llm_router 鍚庣淇濇寔涓€鑷达級

```
python tools/agents/run_collab.py --meeting daily --model "qwen2:7b-instruct"
```

4) 涓衡€滆鍔ㄩ」涓庡喅绛栤€濇寚瀹氬崟鐙ā鍨嬶紙鍙笌 --model 涓嶅悓锛?
```
python tools/agents/run_collab.py --meeting daily --actions-model "qwen2:7b-instruct"
```

鑴氭湰浼氬湪鎺у埗鍙版墦鍗板綊妗ｈ矾寰勶紝骞惰緭鍑哄墠 2000 瀛楃殑棰勮銆?
5) 鑷畾涔夊弬浼氳鑹蹭笌璁▼锛堥€楀彿鍒嗛殧锛?
```
python tools/agents/run_collab.py --meeting daily \
  --participants "鎬荤粡鐞?CEO),浼佸垝鎬荤洃,璐㈠姟鎬荤洃,寮€鍙戞€荤洃,甯傚満鎬荤洃,璧勬簮涓庤鏀? \
  --agenda "寮€鍦鸿鏄?閮ㄩ棬姹囨姤,琛屽姩椤逛笌鍐崇瓥"
```

6) 缁戝畾椤圭洰鐩綍锛堢敤浜庡厓淇℃伅鏍囨敞涓庡悗缁墿灞曪級

```
python tools/agents/run_collab.py --meeting daily --project "DeWatermark AI" --project-id "001-dewatermark-ai"
```

---

## 4. 浜х墿璇存槑

- 淇濆瓨璺緞锛歋truc/GeneralOffice/meetings/
- 鍛藉悕瑙勮寖锛歁TG-YYYYMMDD-HHMM.md
- 鍐呭缁撴瀯锛?  1) 銆愪細璁俊鎭€戜細璁被鍨?椤圭洰/鏃堕棿/鍙備細瑙掕壊/璁▼
  2) 銆愭櫒浼氬紑鍦恒€戯紙鎴栥€愪細璁Е鍙戙€?銆愪細璁紑鍦恒€戯級
  3) 銆愰儴闂ㄦ眹鎶ユ憳瑕併€戯紙Daily 鍖呭惈 浼佸垝/璐㈠姟/寮€鍙?甯傚満/璧勬簮琛屾斂锛汦mergency 渚ч噸 寮€鍙?璐㈠姟/璧勬簮琛屾斂锛?  4) 銆愯鍔ㄩ」涓庡喅绛栥€慚arkdown 琛ㄦ牸锛堣涓嬫枃锛?  5) 銆愪細璁椂闂淬€?
绀轰緥锛堣〃澶村浐瀹氾級锛?
```
| 缂栧彿 | 浜嬮」 | 璐ｄ换閮ㄩ棬/浜?| 浼樺厛绾?| 鎴鏃ユ湡 | 渚濊禆 | 椋庨櫓涓庡簲瀵?| 涓嬩竴姝?|
|---|---|---|---|---|---|---|---|
| 1 | 绀轰緥浜嬮」 | 绀轰緥閮ㄩ棬 | 楂?| 2025-10-30 | 绀轰緥渚濊禆 | 绀轰緥椋庨櫓 | 绀轰緥涓嬩竴姝?|
```

---

## 5. 鈥滆鍔ㄩ」涓庡喅绛栤€濈敓鎴愰€昏緫

- 涓撶敤鈥滀細璁涔︹€漇ystem Prompt锛氫弗鏍艰姹傗€滃彧杈撳嚭Markdown琛ㄦ牸鈥濄€?- 鍙€氳繃 --actions-model 涓烘湰鑺傚崟鐙寚瀹氭ā鍨嬶紝閬垮厤鍙楀叾瀹冩钀介鏍煎奖鍝嶃€?- 鍐呯疆琛ㄦ牸鍥為€€鏈哄埗锛?  - 鑻ュぇ妯″瀷鏈寜瑕佹眰杈撳嚭琛ㄦ牸锛堢己灏戔€渱鈥濇垨鈥?--鈥濇垨琛ㄥご锛夛紝灏嗚嚜鍔ㄥ洖閫€鍒板唴缃殑淇濆簳琛ㄦ牸锛岀‘淇濈粨鏋勭ǔ瀹氥€?- 浼樺厛绾у彇鍊奸檺瀹氫负锛氶珮/涓?浣庯紱鏃ユ湡鏍煎紡锛歒YYY-MM-DD锛涙渶澶?8 鏉°€?
---

## 6. 甯歌闂涓庢帓閿?
1) 鎻愮ず鈥滅揣鎬ヤ細璁渶瑕?--reason鈥濓細
   - 鍙湁鍦?--meeting emergency 鏃跺繀椤绘彁渚?--reason銆?
2) 鎻愮ず鎵句笉鍒版ā鍧楋紙ModuleNotFoundError锛夛細
   - 鏈剼鏈凡鑷姩淇瀵煎叆璺緞锛屽浠嶆姤閿欙紝璇风‘璁や粠浠撳簱鏍圭洰褰曟墽琛岋紝鎴栨鏌ュ伐鍏疯矾寰勬槸鍚﹁绉诲姩銆?
3) 妯″瀷鏈搷搴旀垨鐢熸垚椋庢牸涓嶄竴鑷达細
   - 妫€鏌?llm_router 瀵瑰簲鍚庣鏄惁宸插惎鍔ㄣ€?   - 浣跨敤 --model/--actions-model 鎸囧畾鏇寸ǔ鍋ョ殑鍚庣鎴栨ā鍨嬪埆鍚嶃€?
4) 浜х墿鏈敓鎴愶細
   - 纭 Struc/Agents/01-ceo/tools.py::archive_meeting 瀛樺湪涓旀湁鍐欐潈闄愩€?   - 鑷?2025-10-28 璧凤紝鍚屾椂鐢熸垚 Markdown 涓?JSON 涓ょ被浜х墿锛圝SON 鐢熸垚澶辫触涓嶅奖鍝?Markdown 浜х墿锛夈€?
---

## 7. 鎵╁睍涓庝簩娆″紑鍙?
1) 鏂板閮ㄩ棬锛?   - 鍦?Struc/Agents/<dept>/prompt.py 涓彁渚涚郴缁熸彁绀鸿瘝锛?   - 鍦?run_collab.py 鐩稿簲鍦烘櫙锛坉aily/emergency锛変腑鎻掑叆璋冪敤锛?   - 杩藉姞鍒般€愪細璁俊鎭€戝弬浼氳鑹蹭笌銆愰儴闂ㄦ眹鎶ユ憳瑕併€戝垪琛ㄣ€?
2) 璋冩暣璁▼鎴栧弬浼氬悕鍗曪細
   - 淇敼 run_collab.py 涓?_meeting_meta_block 鐨?agenda 鎴?participants銆?
3) 璋冩暣鈥滆鍔ㄩ」涓庡喅绛栤€濆彛寰勶細
   - 淇敼 _summarize_actions 鐨?system prompt 瑕佹眰锛堣〃澶淬€佸瓧娈靛惈涔夌瓑锛夈€?
4) 瀹氭椂鍖栵細
   - 鍙敤 Windows 浠诲姟璁″垝绋嬪簭瀹氭椂鎵ц鑴氭湰锛?     - PowerShell锛歴cripts/schedule_daily_meeting.ps1锛堟敮鎸佸弬鏁伴€忎紶 --project/--model/--actions-model/--participants/--agenda/--project-id锛?     - 鎵瑰鐞嗭細scripts/schedule_daily_meeting.bat锛堣皟鐢ㄤ笂鏂?PowerShell 鑴氭湰锛?   - 鏃ュ織杈撳嚭榛樿鍐欏叆锛歋truc/GeneralOffice/logs/daily_meeting_YYYYMMDD-HHMM.log

---

## 8. 涓庢棦鏈夊伐鍏风殑鍏崇郴

- generate_meeting_log.py锛坱ools/docs/锛夋彁渚涙ā鏉垮寲鏃ュ織鐢熸垚涓庡鍑哄姛鑳斤紝閫傚悎鎸夆€滀細璁被鍨?鍙備細浜?鏍煎紡鈥濆揩閫熷嚭妯℃澘锛?- run_collab.py 鑱氱劍鈥滃熀浜庨儴闂?Agent 鑷姩杈撳嚭鍐呭 + 姹囨€昏鍔ㄩ」 + 缁熶竴褰掓。鈥濓紝閫傚悎鈥滄棩甯歌嚜鍔ㄥ寲鏅ㄤ細/搴旀€ョ邯瑕佲€濄€?
涓よ€呭彲骞惰浣跨敤锛氬墠鑰呯敤浜庤祫鏂欐ā鏉垮寲涓庡鍙戞牸寮忥紝鍚庤€呰礋璐ｈ嚜鍔ㄦ媺鍙栧悇閮ㄩ棬褰撴棩缁撹骞跺浐鍖栬褰曘€?
---

## 9. CLI 鍙傛暟鍙傝€?
```
--meeting        daily|emergency       浼氳绫诲瀷锛堥粯璁?daily锛?--reason         <string>              绱ф€ヤ細璁師鍥狅紙浠?emergency 蹇呭～锛?--project        <string>              椤圭洰鍚嶇О锛堥粯璁?"DeWatermark AI"锛?--model          <string>              榛樿妯″瀷锛坙lm_router 璺敱鍒悕鎴栨ā鍨婭D锛?--actions-model  <string>              鈥滆鍔ㄩ」涓庡喅绛栤€濈嫭绔嬫ā鍨嬶紙榛樿涓?--model 鐩稿悓锛?--participants   <csv>                 鑷畾涔夊弬浼氳鑹诧紝閫楀彿鍒嗛殧锛堣鐩栭粯璁ゅ弬浼氬悕鍗曪級
--agenda         <csv>                 鑷畾涔変細璁绋嬶紝閫楀彿鍒嗛殧锛堣鐩栭粯璁よ绋嬶級
--project-id     <string>              缁戝畾椤圭洰鐩綍锛堝 001-dewatermark-ai锛夛紝灏嗗啓鍏ャ€愪細璁俊鎭€?```

---

## 10. 鍙樻洿璁板綍

- 2025-10-28
  - 棣栫増锛氭敮鎸佹瘡鏃?绱ф€ヤ細璁紱鏂板浼氳淇℃伅鍧楋紱鏀寔鈥滆鍔ㄩ」涓庡喅绛栤€濅笓灞炴ā鍨嬩笌鍥為€€琛ㄦ牸鏈哄埗銆?  - 鏂板锛欳LI 鑷畾涔?--participants/--agenda锛涘彲閫夌粦瀹?--project-id銆?  - 鏂板锛氫細璁邯瑕?JSON 鍚屾褰掓。锛堝惈缁撴瀯鍖栧尯鍧椾笌琛ㄦ牸瑙ｆ瀽锛夈€?  - 鏂板锛氬畾鏃舵墽琛岃剼鏈?scripts/schedule_daily_meeting.ps1/.bat銆
