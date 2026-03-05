# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
import sys

from typing import List

from alibabacloud_dingtalk.exclusive_1_0.client import Client as dingtalkexclusive_1_0Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dingtalk.exclusive_1_0 import models as dingtalkexclusive__1__0_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient


class Sample:
    def __init__(self):
        pass

    @staticmethod
    def create_client() -> dingtalkexclusive_1_0Client:
        """
        使用 Token 初始化账号Client
        @return: Client
        @throws Exception
        """
        config = open_api_models.Config()
        config.protocol = 'https'
        config.region_id = 'central'
        return dingtalkexclusive_1_0Client(config)

    @staticmethod
    def main(
        args: List[str],
    ) -> None:
        client = Sample.create_client()
        search_org_inner_group_info_headers = dingtalkexclusive__1__0_models.SearchOrgInnerGroupInfoHeaders()
        search_org_inner_group_info_headers.x_acs_dingtalk_access_token = '<your access token>'
        search_org_inner_group_info_request = dingtalkexclusive__1__0_models.SearchOrgInnerGroupInfoRequest(
            group_members_count_end=100,
            sync_to_dingpan=1,
            group_owner='user123',
            create_time_end=1618546742,
            page_size=10,
            create_time_start=1618546755,
            uuid='1111',
            group_members_count_start=1,
            last_active_time_end=1618546999,
            operator_user_id='user234',
            group_name='群1',
            page_start=1,
            last_active_time_start=1618546999
        )
        try:
            client.search_org_inner_group_info_with_options(search_org_inner_group_info_request, search_org_inner_group_info_headers, util_models.RuntimeOptions())
        except Exception as err:
            if not UtilClient.empty(err.code) and not UtilClient.empty(err.message):
                # err 中含有 code 和 message 属性，可帮助开发定位问题
                pass

    @staticmethod
    async def main_async(
        args: List[str],
    ) -> None:
        client = Sample.create_client()
        search_org_inner_group_info_headers = dingtalkexclusive__1__0_models.SearchOrgInnerGroupInfoHeaders()
        search_org_inner_group_info_headers.x_acs_dingtalk_access_token = '<your access token>'
        search_org_inner_group_info_request = dingtalkexclusive__1__0_models.SearchOrgInnerGroupInfoRequest(
            group_members_count_end=100,
            sync_to_dingpan=1,
            group_owner='user123',
            create_time_end=1618546742,
            page_size=10,
            create_time_start=1618546755,
            uuid='1111',
            group_members_count_start=1,
            last_active_time_end=1618546999,
            operator_user_id='user234',
            group_name='群1',
            page_start=1,
            last_active_time_start=1618546999
        )
        try:
            await client.search_org_inner_group_info_with_options_async(search_org_inner_group_info_request, search_org_inner_group_info_headers, util_models.RuntimeOptions())
        except Exception as err:
            if not UtilClient.empty(err.code) and not UtilClient.empty(err.message):
                # err 中含有 code 和 message 属性，可帮助开发定位问题
                pass


if __name__ == '__main__':
    Sample.main(sys.argv[1:])
"""
返回示例
HTTP/1.1 200 OK
Content-Type:application/json

{
  "totalCount" : 20,
  "itemCount" : 10,
  "items" : [ {
    "openConversationId" : "cidmfWxxxx",
    "groupOwner" : "小明",
    "groupName" : "测试群",
    "groupAdminsCount" : 2,
    "groupMembersCount" : 10,
    "groupCreateTime" : 123000000,
    "groupLastActiveTime" : 125000000,
    "groupLastActiveTimeShow" : "6个月前",
    "syncToDingpan" : 0,
    "usedQuota" : 12000,
    "groupOwnerUserId" : "02500",
    "status" : 1,
    "templateId" : "xxx",
    "templateName" : "测试模板"
  } ]
}
"""