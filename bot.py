import argparse
import json
import pickle
import re
import time
from pathlib import Path

import requests
import toml
import tweepy
from tweepy import API, User, Tweet

import uwu


# todo: upgrade owoifier with easter eggs and whatever
# todo: webhooks for getting new tweets from source, better than periodically checking
# todo: refactor object oriented with API subclass


__version__ = '0.3.0'


CONFIG_PATH = 'config.toml'
DATA_PATH = 'tweets.json'
HISTORY_CACHE_DIR = Path('history/')
INTERVAL_SECONDS = 60


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('-t', '--test-get-status', action='store_true', help='Debugging')
    parser.add_argument('-hi', '--history', action='store_true', help='Do all the past tweets of the source account')
    parser.add_argument('-r', '--run', action='store_true', default=True, help='Run the bot. The default')

    return parser


# for this_done_id
# noinspection PyUnboundLocalVariable
def try_process_tweet(tweet: tweepy.Tweet, url_regex: re.Pattern, api: tweepy.API):
    # get list of tweets done before, check if this one is done before
    # todo: speed up by keeping file open for history
    try:
        with open(DATA_PATH) as data_file:
            done_tweets = json.load(data_file)
    except FileNotFoundError:
        done_tweets = []
        done_ids = []
        result_ids = []
    else:
        done_ids, result_ids = zip(*done_tweets)
    if tweet.id in done_ids:
        print(f'Tweet {tweet.id} already done, as {result_ids[done_ids.index(tweet.id)]}')
        return 1

    # check if tweet is desired format
    if not tweet.entities['urls']:
        print(f'Tweet {tweet.id} does not have any links')
        return
    embed_url: str = tweet.entities['urls'][0]['url']
    try:
        # todo: speed up by caching redirect urls
        embed_url_real = requests.get(embed_url).url
    except requests.ConnectionError:
        print(f'Tweet {tweet.id} had a broken link')
        return
    if not re.match(url_regex, embed_url_real):
        print(f'Tweet {tweet.id} had a link that did not match the regex')
        return

    # owoify, but do not edit the link
    tweet_content: str = tweet.text
    tweet_content = tweet_content.replace(embed_url, '{uww}')  # universal wesource wocator
    tweet_content = uwu.owoify(tweet_content)
    tweet_content = tweet_content.format(uww=embed_url)

    # send tweet
    try:
        status_update = api.update_status(tweet_content)
    except tweepy.BadRequest:
        # todo: make owoifier ignore links better
        print(f'Tweet {tweet.id} has broken owoified urls, skipping')
        # 0 if tweet skipped
        this_done_id = 0
    else:
        this_done_id = status_update.id
    finally:
        print(f'Parodied tweet {tweet.id} as {this_done_id}')
        done_tweets.append((tweet.id, this_done_id))
        with open(DATA_PATH, 'w') as data_file:
            json.dump(done_tweets, data_file)


def get_full_tweet_history_cached(
        api: API, screen_name: str, cache_dir: Path = HISTORY_CACHE_DIR
) -> list[Tweet]:
    # check if tweet history is cached as a pickle file
    user: User = api.get_user(screen_name=screen_name)
    cache_dir.mkdir(exist_ok=True)
    history_cache_path = cache_dir / f'{user.id}.pickle'
    try:
        with open(history_cache_path, 'rb') as history_cache_file:
            tweet_history = pickle.load(history_cache_file)
    except FileNotFoundError:
        pass
    else:
        print('Loaded tweet history from cache')
        return tweet_history

    # create paginator for tweet history
    tweet_history_cursor = tweepy.Cursor(api.user_timeline, screen_name=screen_name, count=200).items()
    # get entire tweet history, reverse it
    print('Getting tweet history, this may take some time')
    tweet_history = list(tweet_history_cursor)
    print(f'Got {len(tweet_history)} tweets')
    tweet_history.reverse()

    # save history to cache
    with open(history_cache_path, 'wb') as history_cache_file:
        pickle.dump(tweet_history, history_cache_file)
    print('Saved tweet history to cache')

    return tweet_history


def history(source: str, url_regex: re.Pattern, api: tweepy.API):
    tweet_history = get_full_tweet_history_cached(api, source)

    # do every past tweet
    for tweet in tweet_history:
        try_process_tweet(tweet, url_regex, api)


def run(source: str, url_regex: re.Pattern, api: tweepy.API, interval: float = INTERVAL_SECONDS):
    print('Running bot')
    while True:
        print(f'Sleeping for {interval} seconds')
        time.sleep(interval)

        tweet_history_cursor = tweepy.Cursor(api.user_timeline, screen_name=source).items()
        for tweet in tweet_history_cursor:
            result = try_process_tweet(tweet, url_regex, api)
            # returned when reached a tweet that's done already
            if result == 1:
                break


def test_get_status(api: tweepy.API, status_id: int = 1441796147778138113):
    bbb = api.get_status(status_id)
    print(bbb)


def main():
    with open(CONFIG_PATH) as config_file:
        config = toml.load(config_file)

    url_regex = re.compile(config['settings']['url_regex'])

    auth = tweepy.OAuthHandler(config['auth']['consumer_key'], config['auth']['consumer_secret'])
    auth.set_access_token(config['auth']['access_token'], config['auth']['access_token_secret'])
    api = tweepy.API(auth)

    parser = get_parser()
    args = parser.parse_args()
    if args.test_get_status:
        test_get_status(api)
    elif args.history:
        history(config['settings']['source'], url_regex, api)
    else:
        run(config['settings']['source'], url_regex, api)


if __name__ == '__main__':
    main()
