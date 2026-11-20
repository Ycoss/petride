# conexion a redis cloud, la url se lee del .env
import os
from dotenv import load_dotenv
from redis_om import get_redis_connection

load_dotenv()

redis_conn = get_redis_connection(
    url=os.getenv("REDIS_URL"),
    decode_responses=True
)
