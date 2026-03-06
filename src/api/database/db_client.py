from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Generator, List, Optional, Tuple, Type, TypeVar, cast

import mysql.connector

from src.api.configs.config import Config

T = TypeVar("T")


class RequestType(str, Enum):
    SELECT = "SELECT"
    DELETE = "DELETE"


def _db_config() -> dict:
    """
    Конфигурация для MySQL/MariaDB в виде словаря.
    """
    return {
        "host": str(Config.get("DB_HOST", "localhost")),
        "port": int(Config.get("DB_PORT", 3306)),  # Порт MariaDB по умолчанию
        "database": str(Config.get("DB_NAME", "openmrs")),
        "user": str(Config.get("DB_USERNAME", "openmrs")),
        "password": str(Config.get("DB_PASSWORD", "openmrs"))
    }


@contextmanager
def db_conn() -> Generator[mysql.connector.MySQLConnection, None, None]:
    conn = mysql.connector.connect(**_db_config())
    try:
        yield conn
    finally:
        if conn.is_connected():
            conn.close()


def fetch_one(sql: str, params: Optional[tuple[Any, ...]] = None) -> Optional[Dict[str, Any]]:
    with db_conn() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute(sql, params or ())
            row = cur.fetchone()
            return row


def fetch_all(sql: str, params: Optional[tuple[Any, ...]] = None) -> Optional[List[Dict[str, Any]]]:
    with db_conn() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute(sql, params or ())
            return cast(List[Dict[str, Any]], cur.fetchall())


def execute_non_query(sql: str, params: Optional[tuple[Any, ...]] = None) -> int:
    """Выполняет UPDATE/DELETE/INSERT и возвращает количество измененных строк."""
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            conn.commit()  # Важно для MariaDB/MySQL
            return cur.rowcount


@dataclass(frozen=True)
class Condition:
    """
    Simple WHERE condition builder for SQL queries.
    Supports equality and AND-chaining (enough for our test checks).
    """

    sql: str
    params: Tuple[Any, ...]

    @staticmethod
    def equal_to(column: str, value: Any) -> "Condition":
        return Condition(sql=f"{column} = %s", params=(value, ))

    @staticmethod
    def raw(sql: str, *params: Any) -> "Condition":
        """
        Allows passing custom SQL condition with parameters.
        Example:
            Condition.raw("DATE(p.birthdate) = DATE(%s)", birthdate)
        """
        return Condition(sql=sql, params=tuple(params))

    @staticmethod
    def and_(*conditions: "Condition") -> "Condition":
        conds = [c for c in conditions if c is not None]
        if not conds:
            raise ValueError("At least one condition is required")
        sql = " AND ".join(f"({c.sql})" for c in conds)  # (a = %s) AND (b = %s)
        params: Tuple[Any, ...] = tuple(p for c in conds for p in c.params)  # ("alex") (1, ) -> ("alex", 1)
        return Condition(sql=sql, params=params)


class DBRequest:
    @staticmethod
    def builder() -> "DBRequestBuilder":
        return DBRequestBuilder()


class DBRequestBuilder:
    def __init__(self):
        self._request_type: Optional[RequestType] = None
        self._table: Optional[str] = None
        self._where: Optional[Condition] = None
        self._joins: list[str] = []

    def request_type(self, request_type: RequestType) -> "DBRequestBuilder":
        self._request_type = request_type
        return self

    def table(self, table: str) -> "DBRequestBuilder":
        self._table = table
        return self

    def where(self, condition: Condition) -> "DBRequestBuilder":
        self._where = condition
        return self

    def join(self, table: str, condition: str) -> "DBRequestBuilder":
        """
        Adds INNER JOIN to the query.
        Example:
            .join("person_name pn", "pn.person_id = p.person_id")
        """
        self._joins.append(f"JOIN {table} ON {condition}")
        return self

    def extract_as(self, dao_cls: Type[T]) -> T:
        if self._request_type != RequestType.SELECT:
            raise NotImplementedError(f"Request type not supported: {self._request_type}")
        if not self._table:
            raise ValueError("Table is required")

        sql = f"SELECT * FROM {self._table}"

        if self._joins:
            sql += " " + " ".join(self._joins)

        params: tuple[Any, ...] = ()
        if self._where:
            sql += f" WHERE {self._where.sql}"
            params = self._where.params
        sql += " LIMIT 1"

        row = fetch_one(sql, params)
        if row is None:
            raise AssertionError(f"DB row not found. SQL={sql}, params={params}")

        return dao_cls(**row)  # type: ignore[arg-type]

    def extract_optional_as(self, dao_cls: Type[T]) -> Optional[T]:
        if self._request_type != RequestType.SELECT:
            raise NotImplementedError(f"Request type not supported: {self._request_type}")
        if not self._table:
            raise ValueError("Table is required")

        sql = f"SELECT * FROM {self._table}"

        if self._joins:
            sql += " " + " ".join(self._joins)

        params: tuple[Any, ...] = ()
        if self._where:
            sql += f" WHERE {self._where.sql}"
            params = self._where.params
        sql += " LIMIT 1"

        row = fetch_one(sql, params)
        if row is None:
            return None
        return dao_cls(**row)  # type: ignore[arg-type]

    def extract_all_as(self, dao_cls: Type[T]) -> list[T]:
        if self._request_type != RequestType.SELECT:
            raise NotImplementedError(f"Request type not supported: {self._request_type}")
        if not self._table:
            raise ValueError("Table is required")

        sql = f"SELECT * FROM {self._table}"

        if self._joins:
            sql += " " + " ".join(self._joins)

        params: tuple[Any, ...] = ()

        if self._where:
            sql += f" WHERE {self._where.sql}"
            params = self._where.params

        rows = fetch_all(sql, params)
        return [dao_cls(**row) for row in rows]

    def execute(self) -> int:
        """Метод для выполнения DELETE запросов."""
        if self._request_type != RequestType.DELETE:
            raise NotImplementedError(f"Use extract methods for {self._request_type}")
        if not self._table:
            raise ValueError("Table is required")

        sql = f"DELETE FROM {self._table}"
        params: tuple[Any, ...] = ()

        if self._where:
            sql += f" WHERE {self._where.sql}"
            params = self._where.params
        else:
            # Защита от случайного удаления всей таблицы
            raise ValueError("DELETE request must have a WHERE condition for safety")

        return execute_non_query(sql, params)
