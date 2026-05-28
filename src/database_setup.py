# -*- coding: utf-8 -*-
import os
from sqlalchemy import create_engine, text, Column, String, Float, DateTime, func
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# 1. Environment & Base Configuration
load_dotenv(override=True)
Base = declarative_base()

# 2. Construct Connection URL
connection_url = URL.create(
    drivername="postgresql+psycopg2",
    username=os.getenv("PGUSER"),
    password=os.getenv("PGPASSWORD"),
    host=os.getenv("PGHOST"),
    port=os.getenv("PGPORT"),
    database=os.getenv("PGDATABASE"),
    query={"sslmode": "require"},
)

# 3. Create the Engine
engine = create_engine(
    connection_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# 4. Session Factory
# This is what allows ToastAPI() to "grab its own key" to the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 5. Token Model (The "Filing Cabinet" Slot)
class APIToken(Base):
    __tablename__ = 'api_tokens'
    service_name = Column(String, primary_key=True)
    access_token = Column(String, nullable=False)
    client_id = Column(String, nullable=False)
    expires_at = Column(Float, nullable=False)
    created_at = Column(Float, nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


def get_engine():
    """Returns the SQLAlchemy engine for orders_pull_Update.py."""
    return engine


def create_tables():
    """Creates the Full Schema including the new api_tokens table."""
    try:
        with engine.begin() as conn:
            # --- AUTHENTICATION TABLE ---
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS api_tokens (
                    service_name TEXT PRIMARY KEY,
                    access_token TEXT NOT NULL,
                    client_id TEXT NOT NULL,
                    expires_at DOUBLE PRECISION NOT NULL,
                    created_at DOUBLE PRECISION NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            '''))

            # --- YOUR EXISTING CONFIG TABLES ---
            conn.execute(text(
                'CREATE TABLE IF NOT EXISTS revenue_centers (guid UUID PRIMARY KEY, name TEXT, description TEXT);'))
            conn.execute(
                text('CREATE TABLE IF NOT EXISTS dining_options (guid UUID PRIMARY KEY, name TEXT, behavior TEXT);'))
            conn.execute(text('CREATE TABLE IF NOT EXISTS services (guid UUID PRIMARY KEY, name TEXT);'))
            conn.execute(text(
                'CREATE TABLE IF NOT EXISTS employees (guid UUID PRIMARY KEY, first_name TEXT, last_name TEXT, email TEXT, deleted BOOLEAN DEFAULT FALSE);'))
            conn.execute(text('CREATE TABLE IF NOT EXISTS sales_categories (guid UUID PRIMARY KEY, name TEXT);'))

            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS service_areas (
                    guid UUID PRIMARY KEY,
                    name TEXT,
                    revenue_center_guid UUID REFERENCES revenue_centers(guid) ON DELETE SET NULL
                );
            '''))

            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS tables (
                    guid UUID PRIMARY KEY, 
                    name TEXT,
                    revenue_center_guid UUID REFERENCES revenue_centers(guid) ON DELETE SET NULL,
                    service_area_guid UUID REFERENCES service_areas(guid) ON DELETE SET NULL
                );
            '''))

            # --- YOUR EXISTING TRANSACTIONAL TABLES ---
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS orders_head (
                    order_guid UUID PRIMARY KEY,
                    location_id TEXT,
                    order_number TEXT,
                    fire_date TIMESTAMPTZ,
                    promised_date TIMESTAMPTZ,
                    created_date TIMESTAMPTZ,
                    closed_date TIMESTAMPTZ,
                    paid_date TIMESTAMPTZ,
                    modified_date TIMESTAMPTZ,
                    deleted_date TIMESTAMPTZ,
                    estimated_fulfillment_date TIMESTAMPTZ,
                    business_date INTEGER,
                    required_prep_time TEXT,
                    number_of_guests INTEGER,
                    approval_status TEXT,
                    deleted BOOLEAN DEFAULT FALSE,
                    source TEXT,
                    dining_option_guid UUID REFERENCES dining_options(guid),
                    service_area_guid UUID REFERENCES service_areas(guid),
                    restaurant_service_daypart UUID REFERENCES services(guid), 
                    revenue_center_guid UUID REFERENCES revenue_centers(guid),
                    server_guid UUID REFERENCES employees(guid),
                    last_sync_timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );
            '''))

            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS order_checks (
                    check_guid UUID PRIMARY KEY,
                    order_guid UUID REFERENCES orders_head(order_guid) ON DELETE CASCADE,
                    payment_status TEXT,
                    tax_exempt BOOLEAN DEFAULT FALSE,
                    total_amount NUMERIC(12,2),
                    tax_amount NUMERIC(12,2),
                    net_amount NUMERIC(12,2),
                    tab_name TEXT,
                    customer_first TEXT,
                    customer_last TEXT,
                    customer_phone TEXT,
                    customer_email TEXT,
                    opened_date TIMESTAMPTZ,
                    closed_date TIMESTAMPTZ,
                    voided BOOLEAN DEFAULT FALSE
                );
            '''))

            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS order_items (
                    selection_guid UUID PRIMARY KEY,
                    check_guid UUID REFERENCES order_checks(check_guid) ON DELETE CASCADE,
                    item_guid UUID,
                    item_name TEXT,
                    quantity NUMERIC(12,3),
                    unit_price NUMERIC(12,2),
                    net_price NUMERIC(12,2),
                    deferred BOOLEAN DEFAULT FALSE,
                    tax_amount NUMERIC(12,2),
                    voided BOOLEAN DEFAULT FALSE,
                    fulfillment_status TEXT,
                    plu TEXT,
                    sales_category_guid UUID REFERENCES sales_categories(guid),
                    item_group_guid UUID
                );
            '''))

            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS item_modifiers (
                    modifier_guid UUID PRIMARY KEY,
                    selection_guid UUID REFERENCES order_items(selection_guid) ON DELETE CASCADE,
                    item_guid UUID,
                    mod_name TEXT,
                    quantity NUMERIC(12,3),
                    mod_unit_price NUMERIC(12,2),
                    mod_net_price NUMERIC(12,2),
                    deferred BOOLEAN DEFAULT FALSE,
                    voided BOOLEAN DEFAULT FALSE
                );
            '''))

        print("Azure Postgres: All tables (including api_tokens) verified.")
    except SQLAlchemyError as e:
        print(f"Error creating tables: {e}")


def rebuild_database():
    """Drops and recreates everything for a clean slate."""
    tables = [
        "item_modifiers", "order_items", "order_checks", "orders_head",
        "tables", "service_areas", "sales_categories", "employees",
        "services", "dining_options", "revenue_centers", "api_tokens"
    ]
    try:
        with engine.begin() as conn:
            print("Dropping all existing tables...")
            for table in tables:
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
        create_tables()
        print("Azure Postgres database successfully reconstructed.")
    except SQLAlchemyError as e:
        print(f"Error rebuilding database: {e}")


if __name__ == "__main__":
    rebuild_database()