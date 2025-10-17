import psycopg2
from datetime import datetime

# Connect to the database
conn = psycopg2.connect(
    'postgresql://tradequest_admin:TradeQuestDB2024!@tradequest-prod-postgres.cwlcwgqqib98.us-east-1.rds.amazonaws.com:5432/tradequest_db'
)

cur = conn.cursor()

# Get user counts
cur.execute("""
    SELECT 
        COUNT(*) as total_users,
        COUNT(CASE WHEN email_verified = true THEN 1 END) as verified_users,
        COUNT(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 END) as last_24h,
        COUNT(CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 END) as last_7days
    FROM users;
""")

result = cur.fetchone()
print("\n" + "="*60)
print("USER STATISTICS")
print("="*60)
print(f"Total Users:           {result[0]}")
print(f"Verified Users:        {result[1]}")
print(f"Signups (Last 24h):    {result[2]}")
print(f"Signups (Last 7 days): {result[3]}")
print("="*60)

# Get subscription breakdown
cur.execute("""
    SELECT 
        plan,
        status,
        COUNT(*) as count
    FROM subscriptions
    GROUP BY plan, status
    ORDER BY plan, status;
""")

print("\nSUBSCRIPTION BREAKDOWN")
print("="*60)
subs = cur.fetchall()
if subs:
    for row in subs:
        print(f"{row[0]:20} | {row[1]:10} | {row[2]} users")
else:
    print("No subscriptions yet")
print("="*60)

# Get recent signups
cur.execute("""
    SELECT 
        email,
        created_at,
        email_verified
    FROM users
    ORDER BY created_at DESC
    LIMIT 10;
""")

print("\nMOST RECENT SIGNUPS (Last 10)")
print("="*60)
recent = cur.fetchall()
for row in recent:
    verified = "✓" if row[2] else "✗"
    print(f"{verified} | {row[0]:40} | {row[1].strftime('%Y-%m-%d %H:%M:%S')}")
print("="*60 + "\n")

cur.close()
conn.close()


