"""SQLite 数据库管理"""
import sqlite3
from typing import List, Optional
from contextlib import contextmanager
from pathlib import Path
from ..models.robot import RobotConfig
from ..config import DATABASE_PATH


class RobotDatabase:
    """机械臂数据库"""

    def __init__(self, db_path: Path = DATABASE_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS robots (
                    id TEXT PRIMARY KEY,
                    robot_type TEXT NOT NULL,
                    port TEXT NOT NULL,
                    nickname TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    @contextmanager
    def _get_conn(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def save_robot(self, config: RobotConfig):
        """保存机械臂配置"""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO robots (id, robot_type, port, nickname, notes, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (config.id, config.robot_type.value, config.port, config.nickname, config.notes))

    def get_robot(self, robot_id: str) -> Optional[RobotConfig]:
        """获取机械臂配置"""
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM robots WHERE id = ?", (robot_id,)).fetchone()
            if row:
                return RobotConfig(**dict(row))
        return None

    def list_robots(self) -> List[RobotConfig]:
        """列出所有机械臂"""
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM robots ORDER BY created_at DESC").fetchall()
            return [RobotConfig(**dict(row)) for row in rows]

    def update_robot(self, robot_id: str, **kwargs):
        """更新机械臂信息"""
        fields = []
        values = []
        for k, v in kwargs.items():
            if v is not None and k in ["nickname", "notes", "port"]:
                fields.append(f"{k} = ?")
                values.append(v)

        if fields:
            values.append(robot_id)
            with self._get_conn() as conn:
                conn.execute(f"""
                    UPDATE robots
                    SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, values)

    def delete_robot(self, robot_id: str):
        """删除机械臂"""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM robots WHERE id = ?", (robot_id,))
