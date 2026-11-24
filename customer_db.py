"""Database helpers for what businesses can see about customers"""

import cs304dbi as dbi


def get_customer(conn, account_id):
    """Return a customer's username, email and contact info, or None if
    this account isn't a customer"""
    with dbi.dict_cursor(conn) as curs:
        curs.execute('''select account.account_id, account.username,
                               account.email, customers.contact_info
                        from account
                        join customers on account.account_id = customers.account_id
                        where account.account_id = %s''',
                     [account_id])
        return curs.fetchone()


def get_bookings_with_business(conn, customer_id, business_id):
    """Return the time slots this customer has booked on this
    business's postings, closet to current time first"""
    with dbi.dict_cursor(conn) as curs:
        curs.execute('''select posting.post_id, posting.title,
                               time_slot.start_time, time_slot.end_time
                        from time_slot
                        join posting on time_slot.post_id = posting.post_id
                        where time_slot.customer_id = %s
                          and posting.account_id = %s
                        order by time_slot.start_time''',
                     [customer_id, business_id])
        return curs.fetchall()


def get_inquiries_with_business(conn, customer_id, business_id):
    """Return the inquiries this customer has sent about this
    business's postings newest first"""
    with dbi.dict_cursor(conn) as curs:
        curs.execute('''select posting.post_id, posting.title,
                               inquiry.message, inquiry.created_at
                        from inquiry
                        join posting on inquiry.post_id = posting.post_id
                        where inquiry.customer_id = %s
                          and posting.account_id = %s
                        order by inquiry.created_at desc''',
                     [customer_id, business_id])
        return curs.fetchall()