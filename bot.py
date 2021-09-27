import re

import toml
import tweepy

import uwu

CONFIG_PATH = 'config.toml'


def try_process(tweet: tweepy.Tweet, url_regex: re.Pattern, api: tweepy.API):
    if tweet.entities.links and re.match(url_regex, tweet.entities.links[0]):
        api.update_status(
            uwu.owoify(tweet.text),
            attachment_url=tweet.entities.links[0]
        )


def history(source: str, url_regex: re.Pattern, api: tweepy.API):
    # todo: paginate?
    tweet_history = api.user_timeline(screen_name=source, count=200)
    for tweet in tweet_history:
        try_process(tweet, url_regex, api)


def main():
    with open(CONFIG_PATH) as config_file:
        config = toml.load(config_file)

    url_regex = re.compile(config['settings']['url_regex'])

    auth = tweepy.OAuthHandler(config['auth']['consumer_key'], config['auth']['consumer_secret'])
    auth.set_access_token(config['auth']['access_token'], config['auth']['access_token_secret'])
    api = tweepy.API(auth)
    # todo: remove test line
    bbb = api.get_status(1441796147778138113)
    print(bbb)
    # todo: argparse option for this
    history(config['settings']['source'], url_regex, api)


if __name__ == '__main__':
    main()
