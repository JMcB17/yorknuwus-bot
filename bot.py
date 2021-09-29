import re

import toml
import tweepy

import uwu

CONFIG_PATH = 'config.toml'


def try_process(tweet: tweepy.Tweet, url_regex: re.Pattern, api: tweepy.API):
    # check if tweet is appropriate format
    if tweet.entities.links and re.match(url_regex, tweet.entities.links[0]):
        # do not edit the link
        embed_url = tweet.entities.urls[0]['url']
        tweet_content = tweet.text
        tweet_content = tweet_content.replace(embed_url, '{urw}')  # universal resource wocator owo
        tweet_content = uwu.owoify(tweet_content)
        tweet_content = tweet_content.format(urw=embed_url)

        api.update_status(tweet_content)


def history(source: str, url_regex: re.Pattern, api: tweepy.API):
    # todo: paginate?
    # todo: save ones already done
    # todo: parameter for how far back
    tweet_history = api.user_timeline(screen_name=source, count=200)
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
