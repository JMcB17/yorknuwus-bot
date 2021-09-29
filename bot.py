import json
import re

import requests
import toml
import tweepy

import uwu


# todo: upgrade owoifier


__version__ = '0.1.0'


CONFIG_PATH = 'config.toml'
DATA_PATH = 'tweets.json'


def try_process(tweet: tweepy.Tweet, url_regex: re.Pattern, api: tweepy.API):
    try:
        with open(DATA_PATH) as data_file:
            done_tweets = json.load(data_file)
    except FileNotFoundError:
        done_tweets = []
        done_ids = []
        result_ids = []
    else:
        done_ids, result_ids = zip(*done_tweets)
    # check if tweet is appropriate format, and not done before
    if not tweet.entities['urls']:
        print(f'Tweet {tweet.id} does not have any links')
        return
    if tweet.id in done_ids:
        print(f'Tweet {tweet.id} already done, as {result_ids[done_ids.index(tweet.id)]}')
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

    status_update = api.update_status(tweet_content)
    if status_update:
        done_tweets.append((tweet.id, status_update.json()['id']))
        with open(DATA_PATH, 'w') as data_file:
            json.dump(done_tweets, data_file)
    input()

    return status_update


def history(source: str, url_regex: re.Pattern, api: tweepy.API):
    # todo: paginate?
    # todo: parameter for how far back
    tweet_history: list[tweepy.Tweet] = api.user_timeline(screen_name=source, count=200)
    tweet_history.reverse()
    for tweet in tweet_history:
        try_process(tweet, url_regex, api)


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
    # todo: argparse option for this
    history(config['settings']['source'], url_regex, api)


if __name__ == '__main__':
    main()
