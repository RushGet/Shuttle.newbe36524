import json
import logging
import os
import re
import shutil
import sys

import requests
import yaml
from invoke import task

from models import *

logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.INFO)
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)


def get_all_tags(registry: DockerRegistry, image: str):
    if registry == DockerRegistry.MCR:
        url = f"https://mcr.microsoft.com/v2/{image}/tags/list"
        r = requests.get(url)
        if r.status_code == 200:
            return r.json()['tags']
    elif registry == DockerRegistry.DOCKERHUB:
        # get token
        r = requests.get(f"https://auth.docker.io/token?service=registry.docker.io&scope=repository:{image}:pull")
        token = r.json()['token']
        # get tags
        url = f"https://index.docker.io/v2/{image}/tags/list"
        r = requests.get(url, headers={"Authorization": f"Bearer {token}"})
        if r.status_code == 200:
            return r.json()['tags']
    else:
        url = f"https://{registry.value}/v2/{image}/tags/list"
        r = requests.get(url)
        if r.status_code == 200:
            return r.json()['tags']


def load_config(file: str = "config/config.yaml") -> ShuttleConfig:
    # Load config from file
    with open(file, "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return ShuttleConfig.from_yaml(config)


def select_mcr_tags(image_selector_config: ShuttleImageConfig, tags: list[str]) -> list[McrTagsMatchingResult]:
    image_name = image_selector_config.name
    results = []
    selected_tags = []
    for tag in tags:
        if match_tag_by_regex(tag, image_selector_config.tag_regex,
                              image_selector_config.tag_regex_exclude):
            selected_tags.append(tag)
    results.append(McrTagsMatchingResult(image_name, image_selector_config, selected_tags))
    return results


def match_tag_by_regex(tag: str, regex_list: list, regex_exclude_list: list = None) -> bool:
    # test tag by regex_list and regex_exclude_list
    # if regex_list is not defined, all tags are selected
    # if regex_exclude_list is defined, tags matching regex_exclude_list are excluded
    for regex in regex_list:
        if re.match(regex, tag):
            if regex_exclude_list is not None:
                for regex_exclude in regex_exclude_list:
                    if re.match(regex_exclude, tag):
                        break
                else:
                    return True
            else:
                return True
    return False


def create_image_sync_data_json(items: list[ImageTransportation]) -> list[ImageSyncData]:
    # create json for image-syncer
    limit_tags_count = 10
    data = []
    for item in items:
        # spilt tags into chunks, each chunk has limit_tags_count tags
        tag_chunks = [item.tags[i:i + limit_tags_count] for i in range(0, len(item.tags), limit_tags_count)]
        for i in range(len(tag_chunks)):
            tag_chunk = tag_chunks[i]
            content = {}
            for tag in tag_chunk:
                # create json for each chunk
                source = f"{item.source_registry}/{item.source_image}:{tag}"
                target = f"{item.target}:{tag}"
                content[source] = target
            # write json to file
            data.append(ImageSyncData(f"{item.source_image.replace('/', '_')}-{i}", content))
    return data


@task
def create_data(c):
    # force reset data dir
    if os.path.exists("data"):
        shutil.rmtree("data")
        logging.debug("data dir removed")
    os.mkdir("data")
    logging.debug("data dir created")

    config = load_config()
    if len(config.images) == 0:
        logging.info("No image config found")
        c.run(f'echo "image_sync_files=[]" >> $GITHUB_OUTPUT');
        return

    image_sync_files = []
    for image_config in config.images:
        logging.info(f"Processing {image_config.image}")
        tags = get_all_tags(image_config.docker_registry, image_config.image)
        match_results = select_mcr_tags(image_config, tags)
        # map match_results to ImageTransportation
        items = []
        for match_result in match_results:
            items.append(
                ImageTransportation(image_config.docker_registry.value,
                                    image_config.image,
                                    image_config.target,
                                    match_result.tags))

        # create json for image
        data = create_image_sync_data_json(items)

        # write json to file
        for item in data:
            logging.info(f"Writing {item.name}.json")
            with open(f"data/{item.name}.json", "w") as f:
                json.dump(item.items, f, indent=4)
            image_sync_files.append(f"data/{item.name}.json")

    if len(image_sync_files) == 0:
        logging.info("No images to sync")
        c.run(f'echo "image_sync_files=[]" >> $GITHUB_OUTPUT');
        return

    # dump json, string should be like "['data/xxx.json', 'data/yyy.json']"
    json_content = json.dumps(image_sync_files).replace("\"", "'")
    logging.info(f"image_sync_files={json_content}")
    # print output to GitHub action
    c.run(f'echo "image_sync_files={json_content}" >> $GITHUB_OUTPUT');


@task
def sync(c, image_sync_file: str = ""):
    # sync images
    logging.info("Syncing images")
    os.chmod("image-syncer", 0o755)
    if image_sync_file != "":
        logging.info(f"Syncing {image_sync_file}")
        c.run(f"./image-syncer --auth=./auth.json --images={image_sync_file}")
    else:
        for file in os.listdir("data"):
            if file.endswith(".json"):
                c.run(f"./image-syncer --auth=./auth.json --images=./data/{file}")
