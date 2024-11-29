from atproto import Client

username = '<username>'
password = '<password>'
client = Client()
client.login(username, password)

data = client.get_author_feed(
    actor='did:plc:imrmejwhh23tzkexk63dg7cq',
    filter='posts_and_author_threads',
    limit=100,
)

feed = data.feed
next_page = data.cursor


for feed_view_post in feed:
    post = feed_view_post.post
    is_repost = post.viewer.repost is not None

    if is_repost:
        continue

    print(f"{post.like_count} likes {post.repost_count} reposts {post.quote_count} quotes post:{post.record.text[:10]}")