import re

import toml
import tweepy


CONFIG_PATH = 'config.toml'


def main():
    with open(CONFIG_PATH) as config_file:
        config = toml.load(config_file)

    url_regex = re.compile(config['url_regex'])

    auth = tweepy.OAuthHandler(config['consumer_key'], config['consumer_secret'])
    auth.set_access_token(config['access_token'], config['access_token_secret'])
    api = tweepy.API(auth)


if __name__ == '__main__':
    main()
