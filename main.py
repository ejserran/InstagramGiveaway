import json
import os.path
import logging
import argparse
import auth
try:
    from instagram_private_api import (
        Client, __version__ as client_version)
except ImportError:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from instagram_private_api import (
        Client, __version__ as client_version)


def login(username, password):
    insta_api = auth.login_instagram(username, password)
    return insta_api


def dump_json(filename, data):
    with open(filename, 'w') as outfile:
        json.dump(data, outfile, indent=2)


def handle_comments(vendor, entries, caption):
    feed = private_api.username_feed(vendor)

    for post in feed["items"]:
        if post["caption"] is None:
            continue

        if caption in post["caption"]["text"].lower():
            comments = private_api.media_n_comments(post["id"], post["comment_count"])
            dump_json(vendor + '_comments.json', comments)

            for comment in comments:
                # Type 2 comments are replies
                if comment["type"] is not 2 and '@' in comment["text"]:
                    usr = comment["user"]["username"]
                    if usr in entries:
                        if comment["text"] not in entries[usr]:
                            entries[usr].append(comment["text"])
                    else:
                        tmp = [comment["text"]]
                        entries[usr] = tmp
            break


def get_user_id(user_name):
    info = private_api.username_info(user_name)
    return info["user"]["profile_pic_id"].split('_')[1]


def get_follower_count(user_name):
    info = private_api.username_info(user_name)
    return info["user"]["follower_count"]


def build_common_followers(vendors):
    common_followers = {}
    uuid = private_api.generate_uuid()

    for vendor in vendors:
        count = get_follower_count(vendor)
        print(vendor + " Count: " + str(count))
        followers = {}
        tmp_followers = {}
        max_id = 0
        while count > len(followers):
            tmp = private_api.user_followers(get_user_id(vendor), uuid, max_id=max_id)

            for user in tmp["users"]:
                followers.append(user["username"])

            max_id = tmp["next_max_id"]
            print(len(followers))

        if len(common_followers) is 0:
            common_followers = followers
            continue

        if len(followers) < len(common_followers):
            list1 = followers
            list2 = common_followers
        else:
            list1 = common_followers
            list2 = followers

        for follower in list1:
            if follower in list2:
                tmp_followers.append(follower)

        common_followers = tmp_followers
    return common_followers


def handle_followers(entries):
    bad_list = {}
    for entry in entries:
        if entry not in common_followers_list:
            bad_list.append(entry)
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
    vendors = ["thebabeswhostudy", "faithful.sweets", "femxquarters",
               "petitplatters", "designedby.lin", "designyourlifeplanner"]
    caption = "fall giveaway time!!"
    global common_followers_list
    common_followers_list = build_common_followers(vendors)
    bad_entries = {}
    dump_json('common_followers.json', common_followers_list)

    for vendor in vendors:
        entries = {}
        print(vendor)
        handle_comments(vendor, entries, caption)
        finish_up(entries)
        dump_json(vendor + '_entries.json', entries)
        bad_entries += handle_followers(entries)

    dump_json('bad_entries.json', bad_entries)