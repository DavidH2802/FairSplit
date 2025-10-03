CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sqlite_sequence(name,seq);
CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS memberships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    group_creator INTEGER CHECK(group_creator IN(0, 1)),
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(group_id) REFERENCES groups(id)
);
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    payer_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    description TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(group_id) REFERENCES groups(id),
    FOREIGN KEY(payer_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS invites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER NOT NULL,
        receiver_id INTEGER NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT CHECK(status IN ('active', 'inactive')), 
        group_id INTEGER NOT NULL, 
        group_name TEXT NOT NULL,
        FOREIGN KEY (sender_id) REFERENCES users(id),
        FOREIGN KEY (receiver_id) REFERENCES users(id),
        FOREIGN KEY (group_id) REFERENCES groups(id)
);
CREATE TABLE IF NOT EXISTS loans(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        payer_id INTEGER NOT NULL,
        payee_id INTEGER NOT NULL,
        transaction_id INTEGER NOT NULL,
        amount REAL NOT NULL, 
        group_id INTEGER NOT NULL,
        FOREIGN KEY (payer_id) REFERENCES users(id),
        FOREIGN KEY (payee_id) REFERENCES users(id),
        FOREIGN KEY (transaction_id) REFERENCES transactions(id),
        FOREIGN KEY (group_id) REFERENCES groups(id)
);