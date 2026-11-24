"""Accounts, password hashing and login helpers"""

from passlib.context import CryptContext
import cs304dbi as dbi

pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    default="argon2",
    deprecated=["bcrypt"],

    bcrypt__rounds=12,
    bcrypt__ident="2b",
    bcrypt__truncate_error=True,

    argon2__memory_cost=65536,  # 64 MB
    argon2__time_cost=3,
    argon2__parallelism=4,
)


def hash_password(password):
    return pwd_context.hash(password)


def verify_password(password, stored_hash):
    """Returns (ok, new_hash_or_none). The caller should save new_hash
    if it isn't None."""
    try:
        ok = pwd_context.verify(password, stored_hash)
    except ValueError:
        # stored_hash isn't a real hash (e.g. hand-inserted test data)
        return False, None
    if not ok:
        return False, None
    if pwd_context.needs_update(stored_hash):
        return True, pwd_context.hash(password)
    return True, None


def create_account(conn, username, email, hashed, account_type,
                   business_name):
    """Insert into account, plus business or customers, and commit.
    Returns the new account_id. Raises pymysql.IntegrityError if the
    username is taken."""
    with dbi.dict_cursor(conn) as curs:
        curs.execute('''insert into account
                            (account_type, email, username, password_hash)
                        values (%s, %s, %s, %s)''',
                     [account_type, email, username, hashed])
        account_id = curs.lastrowid
        if account_type == 'business':
            curs.execute('''insert into business (account_id, business_name)
                            values (%s, %s)''',
                         [account_id, business_name])
        else:
            curs.execute('''insert into customers (account_id)
                            values (%s)''',
                         [account_id])
        conn.commit()
        return account_id


def get_login_info(conn, username):
    """Return account_id, account_type, password_hash for a username,
    or None."""
    with dbi.dict_cursor(conn) as curs:
        curs.execute('''select account_id, account_type, password_hash
                        from account
                        where username = %s''',
                     [username])
        return curs.fetchone()


def get_account(conn, account_id):
    """Return account_id, username, account_type for an id, or None."""
    with dbi.dict_cursor(conn) as curs:
        curs.execute('''select account_id, username, account_type
                        from account
                        where account_id = %s''',
                     [account_id])
        return curs.fetchone()


def update_hash(conn, account_id, new_hash):
    """Replace an outdated password hash."""
    with dbi.dict_cursor(conn) as curs:
        curs.execute('''update account set password_hash = %s
                        where account_id = %s''',
                     [new_hash, account_id])
        conn.commit()