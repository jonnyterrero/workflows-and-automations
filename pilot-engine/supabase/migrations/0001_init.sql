create table pilot_trades (
  id            bigint generated always as identity primary key,
  pilot         text not null,              -- e.g. 'pelosi'
  politician    text,                       -- raw name from source
  ticker        text not null,
  asset_type    text default 'equity',      -- equity | option | bond | crypto
  txn_type      text not null,              -- purchase | sale | exchange
  txn_date      date,
  filed_date    date,                       -- disclosure date (lag lives here)
  amount_low    numeric,                    -- STOCK Act ranges
  amount_high   numeric,
  owner         text,                       -- self | spouse | child
  source_url    text,
  source        text not null,              -- capitol_trades | edgar | quiver
  raw           jsonb,
  dedupe_hash   text unique not null,       -- sha256(pilot|ticker|txn_date|txn_type|amount_low)
  ingested_at   timestamptz default now()
);

create table pilot_holdings (
  pilot      text not null,
  ticker     text not null,
  weight     numeric not null,              -- 0–1
  as_of      date not null,
  primary key (pilot, ticker, as_of)
);

create table target_weights (
  pilot      text not null,
  ticker     text not null,
  weight     numeric not null,
  computed_at timestamptz default now(),
  primary key (pilot, ticker)
);

create table proposed_orders (
  batch_id    uuid not null,
  ticker      text not null,
  side        text not null,                -- buy | sell
  notional    numeric not null,             -- dollars, fractional-ok
  rationale   text,
  status      text default 'pending',       -- pending | approved | rejected | executed | failed
  created_at  timestamptz default now(),
  decided_at  timestamptz,
  primary key (batch_id, ticker)
);

create table order_executions (
  id              bigint generated always as identity primary key,
  batch_id        uuid not null,
  ticker          text not null,
  side            text not null,
  notional        numeric,
  broker_order_id text,
  fill_price      numeric,
  fill_qty        numeric,
  status          text,
  executed_at     timestamptz default now(),
  foreign key (batch_id, ticker) references proposed_orders (batch_id, ticker)
);

create table validation_log (
  id             bigint generated always as identity primary key,
  pilot          text not null,
  signal_date    date not null,
  diy_signal     jsonb,                     -- what WE would have done
  autopilot_fill jsonb,                     -- what Autopilot actually did (from Public history)
  match          boolean,
  notes          text,
  created_at     timestamptz default now()
);

create table source_register (
  source_id   text primary key,
  name        text,
  url         text,
  type        text,                         -- scraper | api | filing
  reliability text,                         -- A | B | C
  last_ok     timestamptz,
  notes       text
);
