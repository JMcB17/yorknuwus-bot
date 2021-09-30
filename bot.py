import argparse
import json
import re
import time

import requests
import toml
import tweepy

import uwu


# todo: upgrade owoifier


__version__ = '0.1.0'


CONFIG_PATH = 'config.toml'
DATA_PATH = 'tweets.json'
INTERVAL_SECONDS = 60


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('-t', '--test-get-status', action='store_true', help='Debugging')
    parser.add_argument('-hi', '--history', action='store_true', help='Do all the past tweets of the source account')
    parser.add_argument('-r', '--run', action='store_true', default=True, help='Run the bot. The default')

    return parser


def try_process_tweet(tweet: tweepy.Tweet, url_regex: re.Pattern, api: tweepy.API):
    # get list of tweets done before, check if this one is done before
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
    embed_url_real = requests.get(embed_url).url
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
        print(f'Tweet {tweet.id} has broken urls')
    else:
        print(f'Parodied tweet {tweet.id} as {status_update.id}')
        if status_update:
            done_tweets.append((tweet.id, status_update.id))
            with open(DATA_PATH, 'w') as data_file:
                json.dump(done_tweets, data_file)

        return status_update


def history(source: str, url_regex: re.Pattern, api: tweepy.API):
    # create paginator for tweet history
    tweet_history_cursor = tweepy.Cursor(api.user_timeline, screen_name=source, count=200).items()
    # get entire tweet history, reverse it
    print('Getting tweet history, this may take some time')
    tweet_history = list(tweet_history_cursor)
    print(f'Got {len(tweet_history)} tweets')
    tweet_history.reverse()

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
