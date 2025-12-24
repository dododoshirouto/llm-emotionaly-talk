# Updates

## 2025-12-24
### 環境構築スクリプトの修正
- `voicevox_core` ダウンローダーのエラー回避のため、PowerShellでの直接ダウンロード方式に変更。
- `ollama` ライブラリと `voicevox_core` の `pydantic` バージョン競合を解決するため、`ollama` ライブラリを削除（HTTPリクエストでの代替を予定）。
- `setup.ps1` を更新。

### 環境構築スクリプトの作成
- `_install.bat` および `setup.ps1` を作成し、環境構築を自動化。
- `.gitignore` を更新し、`venv` や `voicevox_core` を除外。
- `requirements.txt` を作成。
