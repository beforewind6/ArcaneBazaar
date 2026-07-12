import mysql.connector
import json
from datetime import date, datetime, timedelta
from decimal import Decimal

from config import DB_CONFIG
from create_logger import setup_logger
from utils.format import DateEncoder, default_encoder

logger = setup_logger("BazaarService")


class BazaarService:
    def __init__(self):
        self.conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"],
        )

    def execute_query(self, sql: str) -> str:
        try:
            cursor = self.conn.cursor(dictionary=True)
            cursor.execute(sql)
            results = cursor.fetchall()
            cursor.close()
            for result in results:
                for key, value in result.items():
                    if isinstance(value, (date, datetime, timedelta, Decimal)):
                        result[key] = default_encoder(value)
            return json.dumps(
                {"status": "success", "data": results}
                if results
                else {"status": "no_data", "message": "未找到数据，请确认查询条件。"},
                cls=DateEncoder,
                ensure_ascii=False,
            )
        except Exception as e:
            logger.error(f"查询错误: {str(e)}")
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)
