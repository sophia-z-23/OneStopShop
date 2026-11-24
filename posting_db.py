"""Database helpers for business postings (items and scheduling)"""

import cs304dbi as dbi


def is_business(conn, account_id):
    """Return True if this account has a row in the business table"""
    with dbi.dict_cursor(conn) as curs:
        curs.execute('''select account_id from business where account_id = %s''',
                     [account_id])
        return curs.fetchone() is not None


def insert_posting(conn, account_id, post_type, title, price, description):
    """Insert a posting with no image yet and return its new post_id
    Does not commit; the caller commits after the image is saved"""
    with dbi.dict_cursor(conn) as curs:
        curs.execute('''insert into posting
                            (account_id, post_type, title, price, description,
                             created_at)
                        values (%s, %s, %s, %s, %s, now())''',
                     [account_id, post_type, title, price, description])
        return curs.lastrowid


def set_image(conn, post_id, filename):
    """Record the saved image's filename for a posting"""
    with dbi.dict_cursor(conn) as curs:
        curs.execute('''update posting set image_link = %s where post_id = %s''',
                     [filename, post_id])


def insert_time_slot(conn, post_id, start_time, end_time):
    """Add one open (unbooked) time slot to a scheduling posting.
    customer_id stays NULL until a customer books the slot"""
    with dbi.dict_cursor(conn) as curs:
        curs.execute('''insert into time_slot
                            (post_id, start_time, end_time, customer_id)
                        values (%s, %s, %s, NULL)''',
                     [post_id, start_time, end_time])


def get_posting(conn, post_id):
    """Return one posting as a dict or None"""
    with dbi.dict_cursor(conn) as curs:
        curs.execute('''select post_id, account_id, post_type, title, price,
                               description, image_link, created_at
                        from posting
                        where post_id = %s''',
                     [post_id])
        return curs.fetchone()


def get_postings_by_account(conn, account_id):
    """Return all postings made by one account, newest first"""
    with dbi.dict_cursor(conn) as curs:
        curs.execute('''select post_id, post_type, title, price, image_link,
                               created_at
                        from posting
                        where account_id = %s
                        order by created_at desc, post_id desc''',
                     [account_id])
        return curs.fetchall()


def get_time_slots(conn, post_id):
    """Return the time slots for a posting"""
    with dbi.dict_cursor(conn) as curs:
        curs.execute('''select slot_id, start_time, end_time, customer_id
                        from time_slot
                        where post_id = %s
                        order by start_time''',
                     [post_id])
        return curs.fetchall()