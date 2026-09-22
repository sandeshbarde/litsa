import sqlite3

def check():
    conn = sqlite3.connect('dubai_leads.db')
    c = conn.cursor()
    c.execute('SELECT website_status, COUNT(*) FROM businesses GROUP BY website_status')
    rows = c.fetchall()
    print("Website Status Breakdown:")
    for status, count in rows:
        print(f"  {status}: {count}")

    c.execute("SELECT COUNT(*) FROM businesses WHERE website_status = 'WEBSITE_WORKING' OR (website IS NOT NULL AND website != '' AND website_status NOT IN ('NO_WEBSITE', 'WEBSITE_DOWN', 'UNREACHABLE'))")
    with_website = c.fetchone()[0]
    print(f"Total with working website: {with_website}")
    conn.close()

if __name__ == '__main__':
    check()
