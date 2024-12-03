from enum import Enum

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from atproto import Client
from atproto_client.models.app.bsky.feed.get_actor_feeds import Response
from aiocache import Cache, cached
from aiocache.serializers import PickleSerializer

import dateutil.parser

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


class Sort(str, Enum):
    time = "time"
    likes = "likes"
    replies = "replies"
    reposts = "reposts"
    quotes = "quotes"
    characters = "characters"


@app.post("/stats", response_class=HTMLResponse)
async def get_stats(request: Request, username: str = Form(), password: str = Form(),
                    sort: Sort = Form()):
    data: Response = await get_bluesky_users_posts(username, password)

    password = None

    feed = data.feed
    posts_data = []

    for feed_view_post in feed:
        post = feed_view_post.post
        is_repost = post.viewer.repost is not None

        if is_repost:
            continue

        post_info = {
            "likes": post.like_count,
            "replies": post.reply_count,
            "reposts": post.repost_count,
            "quotes": post.quote_count,
            "text": post.record.text,
            "characters": len(post.record.text),
            "time": format_datetime(post.record.created_at),
            "images": extract_image_urls(post)
        }

        posts_data.append(post_info)

    posts_data.sort(key=lambda x: x[sort], reverse=True)

    return templates.TemplateResponse("post-list.html", {"request": request, "posts": posts_data})


@cached(
    ttl=30, cache=Cache.MEMORY, key="bluesky_posts", serializer=PickleSerializer())
async def get_bluesky_users_posts(username: str, password: str) -> Response:
    client = Client()
    client_response = client.login(username, password)

    data = client.get_author_feed(
        actor=client_response.did,
        filter='posts_and_author_threads',
        limit=100,
    )

    return data


def format_datetime(date_string: str):
    datetime_object = dateutil.parser.parse(date_string)
    formatted_datetime = datetime_object.strftime("%B %d, %Y at %I:%M %p")

    return formatted_datetime


def extract_image_urls(post):
    try:
        return [image.thumb for image in post.embed.images]
    except AttributeError:
        return []
