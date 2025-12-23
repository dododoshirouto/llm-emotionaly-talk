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
   * 必須オプション: 
     * `logprobs=True`
     * `top_logprobs=5` (エントロピー計算用に上位5候補を取得)

3. **データ構造化**: 受信したレスポンスを以下の構造のリストに変換する。
```python
raw_tokens = [
    {
        "token": "Hello", 
        "top_logprobs": {'Hello': -0.1, 'Hi': -2.5, ...}, # 上位候補の対数確率
        "latency": 0.1
    },
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

#### ルートA: 感情・迷い解析と物理演算

各トークンのメタデータから、2つの主要な感情軸を算出し、変調パラメータを決定する。

1. **基本指標の算出**:
   * **Confidence (自信)**: `prob` (トップトークンの確率 $0.0 \sim 1.0$) をそのまま使用。
     * 自信があるほど値が大きい。
   * **Confusion (迷い)**: `top_logprobs` から **Shannon Entropy** を算出。
     * $H = - \sum p \log p$
     * 迷っている（候補が多い）ほど値が大きい。

2. **減衰計算 (物理モデル)**:
   * 漸化式: `Val_Current = (Val_Prev * DECAY_RATE) + (Input - BASELINE)`
   * **Pitch変調用 inputs**: `Confidence` ($1.0 - prob$ などで反転させるか、そのまま使うかは調整)
   * **Speed変調用 inputs**: `Confusion` (Entropy)

#### ルートB: AudioQuery作成

音声合成のベースとなる設計図を作成する。

1. **全文生成**: トークンリストの `token` (原文) を全て結合する。
2. **Query生成**: `core.audio_query(full_text, speaker_id)` を実行。
3. **参照展開**: 生成された `AudioQuery` 内の全モーラ (`phrase.moras`) を1次元リストに展開する。

### Phase 4 & 5: アライメントと単純加算変調

算出した「変位量」を、VOICEVOXのパラメータに直接加算する。

**マッピング定義:**

| 指標 | 計算元 | 意味 | マッピング先 | 挙動 |
| --- | --- | --- | --- | --- |
| **Confidence** | **Prob** (確率) | 値が高いほど自信あり | **Pitch** | 確率が**低い**（自信がない）時、ピッチを揺らす/下げる |
| **Confusion** | **Entropy** (エントロピー) | 値が高いほど迷っている | **Speed** | エントロピーが**高い**（迷っている）時、**ゆっくり**話す (Speedを下げる) |

1. **マッピングループ**:
   * トークンリストを順に処理し、対応するモーラに対して物理演算で求めた変位を加算する。

2. **加算適用**:
   * **Pitch (音高)**:
     * `Confidence` (prob) が低い → ピッチ不安定化（震えなど）。
   * **Speed (長さ)**:
     * `Confusion` (entropy) が高い（迷い） → Speedを下げる（滞る）。
     * `Confusion` (entropy) が低い（スムーズ） → Speedを上げる（流暢）。
     * ※ `latency` も補助的に使うとよりリアルかも（要検討）。

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