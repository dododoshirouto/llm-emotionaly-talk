# 実装計画: LLM Emotional Talk (動的感情韻律変調システム)

本ドキュメントは、LLMの生成確率（確信度）に基づいてVOICEVOXの音声パラメータを動的に操作し、感情豊かな発話を実現するシステムの実装計画である。

## 1. フェーズ分けとマイルストーン

### Phase 0: 環境準備と依存関係の整理
開発に必要なライブラリと外部リソースを配置し、最小限の実行環境を整える。

- [ ] **依存ライブラリの定義** (`requirements.txt`)
    - `ollama`
    - `voicevox_core` (公式のwhlまたはSDKを使用)
    - `pykakasi`
    - `numpy`
    - `pyaudio` (音声再生用)
- [ ] **外部リリースの配置**
    - `VOICEVOX CODE (0.16.3)` ライブラリファイル (dll/dylib/so)
    - `open_jtalk_dic_utf_8-1.11`
    - `cmudict-0.7b` 系辞書ファイル (`eng_to_kana`用)

### Phase 1: 基本モジュールの実装 (個別の機能検証)
各コンポーネントを独立したモジュールとして実装し、単体で動作することを確認する。

- [ ] **テキスト処理モジュール** (`src/text_processing.py`)
    - `reference/ZundaYomiageWinNotif/eng_to_kana.py` を移植・改修
    - `pykakasi` を統合し、トークン文字列から「読み（カタカナ）」と「モーラ数」を算出する機能の実装
- [ ] **LLMクライアントモジュール** (`src/llm_client.py`)
    - Ollama APIと通信し、テキスト生成と同時に `logprobs` (Pitch用) と `top_logprobs` (Speed用) を取得する
    - レスポンスをシステム用トークン構造体 (`token`, `prob`, `top_logprobs`, `latency` 等) に正規化する
- [ ] **VOICEVOXアダプタ** (`src/tts_engine.py`)
    - `voicevox_core` (0.16.3) を初期化し、テキストから `AudioQuery` を生成する
    - 変調なしで音声合成(WAV出力)ができるまでのパイプライン構築

### Phase 2: 感情物理演算とアライメントの実装
トークンごとの相対変位と減衰（Decay）計算を実装し、自然な揺らぎを生成する。

- [ ] **物理演算モデル** (`src/physics.py`)
    - **Pitch系の相対変位**: `Confidence` (Prob) から変位衝撃値 ($I_t$) を算出
    - **Speed系の相対変位**: `Confusion` (Entropy) から変位衝撃値 ($I_t$) を算出
    - **減衰シミュレーション**: $V_t = V_{t-1} \times \text{DECAY} + I_t \times \text{SENSITIVITY}$ の漸化式を実装
- [ ] **アライメント処理** (`src/alignment.py`)
    - LLMの「トークン」単位のデータを、VOICEVOXの「モーラ」単位にマッピングするロジック
    - トークンの母音数・モーラ数に基づく長さの同期

### Phase 3: パラメータ変調と統合
計算した変調量を実際に音声データ(`AudioQuery`)に適用し、出力を確認する。

- [ ] **AudioQuery操作**
    - `AudioQuery` 内の `moras` リストに対して、計算したピッチと速度(length)を加算・適用する処理
- [ ] **メインパイプライン** (`main.py`)
    - 入力 → LLM生成 → 解析 → 変調 → 音声合成 → 再生 の一連の流れを結合
    - ストリーミング処理ではなく、まずは一括生成での動作確認を行う

### Phase 4: テストと調整
- [ ] 実際にLLMと対話し、確信度の低い部分で声が震えるか等の挙動確認
- [ ] 係数パラメータ (`PITCH_COEFF`, `DECAY_RATE`) のチューニング

---

## 2. ディレクトリ構成案

```
e:/llm-emotionaly-talk/
├── PLAN.md                 # 本計画書
├── README.md               # 仕様書
├── requirements.txt        # 依存ライブラリ
├── dictionaries/           # 辞書ファイル置き場
│   ├── open_jtalk_dic/
│   └── cmudict/
└── src/
    ├── __init__.py
    ├── main.py             # エントリーポイント
    ├── llm_client.py       # Ollama通信
    ├── text_processing.py  # 日英変換・モーラ計算
    ├── tts_engine.py       # VOICEVOX操作
    ├── physics.py          # 物理演算・感情計算
    └── alignment.py        # トークンとモーラのマッピング
```

## 3. 技術的な懸念点と対応

- **トークンとモーラの不一致**:
    - LLMのトークン区切りと日本語の音韻区切りは必ずしも一致しない。
    - **対応**: `pykakasi` と `eng_to_kana` でおよそのモーラ数を算出し、比率で割り振る簡易マッピングを採用する。厳密なアライメントよりも「それっぽい」感情表現を優先する。
- **VOICEVOX Coreのバージョン**:
    - `reference` のコードはAPIが古い可能性がある。
    - **対応**: 最新の `voicevox_core` (0.15.x以降) の仕様に合わせて実装する。特に `AudioQuery` の構造操作は慎重に行う。
