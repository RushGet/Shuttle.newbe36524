import unittest

from tasks import *

test_config_file = "config/config_test.yaml"


def test_load_config():
    config = load_config(test_config_file)
    assert config is not None
    assert config.version == 0.1
    print(config)


def test_filter_by_tag_selectors():
    config = load_config(test_config_file)
    with open('test_data/dotnet_sdk_tags.json', "r", encoding='utf-8') as f:
        mcr_tags_json = json.load(f)
    result = select_mcr_tags(config.images[0], mcr_tags_json['tags'])
    assert result is not None
    with open('test_data/dotnet_sdk_match_data.json', "r", encoding='utf-8') as f:
        match_data = json.load(f)
    print(result[0])
    # check tags
    assert result[0].tags == match_data


def test_filter_by_tag_selectors_redis():
    config = load_config(test_config_file)
    with open('test_data/redis_dockerhub_tags.json', "r", encoding='utf-8') as f:
        mcr_tags_json = json.load(f)
    result = select_mcr_tags(config.images[1], mcr_tags_json['tags'])
    print(result)
    assert result is not None
    with open('test_data/redis_match_data.json', "r", encoding='utf-8') as f:
        match_data = json.load(f)
    print(result[0])
    # check tags
    assert result[0].tags == match_data


def test_match_include():
    tag = '3.1.201'
    regex_list = ['^3\\..*']
    regex_exclude_list = None
    assert match_tag_by_regex(tag, regex_list, regex_exclude_list)


def test_match_exclude():
    tag = '3.1.201-preview1'
    regex_list = ['^3\\..*']
    regex_exclude_list = ['.*preview.*']
    assert not match_tag_by_regex(tag, regex_list, regex_exclude_list)


def test_create_image_sync_data_json():
    items = [
        ImageTransportation('mcr.microsoft.com',
                            'dotnet/sdk',
                            'registry.cn-hangzhou.aliyuncs.com/newbe36524/dotnet-sdk',
                            ['3.1.201', '3.1.202'])]
    result = create_image_sync_data_json(items)
    assert result is not None
    assert len(result) == 1
    expected = {
        "mcr.microsoft.com/dotnet/sdk:3.1.201": "registry.cn-hangzhou.aliyuncs.com/newbe36524/dotnet-sdk:3.1.201",
        "mcr.microsoft.com/dotnet/sdk:3.1.202": "registry.cn-hangzhou.aliyuncs.com/newbe36524/dotnet-sdk:3.1.202"
    }
    assert result[0].items == expected
    assert result[0].name == 'dotnet_sdk-0'
    logging.info(result[0])


def test_create_image_sync_data_json_with_more_tags():
    items = [
        ImageTransportation('mcr.microsoft.com',
                            'dotnet/sdk',
                            'registry.cn-hangzhou.aliyuncs.com/newbe36524/dotnet-sdk',
                            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11'])]
    result = create_image_sync_data_json(items)
    assert result is not None
    assert len(result) == 2
    expected0 = {
        "mcr.microsoft.com/dotnet/sdk:1": "registry.cn-hangzhou.aliyuncs.com/newbe36524/dotnet-sdk:1",
        "mcr.microsoft.com/dotnet/sdk:2": "registry.cn-hangzhou.aliyuncs.com/newbe36524/dotnet-sdk:2",
        "mcr.microsoft.com/dotnet/sdk:3": "registry.cn-hangzhou.aliyuncs.com/newbe36524/dotnet-sdk:3",
        "mcr.microsoft.com/dotnet/sdk:4": "registry.cn-hangzhou.aliyuncs.com/newbe36524/dotnet-sdk:4",
        "mcr.microsoft.com/dotnet/sdk:5": "registry.cn-hangzhou.aliyuncs.com/newbe36524/dotnet-sdk:5",
        "mcr.microsoft.com/dotnet/sdk:6": "registry.cn-hangzhou.aliyuncs.com/newbe36524/dotnet-sdk:6",
        "mcr.microsoft.com/dotnet/sdk:7": "registry.cn-hangzhou.aliyuncs.com/newbe36524/dotnet-sdk:7",
        "mcr.microsoft.com/dotnet/sdk:8": "registry.cn-hangzhou.aliyuncs.com/newbe36524/dotnet-sdk:8",
        "mcr.microsoft.com/dotnet/sdk:9": "registry.cn-hangzhou.aliyuncs.com/newbe36524/dotnet-sdk:9",
        "mcr.microsoft.com/dotnet/sdk:10": "registry.cn-hangzhou.aliyuncs.com/newbe36524/dotnet-sdk:10"
    }
    assert result[0].items == expected0

    expected1 = {
        "mcr.microsoft.com/dotnet/sdk:11": "registry.cn-hangzhou.aliyuncs.com/newbe36524/dotnet-sdk:11"
    }
    assert result[1].items == expected1
