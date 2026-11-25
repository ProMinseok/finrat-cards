# spec.json 형식

```json
{"prefix": "finrat_ai_1126_0730", "slot": "0730", "cards": [ <cover>, <body>..., <cta> ]}
```
텍스트 안에서는 줄바꿈용 `<br>`만 쓸 수 있다. 전체 예시: `examples/2026-11-25-2100.json`.

## kind: cover
`date_label`(예 "2026.11.26 THU · US CLOSE"), `kicker`(작은 제목), `big`(큰 숫자, 예 "−6.16%" 또는 "22:30", 선택), `big_dir`("up"/"down", 생략 시 노랑), `big_size`(기본 180, 긴 문자열이면 130~150), `headline`(2줄 이내), `chips`(3개 이하), `footer`.

## kind: body
`kicker_right`(오른쪽 위 기준 시각·설명), `title`(2줄 이내), `gap`(기본 30), `blocks`(2~3개):
- `rows`: {"label"?, "rows":[{"name","value","change","dir":"up|down|flat"}]} — 최대 5행
- `stats`: {"label"?, "items":[{"name","value","dir"}]} — 2~4칸 (수급 등)
- `bars`: {"label"?, "items":[{"label","value","pct"}]} — 2~5개 (일별 등락)
- `compare`: {"header":[라벨, 이전, 이번], "rows":[{"name","a","b"}]}
- `numbered`: {"label"?, "items":[{"title","body"}]} — 최대 3개
- `boxes`: {"label"?, "items":[{"title","body"}]} — 최대 3개
- `timeline`: {"label"?, "items":[{"time","title","body"}]} — 최대 5개
- `scenarios`: {"label"?, "items":[{"title","body","tone":"up|down"}], "note"?} — 2개

## kind: cta
`big`(다음 게시 시각), `headline`, `chips`, `source`.
