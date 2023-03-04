from enum import Enum


class DockerRegistry(Enum):
    MCR = "mcr.microsoft.com"
    DOCKERHUB = "docker.io"


class ShuttleImageConfig:
    name: str
    docker_registry: DockerRegistry
    image: str
    target: str
    tag_regex: list[str]
    tag_regex_exclude: list[str]

    def __init__(self, name: str, docker_registry: str, image: str, target: str, tag_regex: [str],
                 tag_regex_exclude: [str]):
        self.name = name
        self.docker_registry = DockerRegistry(docker_registry)
        self.image = image
        self.target = target
        self.tag_regex = tag_regex
        self.tag_regex_exclude = tag_regex_exclude

    def __str__(self):
        return f"name: {self.name}, docker_registry: {self.docker_registry}, image: {self.image}, " \
               f"target: {self.target}, tag_regex: {self.tag_regex}, " \
               f"tag_regex_exclude: {self.tag_regex_exclude}"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class ShuttleConfig:
    version: float
    images: list[ShuttleImageConfig]

    def __init__(self, version: float, images: [ShuttleImageConfig]):
        self.version = version
        self.images = images

    def __str__(self):
        return f"version: {self.version}, images: {self.images}"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    # static from yaml
    @staticmethod
    def from_yaml(yaml):
        images = []
        if yaml['images'] is not None:
            for image in yaml['images']:
                images.append(
                    ShuttleImageConfig(image['name'], image['docker_registry'], image['image'], image['target'],
                                       image['tag_regex'], image.get('tag_regex_exclude', None)))
        return ShuttleConfig(yaml['version'], images)


class ImageTransportation:
    tags: list[str]
    target: str
    source_registry: str
    source_image: str

    def __init__(self, source_registry: str, source_image: str, target: str, tags: [str]):
        self.tags = tags
        self.target = target
        self.source_registry = source_registry
        self.source_image = source_image

    def __str__(self):
        return f"{self.source_registry}/{self.source_image}: {self.tags} -> {self.target}"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class McrTagsMatchingResult:
    image: str
    match_config: ShuttleImageConfig
    tags: list[str]

    def __init__(self, image: str, match_config: ShuttleImageConfig, tags: list[str]):
        self.image = image
        self.match_config = match_config
        self.tags = tags

    def __str__(self):
        return f"{self.image}: {self.tags} -> {self.match_config.target}"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class ImageSyncData:
    items: dict[str, str]
    name: str

    def __init__(self, name: str, items: dict[str, str]):
        self.name = name
        self.items = items

    def __str__(self):
        return f"{self.name}: {self.items}"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.__dict__ == other.__dict__
