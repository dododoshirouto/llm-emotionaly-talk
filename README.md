# 詳細仕様書：動的感情韻律変調システム (End-to-End Flow)

## 1. システム概要

本システムは、Ollamaを用いたAIキャラクターとの対話セッションにおいて、生成された回答の「意味（テキスト）」だけでなく「生成過程の感情（メタデータ）」を解析し、VOICEVOXによる音声合成時に「声の震え・上ずり・早口」として物理的に反映させるパイプラインである。

## 2. 処理フロー図 (Mermaid)

```mermaid
graph TD
    %% Phase 1: AI Generation
    Start[開始] --> Init[Ollama会話セッション作成<br>キャラプロンプト設定]
    Init --> Input[ユーザー入力送信]
    Input --> Recv[レスポンス受信<br>(ストリーミング/バッファリング)]
    
    %% Phase 2: Pre-processing
    Recv --> TokenProc[トークンリスト化]
    TokenProc --> Eng2Kana[トークンごとの日英変換処理<br>(eng_to_kana / pykakasi)]
    
    %% Phase 3: Parallel Processing
    Eng2Kana --> BranchA{ルートA: 感情解析}
    Eng2Kana --> BranchB{ルートB: 音声基盤}
    
    %% Route A: Physics
    BranchA --> CalcEmo[感情メトリクス抽出<br>Confidence / Interest]
    CalcEmo --> Physics[減衰物理演算<br>変位量の算出]
    
    %% Route B: Base Audio
    BranchB --> JoinText[全文結合]
    JoinText --> GenQuery[VoicevoxCore.audio_query<br>AudioQuery生成]
    
    %% Phase 4: Integration
    Physics --> Alignment[アライメント処理]
    GenQuery --> Alignment
    Alignment --> Mapping[モーラ/トークン対応付け]
    
    %% Phase 5: Modulation
    Mapping --> ModPitch[ピッチ変調<br>(単純加算)]
    Mapping --> ModSpeed[スピード/長さ変調<br>(単純加算)]
    
    %% Phase 6: Output
    ModSpeed --> Synth[VoicevoxCore.synthesis<br>音声生成]
    Synth --> Save[WAVファイル保存]
    Save --> End[完了]

```

## 3. 定数・設定定義

* **物理演算パラメータ**
* `DECAY_RATE` (減衰率): `0.5`
* `BASELINE_SCORE` (基準値): `0.5`


* **感度パラメータ (単純加算用係数)**
* `PITCH_COEFF` (ピッチ係数): 例 `0.5` (スコア1.0で +0.5Hz相当の変化 ※単位は調整要)
* `SPEED_COEFF` (速度係数): 例 `-0.05` (スコア1.0で母音長を -0.05秒短縮＝早口)



## 4. 詳細処理ステップ

### Phase 1: Ollamaセッションと受信

1. **セッション初期化**: システムプロンプト（キャラ設定）を含むメッセージ履歴を作成。
2. **クエリ送信**: ユーザー入力を追記し、Ollama APIへリクエスト (`stream=False` または全受信待ち)。
* 必須オプション: `logprobs=True` (感情解析用)


3. **データ構造化**: 受信したレスポンスを以下の構造のリストに変換する。
```python
raw_tokens = [
    {"token": "Hello", "prob": 0.9, "latency": 0.1},
    {"token": "、", "prob": 0.99, "latency": 0.05},
    {"token": "world", "prob": 0.6, "latency": 0.2},
    ...
]

```



### Phase 2: トークンごとの日英変換 (Preprocessing)

各トークンの文字列に対し、読み（発音）ベースの長さを確定させる。

1. **英単語判定**: トークンが `[a-zA-Z]+` の場合、`alkana` 等でカタカナ変換（例: "Hello" → "ハロー"）。
2. **日本語判定**: 漢字混じりの場合、`pykakasi` でカタカナ変換（例: "世界" → "セカイ"）。
3. **モーラ数確定**: 変換後のカナ文字数を、そのトークンの「消費モーラ数」として保持する。
* *データ更新:* `{"token": "Hello", "kana": "ハロー", "mora_count": 3, ...}`



### Phase 3: 並列処理 (分岐)

#### ルートA: 感情分析と物理演算

各トークンのメタデータから、適用すべき「変位量」を計算する。

1. **正規化**: `prob` (確率) や `latency` (遅延) を `0.0`〜`1.0` に正規化し、`confidence`, `interest` とする。
2. **減衰計算 (物理モデル)**:
* 漸化式: `Val_Current = (Val_Prev * DECAY_RATE) + (Input - BASELINE)`
* これをピッチ用変位 `mod_p` と、速度用変位 `mod_s` それぞれで算出する。



#### ルートB: AudioQuery作成

音声合成のベースとなる設計図を作成する。

1. **全文生成**: トークンリストの `token` (原文) を全て結合する。
2. **Query生成**: `core.audio_query(full_text, speaker_id)` を実行。
3. **参照展開**: 生成された `AudioQuery` 内の全モーラ (`phrase.moras`) を1次元リストに展開する。

### Phase 4 & 5: アライメントと単純加算変調

算出した「変位量」を、VOICEVOXのパラメータに直接加算する。

1. **マッピングループ**:
* トークンリストを順に処理。
* トークンが持つ `mora_count` 分だけ、AudioQueryのモーラリストを進める。


2. **単純加算適用 (Simple Addition)**:
* 対象モーラに対して、物理演算で求めた変位を加算する。
* **Pitch (音高):**


* 効果: 自信があれば音が高く、なければ低くなる（またはその逆）。


* **Speed (母音長/子音長):**
* ※VoicevoxCoreには `speedScale` があるが、モーラごとの制御をするため `length` を操作する。
* 興味が高い＝早口＝長さが**減る**必要がある。


* *注意*: `SPEED_COEFF` は負の値（例: -0.05）を設定し、興味スコアが高いほど長さが引かれる（短くなる）ようにする。
* *ガード処理*: 結果が `0.01` 未満にならないよう `max(0.01, result)` でクリップする。





### Phase 6: 生成と保存

1. **音声合成**: 変調済みの `AudioQuery` を `core.synthesis` に渡す。
2. **ファイル出力**: 返却されたバイナリデータを `output.wav` として書き出す。

## 5. 実装時に必要なライブラリ構成

* `ollama` (または `openai`): API通信
* `voicevox_core`: 音声合成エンジン
* `pykakasi`: 日本語読み変換
* `alkana`: 英単語読み変換
* `numpy`: (オプション) 数値計算用だが、今回は単純計算なのでPython標準でも可

## 参考(Reference)

### ZundaYomiageWinNotif

VOICEVOX_coreのインストール/利用部分

en-to-jaのロジック