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

maxItems = 5
now = dt.now()
hour = now.hour
hour -= 12 if hour >= 13 else hour
num_lines = sum(1 for _ in open('subscriptions.csv'))
block_size = ceil(num_lines/12)
start_range = hour*block_size
end_range = start_range+block_size


async def runAll():
    with open('subscriptions.csv') as f:
        reader = csv.reader(f)
        name_list = list(reader)

        # TODO: Switch to 3.11 TaskGroup or trio nursery
        await asyncio.gather(*[
            # run(row['username']) for row in csv.DictReader(f, fieldnames=['username'])])
            run(row[0] for row in name_list[start_range:end_range])])


async def run(csvuser):
    try:
        print(f'Running for user \'{csvuser}\'')

        fg = FeedGenerator()
        fg.id('https://tiktok.com/@' + csvuser)
        fg.title(csvuser + ' TikTok')
        fg.author({'name': 'Conor ONeill', 'email': 'conor@conoroneill.com'})
        fg.link(href='http://tiktok.com', rel='alternate')
        fg.logo(ghPagesURL + 'tiktok-rss.png')
        fg.subtitle('OK Boomer, all the latest TikToks from ' + csvuser)
        fg.link(href=ghPagesURL + 'rss/' + csvuser + '.xml', rel='self')
        fg.language('en')

        # Set the last modification time for the feed to be the most recent post, else now.
        updated = None

        async with AsyncTikTokAPI(navigation_retries=3, navigation_timeout=60) as api:
            tiktokuser = await api.user(csvuser, video_limit=maxItems)
            async for video in tiktokuser.videos:
                # print(video.create_time, video.desc)
                print("URL = " + "https://tiktok.com/@" +
                      csvuser + "/video/" + str(video.id))
                fe = fg.add_entry()
                link = "https://tiktok.com/@" + \
                    csvuser + "/video/" + str(video.id)
                fe.id(link)
                ts = video.create_time
                print(ts)
                fe.published(ts)
                fe.updated(ts)
                updated = max(ts, updated) if updated else ts
                if video.desc:
                    fe.title(video.desc[0:255])
                else:
                    fe.title("No Title")
                fe.link(href=link)
                # fe.description("<img src='" + tiktok.as_dict['video']['cover'] + "' />")
                if video.desc:
                    fe.description(video.desc)
                else:
                    fe.description("No Description")
                # print(fg.rss_str(pretty=True))

        fg.updated(updated)
        # Write the RSS feed to a file
        fg.atom_file('rss/' + csvuser + '.xml', pretty=True)
    except Exception as e:
        print(f"Some error: {e}")
        pass


asyncio.run(runAll())
