import asyncio
import csv
from datetime import datetime as dt
from feedgen.feed import FeedGenerator
from tiktokapipy.async_api import AsyncTikTokAPI
from math import ceil

# Now using a new TikTok library https://github.com/Russell-Newton/TikTokPy

# Normal GitHub Pages URL
ghPagesURL = "https://kickerofelves.github.io/tiktok-rss-flat/"

# Custom Domain
# ghPagesURL = "https://tiktokrss.conoroneill.com/"

def log(message):
    print(f"-------------------- { message } --------------------")


def logError(exception):
    log("!!!!! ERROR !!!!!")
    log(exception)

maxItems = 5
now = dt.now()
print(f"github time:{now}")
log(f"Github time: {now}")
hour = now.hour
hour -= 12 if hour >= 13 else hour
num_lines = sum(1 for _ in open('subscriptions.csv'))
log(f"Number of subscriptions: {num_lines}")
block_size = ceil(num_lines/12)
start_range = hour*block_size
end_range = start_range+block_size

async def runAll():
    try:
        log("runAll start")
        log("attempt to load subscription file number to run")
        with open('subscriptions.csv') as f:
            reader = csv.reader(f)
            name_list = list(reader)
            log(f"Type of username: {type(name_list[0][0])}")
            # TODO: Switch to 3.11 TaskGroup or trio nursery
            await asyncio.gather(*[
                # run(row['username']) for row in csv.DictReader(f, fieldnames=['username'])])
                run(row[0] for row in name_list[start_range:end_range])])
    except Exception as e:
        logError(e)


async def run(tiktokUsername):
    log(f"run start ( { tiktokUsername } )")
    try:
        feedGenerator = FeedGenerator()
        feedGenerator.id("https://www.tiktok.com/@" + tiktokUsername)
        feedGenerator.title("@" + tiktokUsername + " | TikTok")
        feedGenerator.author(
            {"name": "Conor ONeill", "email": "conor@conoroneill.com"})
        feedGenerator.link(href="https://www.tiktok.com/@" +
                           tiktokUsername, rel="alternate")
        feedGenerator.logo(ghPagesURL + "tiktok-rss.png")
        feedGenerator.subtitle("Latest TikToks from @" + tiktokUsername)
        feedGenerator.link(href=ghPagesURL + "rss/" +
                           tiktokUsername + ".xml", rel="self")
        feedGenerator.language("en")

        # Set the last modification time for the feed to be the most recent post, else now.
        updated = None

        async with AsyncTikTokAPI(navigation_retries=3, navigation_timeout=60) as api:
            tiktokUser = await api.user(tiktokUsername, video_limit=maxItems)
            async for video in tiktokUser.videos:
                log(f"processing video from @{ tiktokUsername }")
                try:
                    videoLink = f"https://www.tiktok.com/@{ tiktokUsername }/video/{ str( video.id ) }"
                    feedEntry = feedGenerator.add_entry()
                    feedEntry.id(videoLink)

                    timestamp = video.create_time
                    # print( timestamp )
                    feedEntry.published(timestamp)
                    feedEntry.updated(timestamp)
                    updated = max(timestamp, updated) if updated else timestamp

                    if video.desc:
                        feedEntry.title(video.desc[0:255])
                    else:
                        feedEntry.title("[no title]")

                    feedEntry.link(href=videoLink)

                    # feedEntry.description( "<img src = "" + tiktok.as_dict["video"]["cover"] + "" />" )
                    if video.desc:
                        feedEntry.description(video.desc)
                    else:
                        feedEntry.description("[no description]")

                    log(
                        f"successfully processed video from @{ tiktokUsername }")

                except Exception as e:
                    log(
                        f"error occurred while processing video from @{ tiktokUsername }")
                    logError(e)
                    continue

        feedGenerator.updated(updated)

        feedFileName = "rss/" + tiktokUsername + ".xml"
        log(f"attempt to write feed to file { feedFileName }")
        # Write the RSS feed to a file
        feedGenerator.atom_file(feedFileName, pretty=True)

    except Exception as e:
        log("error occurred outside of processing videos")
        logError(e)
        pass

    log(f"run end ( { tiktokUsername } )")


asyncio.run(runAll())
