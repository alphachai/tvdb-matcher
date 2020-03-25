import json
import re
from collections import defaultdict
from pathlib import Path

import click
import requests

TVDB_URL = "https://api.thetvdb.com"


def check(resp):
    try:
        assert resp.status_code // 2 == 100
        return resp.json()
    except AssertionError:
        resp.raise_for_status()


def clean_name(n):
    n = re.sub(r"\W+", "", n.replace(" ", "_")).replace("_", " ").lower()
    while "  " in n:
        n = n.replace("  ", " ")
    return n


def find_matches(name, show):
    matches = []
    ep_split = name.split(" ")
    ep_split_count = len(ep_split)
    for season_id, season_data in show.items():
        for episode_id, episode_data in season_data.items():
            name = episode_data["episodeName"]
            _split = episode_data.get("_split", None)
            if not _split:
                _split = clean_name(name).split(" ")
                episode_data["_split"] = _split

            match_count = 0
            for s in ep_split + [
                f"S{season_id}",
                f"E{episode_id}",
                f"S{season_id}E{episode_id}",
            ]:
                if s in _split:
                    match_count += 1
            if match_count > 0:
                matches.append((season_id, episode_id, match_count / len(_split), name))

    return sorted(matches, key=lambda x: x[2], reverse=True)


@click.command()
@click.option("--dryrun", default=False, type=click.BOOL)
@click.option("--apikey")
@click.option("--user")
@click.option("--userkey")
@click.option("--showid")
@click.argument("path_param")
def main(dryrun, apikey, user, userkey, showid, path_param):
    payload = {"apikey": apikey, "username": user, "userkey": userkey}
    resp = check(requests.post(f"{TVDB_URL}/login", json=payload))
    token = resp.get("token")
    headers = {"Authorization": f"Bearer {token}"}

    show_path = Path(path_param)
    cache_path = Path("cache.json")

    show_data = {}
    episode_data = {}

    # Load show episodes from TVDB API, cache them forever in cache.json
    if cache_path.is_file():
        with open(str(cache_path.absolute()), "r") as f:
            _data = json.loads("".join([line for line in f]))
            episode_data = _data["episodes"]
            show_data = _data["shows"]
    else:
        url = f"{TVDB_URL}/series/{showid}"

        _episodes = []
        page = 0
        url = f"{TVDB_URL}/series/{showid}/episodes"
        resp = check(requests.get(url, params={"page": page}, headers=headers))
        _episodes.extend(resp["data"])
        for i in range(2, resp["links"]["last"] + 1):
            resp = check(requests.get(url, params={"page": i}, headers=headers))
            _episodes.extend(resp["data"])

        episode_data = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        for e in _episodes:
            season = e["airedSeason"]
            episode = e["airedEpisodeNumber"]
            name = e["episodeName"]
            episode_data[showid][season][episode] = e

        with open(str(cache_path.absolute()), "a") as f:
            f.write(json.dumps({"shows": show_data, "episodes": episode_data}) + "\n")

    # Discover episodes on disk at user-specified path.
    show_files = []
    for p in show_path.iterdir():
        if p.is_file():
            show_files.append(p)

    episodes = {}
    for sf in show_files:
        file_name_no_ext = ".".join(sf.name.split(".")[:-1])
        episode_name = clean_name(file_name_no_ext)
        if episode_name not in episodes:
            episodes[episode_name] = {
                "name": episode_name,
                "files": [],
            }
        episodes[episode_name]["files"].append(sf)

    # Match episodes on disk to episodes in TVDB
    for _, episode in episodes.items():
        episode["matches"] = find_matches(episode["name"], episode_data[showid])

    matches = []
    for _, episode in episodes.items():
        name = episode["name"]
        match = episode["matches"][0]
        pct = match[2] * 100

        best_matches = [match]
        for m in episode["matches"][1:]:
            if m[2] >= pct:
                best_matches.append(m)

        if len(best_matches) > 1:
            print(f'Found multiple matches for "{name}"...')
            for mi in range(len(best_matches)):
                print(f"({mi})\t{best_matches[mi]}")
            try:
                chosen_match = int(input("Select best match: "))
                assert chosen_match in range(len(best_matches))
            except Exception as e:
                print(f"Unacceptable match selected. {e}")
            match = episode["matches"][mi]

        matches.append((episode, match))

    # Write results to stdout/disk
    for episode, match in matches:
        name = episode["name"]
        season_id = match[0]
        episode_id = match[1]
        pct = match[2] * 100
        match_name = match[3]
        print(
            f'Matched {name} with S{season_id}E{episode_id} "{match_name}" with {pct:.0f}% certainty.'
        )

        new_name = f"S{season_id}E{episode_id} {match_name}"
        for p in episode["files"]:
            try:
                assert p.is_file()
            except:
                print(f"Skipping {p} because it's not a file.")
                continue
            new_p = p.parents[0] / f"{new_name}{p.suffix}"
            try:
                assert not new_p.is_file()
            except:
                print(f"Skipping {p} because {new_p} already exists.")
                continue
            if not dryrun:
                p.rename(new_p)
            else:
                print(f"Would rename {p} to {new_p}")


if __name__ == "__main__":
    main()
