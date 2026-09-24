"""SQLite storage for TK Tally Bot. Everything is scoped per guild (server)."""
from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from typing import Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS tks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id    INTEGER NOT NULL,
    killer_id   INTEGER NOT NULL,
    victim_id   INTEGER NOT NULL,
    reporter_id INTEGER NOT NULL,
    weapon      TEXT,
    game        TEXT,
    created_at  REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tks_killer ON tks(guild_id, killer_id);
CREATE INDEX IF NOT EXISTS idx_tks_victim ON tks(guild_id, victim_id);

CREATE TABLE IF NOT EXISTS achievements (
    guild_id  INTEGER NOT NULL,
    user_id   INTEGER NOT NULL,
    key       TEXT NOT NULL,
    earned_at REAL NOT NULL,
    PRIMARY KEY (guild_id, user_id, key)
);

CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id      INTEGER PRIMARY KEY,
    roles_enabled INTEGER NOT NULL DEFAULT 1
);
"""


@dataclass
class TK:
    id: int
    guild_id: int
    killer_id: int
    victim_id: int
    reporter_id: int
    weapon: Optional[str]
    game: Optional[str]
    created_at: float


class TallyDB:
    def __init__(self, path: str = "tktally.db"):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    # ---- TK records -------------------------------------------------------
    def add_tk(self, guild_id: int, killer_id: int, victim_id: int, reporter_id: int,
               weapon: Optional[str] = None, game: Optional[str] = None,
               now: Optional[float] = None) -> int:
        cur = self.conn.execute(
            "INSERT INTO tks (guild_id, killer_id, victim_id, reporter_id, weapon, game, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (guild_id, killer_id, victim_id, reporter_id, weapon, game, now or time.time()),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_tk(self, tk_id: int) -> Optional[TK]:
        row = self.conn.execute("SELECT * FROM tks WHERE id = ?", (tk_id,)).fetchone()
        return TK(**dict(row)) if row else None

    def remove_tk(self, tk_id: int) -> bool:
        cur = self.conn.execute("DELETE FROM tks WHERE id = ?", (tk_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def last_report_by(self, guild_id: int, reporter_id: int) -> Optional[TK]:
        row = self.conn.execute(
            "SELECT * FROM tks WHERE guild_id = ? AND reporter_id = ? ORDER BY created_at DESC, id DESC LIMIT 1",
            (guild_id, reporter_id),
        ).fetchone()
        return TK(**dict(row)) if row else None

    def last_tk_between(self, guild_id: int, killer_id: int, victim_id: int) -> Optional[TK]:
        row = self.conn.execute(
            "SELECT * FROM tks WHERE guild_id = ? AND killer_id = ? AND victim_id = ?"
            " ORDER BY created_at DESC, id DESC LIMIT 1",
            (guild_id, killer_id, victim_id),
        ).fetchone()
        return TK(**dict(row)) if row else None

    def recent_duplicate(self, guild_id: int, killer_id: int, victim_id: int,
                         window_s: float, now: Optional[float] = None) -> bool:
        """True if the same killer→victim pair was already reported within window_s seconds."""
        cutoff = (now or time.time()) - window_s
        row = self.conn.execute(
            "SELECT 1 FROM tks WHERE guild_id = ? AND killer_id = ? AND victim_id = ? AND created_at >= ?",
            (guild_id, killer_id, victim_id, cutoff),
        ).fetchone()
        return row is not None

    # ---- Stats ------------------------------------------------------------
    def kill_count(self, guild_id: int, user_id: int) -> int:
        """Team kills committed on OTHER people (self-kills are tracked separately)."""
        return self.conn.execute(
            "SELECT COUNT(*) FROM tks WHERE guild_id = ? AND killer_id = ? AND victim_id != killer_id",
            (guild_id, user_id),
        ).fetchone()[0]

    def death_count(self, guild_id: int, user_id: int) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) FROM tks WHERE guild_id = ? AND victim_id = ? AND victim_id != killer_id",
            (guild_id, user_id),
        ).fetchone()[0]

    def self_kill_count(self, guild_id: int, user_id: int) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) FROM tks WHERE guild_id = ? AND killer_id = ? AND victim_id = killer_id",
            (guild_id, user_id),
        ).fetchone()[0]

    def pair_count(self, guild_id: int, killer_id: int, victim_id: int) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) FROM tks WHERE guild_id = ? AND killer_id = ? AND victim_id = ?",
            (guild_id, killer_id, victim_id),
        ).fetchone()[0]

    def kills_since(self, guild_id: int, killer_id: int, since: float) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) FROM tks WHERE guild_id = ? AND killer_id = ? AND victim_id != killer_id"
            " AND created_at >= ?",
            (guild_id, killer_id, since),
        ).fetchone()[0]

    def distinct_victims(self, guild_id: int, killer_id: int) -> int:
        return self.conn.execute(
            "SELECT COUNT(DISTINCT victim_id) FROM tks WHERE guild_id = ? AND killer_id = ? AND victim_id != killer_id",
            (guild_id, killer_id),
        ).fetchone()[0]

    def leaderboard(self, guild_id: int, limit: int = 10) -> list[tuple[int, int]]:
        rows = self.conn.execute(
            "SELECT killer_id, COUNT(*) AS n FROM tks WHERE guild_id = ? AND victim_id != killer_id"
            " GROUP BY killer_id ORDER BY n DESC, MIN(created_at) ASC LIMIT ?",
            (guild_id, limit),
        ).fetchall()
        return [(r[0], r[1]) for r in rows]

    def victim_board(self, guild_id: int, limit: int = 10) -> list[tuple[int, int]]:
        rows = self.conn.execute(
            "SELECT victim_id, COUNT(*) AS n FROM tks WHERE guild_id = ? AND victim_id != killer_id"
            " GROUP BY victim_id ORDER BY n DESC, MIN(created_at) ASC LIMIT ?",
            (guild_id, limit),
        ).fetchall()
        return [(r[0], r[1]) for r in rows]

    def nemesis(self, guild_id: int, victim_id: int) -> Optional[tuple[int, int]]:
        """Who has team-killed this user the most."""
        row = self.conn.execute(
            "SELECT killer_id, COUNT(*) AS n FROM tks WHERE guild_id = ? AND victim_id = ? AND killer_id != victim_id"
            " GROUP BY killer_id ORDER BY n DESC LIMIT 1",
            (guild_id, victim_id),
        ).fetchone()
        return (row[0], row[1]) if row else None

    def favorite_victim(self, guild_id: int, killer_id: int) -> Optional[tuple[int, int]]:
        row = self.conn.execute(
            "SELECT victim_id, COUNT(*) AS n FROM tks WHERE guild_id = ? AND killer_id = ? AND killer_id != victim_id"
            " GROUP BY victim_id ORDER BY n DESC LIMIT 1",
            (guild_id, killer_id),
        ).fetchone()
        return (row[0], row[1]) if row else None

    def reset_user(self, guild_id: int, user_id: int) -> int:
        cur = self.conn.execute(
            "DELETE FROM tks WHERE guild_id = ? AND (killer_id = ? OR victim_id = ?)",
            (guild_id, user_id, user_id),
        )
        self.conn.execute("DELETE FROM achievements WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
        self.conn.commit()
        return cur.rowcount

    # ---- Achievements -----------------------------------------------------
    def award(self, guild_id: int, user_id: int, key: str) -> bool:
        """Grant an achievement. Returns True only the first time."""
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO achievements (guild_id, user_id, key, earned_at) VALUES (?, ?, ?, ?)",
            (guild_id, user_id, key, time.time()),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def achievements(self, guild_id: int, user_id: int) -> list[str]:
        rows = self.conn.execute(
            "SELECT key FROM achievements WHERE guild_id = ? AND user_id = ? ORDER BY earned_at",
            (guild_id, user_id),
        ).fetchall()
        return [r[0] for r in rows]

    # ---- Settings ---------------------------------------------------------
    def roles_enabled(self, guild_id: int) -> bool:
        row = self.conn.execute(
            "SELECT roles_enabled FROM guild_settings WHERE guild_id = ?", (guild_id,)
        ).fetchone()
        return bool(row[0]) if row else True

    def set_roles_enabled(self, guild_id: int, enabled: bool) -> None:
        self.conn.execute(
            "INSERT INTO guild_settings (guild_id, roles_enabled) VALUES (?, ?)"
            " ON CONFLICT(guild_id) DO UPDATE SET roles_enabled = excluded.roles_enabled",
            (guild_id, int(enabled)),
        )
        self.conn.commit()
