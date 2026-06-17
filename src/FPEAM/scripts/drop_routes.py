import psycopg2
import logging
from multiprocessing import Pool

logging.basicConfig(level=logging.INFO)


def get_views(cur):
    _sql = """SELECT table_name FROM information_schema.tables WHERE table_schema = 'groads~' AND table_name LIKE '0%_geom' LIMIT 100;"""
    cur.execute(_sql)
    return [x[0] for x in cur.fetchall()]


def get_tables(cur):
    _sql = """SELECT table_name FROM information_schema.tables WHERE table_schema = 'groads~' AND table_name LIKE '0%' LIMIT 10;"""
    cur.execute(_sql)
    return [x[0] for x in cur.fetchall()]


def drop_view(view):
    logging.info(view)
    _sql = """DROP VIEW IF EXISTS "groads~"."{t}" CASCADE;""".format(t=view)
    cur.execute(_sql)


def drop_table(table):
    logging.info(table)
    _sql = """DROP TABLE "groads~"."{t}" CASCADE;""".format(t=table)
    cur.execute(_sql)


with psycopg2.connect(host='localhost', dbname='fpeam_topology') as conn:
    with conn.cursor() as cur:
        views = get_views(cur)
        while views:
            with Pool(processes=10) as pool:
                pool.map(drop_view, views)
            conn.commit()
            views = get_views(cur)

        tables = get_tables(cur)
        while tables:
            with Pool(processes=10) as pool:
                pool.map(drop_table, tables)
            conn.commit()
            tables = get_tables(cur)
