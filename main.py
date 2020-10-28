import json
import os.path
import logging
import argparse
import auth
import sys
try:
    from instagram_private_api import (
        Client, __version__ as client_version)
    from instagram_web_api import (
        Client, __version__ as web_client_version)
except ImportError:
    sys.path.append('./vevn/Lib/site-packages/')
    from instagram_private_api import (
        Client, __version__ as client_version)
    from instagram_web_api import (
        Client, __version__ as web_client_version)


def login(username, password):
    insta_api = auth.login_instagram(username, password)
    return insta_api


def dump_json(filename, data, permission='w'):
    with open(filename, permission) as outfile:
        json.dump(data, outfile, indent=2)
        outfile.write("\n")


def handle_comments(vendor, entries, caption):
    print('\r' + vendor + " Comment Entries: ...", end='')
    sys.stdout.flush()
    feed = web_api.user_feed(get_user_id(vendor))
    entry_count = 0

    for post in feed:
        if len(post["node"]["edge_media_to_caption"]["edges"]) <= 0:
            continue

        if caption in post["node"]["edge_media_to_caption"]["edges"][0]["node"]["text"].lower():
            comments = private_api.media_n_comments(post["node"]["id"],
                                                    post["node"]["edge_media_preview_comment"]["count"])
            dump_json(vendor + '_comments.json', comments)

            for comment in comments:
                # Type 2 comments are replies
                if comment["type"] is not 2 and '@' in comment["text"]:
                    usr = comment["user"]["username"]
                    if usr in entries:
                        if comment["text"] not in entries[usr]:
                            entries[usr].append(comment["text"])
                            entry_count += 1
                    else:
                        entries[usr] = [comment["text"]]
                        entry_count += 1

            print('\r' + vendor + " Comment Entries: " + str(entry_count))
            sys.stdout.flush()
            break


def get_user_id(user_name):
    info = web_api.user_info2(user_name)
    return info["id"]


def get_follower_count(user_name):
    info = web_api.user_info2(user_name)
    return info["edge_followed_by"]["count"]


def build_common_followers(vendors):
    print("Gathering list of followers...")
    common_followers = list()

    for vendor in vendors:
        uuid = private_api.generate_uuid()
        count = get_follower_count(vendor)
        followers = list()
        max_id = 0
        print('\r' + vendor + " Follower Count: 0/" + str(count), end='')
        sys.stdout.flush()

        while count > len(followers):
            tmp = private_api.user_followers(get_user_id(vendor), uuid, max_id=max_id)

            for user in tmp["users"]:
                followers.append(user["username"])

            max_id = tmp["next_max_id"]
            if len(followers) >= count:
                print('\r' + vendor + " Follower Count: " + str(count) + "/" + str(count))
                sys.stdout.flush()
            else:
                print('\r' + vendor + " Follower Count: " + str(len(followers)) + "/" + str(count), end='')
                sys.stdout.flush()

        if len(common_followers) is 0:
            common_followers = followers
            continue

        common_followers = list(set(followers) & set(common_followers))
    return common_followers


def handle_followers(entries):
    bad_list = set()
    for entry in entries:
        if entry not in common_followers_list:
            bad_list.add(entry)
    return bad_list


def finish_up(x):
    for y in x:
        x[y].append(len(x[y]))


if __name__ == '__main__':
    logging.basicConfig()
    logger = logging.getLogger('instagram_private_api')
    logger.setLevel(logging.WARNING)

    parser = argparse.ArgumentParser(description='Login Info')
    parser.add_argument('-u', '--username', dest='username', type=str, required=True)
    parser.add_argument('-p', '--password', dest='password', type=str, required=True)

    args = parser.parse_args()

    private_api = login(args.username, args.password)
    web_api = Client()
    vendors = ["thebabeswhostudy", "faithful.sweets", "femxquarters",
               "petitplatters", "designedby.lin", "designyourlifeplanner"]
    caption = "fall giveaway time!!"
    global common_followers_list
    common_followers_list = build_common_followers(vendors)
    bad_entries = set()
    dump_json('common_followers.json', list(common_followers_list))

    print("Gathering comment entries...")
    for vendor in vendors:
        entries = dict()
        handle_comments(vendor, entries, caption)
        finish_up(entries)
        dump_json(vendor + '_entries.json', entries)
        bad_entries |= handle_followers(entries)

    dump_json('bad_entries.json', list(bad_entries))
    print("All done!")
