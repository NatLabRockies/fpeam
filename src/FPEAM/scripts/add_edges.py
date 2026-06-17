import psycopg2
import logging
from multiprocessing import Pool

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(level=logging.DEBUG)
_formatter = logging.Formatter('%(asctime)s, %(levelname)-8s [%(filename)s:%(module)s.%(funcName)s.%(lineno)d] %(message)s')

_chandler = logging.StreamHandler()
_chandler.setLevel(logging.DEBUG)
_chandler.setFormatter(_formatter)

LOGGER.addHandler(_chandler)


def get_max_gid():
    with psycopg2.connect(host='localhost', dbname='fpeam_routing') as conn:
        with conn.cursor() as cur:
            sql = """SELECT max(gid) FROM groads.americas_by_cnty_merge;"""
            cur.execute(sql)
            return cur.fetchone()[0]


def get_min_gid():
    with psycopg2.connect(host='localhost', dbname='fpeam_routing') as conn:
        with conn.cursor() as cur:
            sql = """SELECT min(gid) FROM groads.americas_by_cnty_merge WHERE topo_geom IS NULL;"""
            cur.execute(sql)
            return cur.fetchone()[0]

lower_limit = get_min_gid()
upper_limit = get_max_gid()
step = 1

lower_limit = 247620
upper_limit = 247621

# {'min': 239502, 'max': 240502}
# 2019-04-16 13:42:55,135, ERROR    [add_edges.py:add_edges.<module>.58] Invalid edge (no two distinct vertices exist)
# {'min': 247502, 'max': 248502}
# 2019-04-16 13:53:17,458, ERROR    [add_edges.py:add_edges.<module>.58] SQL/MM Spatial exception - geometry crosses edge 74827

with psycopg2.connect(host='localhost', dbname='fpeam_routing') as conn:
    with conn.cursor() as cur:
        for min in range(lower_limit, upper_limit, step):
            kvals = {'min': min, 'max': min + step}
            LOGGER.info(kvals)
            sql = """UPDATE "groads"."americas_by_cnty_merge" SET "topo_geom" = topology.totopogeom("the_geom_4326", 'groads_topo', 1, 0.001) WHERE "gid" >= %(min)s AND "gid" < %(max)s AND "topo_geom" IS NULL;"""
            try:
                cur.execute(sql, kvals)
                conn.commit()
            except Exception as e:
                LOGGER.error(e)
                conn.rollback()

LOGGER.info('complete!')
