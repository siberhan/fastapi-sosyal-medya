from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# --- SENİN PROJENE ÖZEL AYARLAR ---
from app.models import Base  # Tablolarını (Metadata) buradan alacak
from app.config import settings # Veritabanı şifresini buradan alacak
# ----------------------------------

# Alembic Config nesnesi
config = context.config

# Loglama ayarları
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- KRİTİK AYAR 1: Metadata Bağlantısı ---
# Alembic'in senin tablolarını tanıması için bu satır şart!
target_metadata = Base.metadata

# --- KRİTİK AYAR 2: Dinamik Veritabanı URL'si ---
# alembic.ini dosyasındaki dummy URL yerine, senin gerçek ayarlarını kullanıyoruz.
db_url = f"postgresql+psycopg2://{settings.database_username}:{settings.database_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}"
config.set_main_option("sqlalchemy.url", db_url)


def run_migrations_offline() -> None:
    """Veritabanına bağlanmadan SQL çıktısı üretir."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Veritabanına bağlanıp değişiklikleri uygular."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()