# 🚀 LiPeaks Backend - エンタープライズマルチテナントSaaSプラットフォームバックエンドシステム

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2+-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📖 プロジェクト概要

LiPeaks Backendは、Django 5.2を基盤としたエンタープライズレベルのマルチテナントSaaSプラットフォームバックエンドシステムです。先進的なマルチテナントアーキテクチャ設計を採用し、異なる組織やクライアント（テナント）に完全に分離されたアプリケーション環境を提供します。

## ✨ 主要機能

- 🔐 **マルチテナントアーキテクチャ** - データの完全分離、無制限のテナント拡張をサポート
- 👥 **ユーザー権限管理** - RBAC権限システム、細かい制御
- 📝 **コンテンツ管理システム** - 記事、メディア、テンプレート管理
- 💼 **顧客関係管理** - 顧客情報、分類、追跡
- 📋 **注文管理システム** - ビジネスプロセス、コスト管理
- ⏰ **チェックインシステム** - タスク管理、統計分析
- 🍽️ **メニュー管理** - 動的メニュー、権限制御
- 📊 **チャート分析** - データ可視化、レポート生成

## 🏗️ 技術アーキテクチャ

- **バックエンドフレームワーク**: Django 5.2 + Django REST Framework
- **データベース**: MySQL 8.0+ (PyMySQLドライバー)
- **認証**: JWT + RBAC権限システム
- **APIドキュメント**: OpenAPI 3.0 + Swagger UI
- **デプロイ**: Docker + Nginx + Gunicorn

## 🚀 クイックスタート

### 要件
- Python 3.9+
- MySQL 8.0+
- Redis 6.0+ (オプション)

### Dockerワンクリックデプロイ
```bash
# プロジェクトをクローン
git clone https://github.com/fx0883/lipeaks_backend.git
cd lipeaks_backend

# サービスを開始
docker-compose up -d

# データベースを初期化
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

### Python環境でのデプロイ
```bash
# 仮想環境を作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係をインストール
pip install -r requirements.txt

# 環境変数を設定
cp .env.sample .env
# .envファイルを編集

# データベースマイグレーション
python manage.py migrate
python manage.py createsuperuser

# サービスを開始
python manage.py runserver
```

## 📚 APIドキュメント

- **Swagger UI**: `/api/v1/docs/`
- **ReDoc**: `/api/v1/redoc/`
- **OpenAPI Schema**: `/api/v1/schema/`

## 🔧 設定

### 環境変数
```bash
SECRET_KEY=your-secret-key
DEBUG=False
DB_NAME=lipeaks_db
DB_USER=lipeaks_user
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=3306
```

### データベース設定
```sql
CREATE DATABASE lipeaks_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'lipeaks_user'@'localhost' IDENTIFIED BY 'your-password';
GRANT ALL PRIVILEGES ON lipeaks_db.* TO 'lipeaks_user'@'localhost';
```

## 🛠️ 開発ガイド

### プロジェクト構造
```
lipeaks_backend/
├── core/           # コア設定
├── users/          # ユーザー管理
├── tenants/        # テナント管理
├── rbac/           # 権限管理
├── cms/            # コンテンツ管理
├── customers/      # 顧客管理
├── orders/         # 注文管理
├── check_system/   # チェックインシステム
├── menus/          # メニュー管理
├── charts/         # チャート分析
└── common/         # 共通機能
```

### 開発環境
```bash
# 開発依存関係をインストール
pip install -r requirements-dev.txt

# コードフォーマット
black .
isort .

# テストを実行
python manage.py test
```

## 🚀 デプロイガイド

### 本番環境デプロイ
```bash
# Gunicornを使用
gunicorn core.wsgi:application --bind 0.0.0.0:8000

# Dockerを使用
docker-compose -f docker-compose.prod.yml up -d
```

### Nginx設定
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location /static/ {
        alias /path/to/staticfiles/;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔒 セキュリティ機能

- JWT認証メカニズム
- テナントデータ分離
- RBAC権限制御
- CSRF保護
- XSS保護
- SQLインジェクション保護

## 📈 監視と運用

### ログ管理
- 構造化ログ記録
- ログローテーションと保持
- エラー監視とレポート

### パフォーマンス最適化
- データベースクエリ最適化
- Redisキャッシュサポート
- 静的ファイル最適化

## ❓ よくある質問

**Q: 新しいビジネスモジュールを追加するには？**
A: BaseModelを継承することで、自動的にテナント分離機能を取得できます

**Q: データベースパフォーマンスを最適化するには？**
A: TenantManagerを使用し、適切なインデックスを設定してください

**Q: 本番環境を設定するには？**
A: DEBUG=Falseに設定し、本番データベースを設定し、HTTPSを有効にしてください

## 🤝 貢献

1. プロジェクトをフォーク
2. 機能ブランチを作成
3. 変更をコミット
4. プルリクエストを作成

## 📄 ライセンス

このプロジェクトは[MITライセンス](LICENSE)の下で公開されています

## 📞 お問い合わせ

- **メール**: contact@lipeaks.com
- **問題報告**: [GitHub Issues](https://github.com/fx0883/lipeaks_backend/issues)
- **技術討論**: QQグループ/WeChatグループ

---

<div align="center">

**このプロジェクトがお役に立てば、⭐ Starをお願いします！**

[LiPeaks Team](https://github.com/fx0883)によって❤️で作られました

</div>
