import pytest
from typing import Callable, Coroutine
from selenium.webdriver.chrome.webdriver import WebDriver
from adspower.async_api import Group, Category, HTTPClient
from adspower.async_api.selenium import Profile as ProfileSelenium
from adspower.async_api.playwright import Profile as ProfilePlaywright

HTTPClient.set_delay(1.1)
HTTPClient.set_timeout(30)
ProfileType = ProfileSelenium | ProfilePlaywright


class TestGroup:
    @pytest.mark.asyncio
    async def test_create(self, name, remark):
        group = await Group.create(name=name, remark=remark)
        group_to_check = (await Group.query(name=name))[0]
        assert group == group_to_check

    @pytest.mark.asyncio
    async def test_update(self, name, remark):
        group = await Group.create(name=name, remark=remark)
        await group.update(name=f'new{name}', remark='new_remark')
        group_to_check = (await Group.query(name=f'new{name}'))[0]
        assert group == group_to_check


class TestCategory:
    @pytest.mark.asyncio
    async def test_query(self, category_name):
        categories = await Category.query()
        assert len(categories) > 0


@pytest.mark.parametrize('profile_cls', [ProfilePlaywright, ProfileSelenium])
class TestProfile:
    @pytest.fixture(scope="function")
    def make_profile(
            self,
            profile_cls,
            get_name,
            get_remark
    ) -> Callable[[], Coroutine[..., ..., tuple[ProfileType, type[ProfileType]]]]:
        async def _make_profile() -> tuple[ProfileType, type[ProfileType]]:

            group = await Group.create(name=get_name(), remark=get_remark())
            profile = await profile_cls.create(name=get_name(), remark=get_remark(), group=group)
            return profile, profile_cls

        return _make_profile

    @pytest.mark.asyncio
    async def test_create(self, make_profile):
        profile, profile_cls = await make_profile()
        
        profile_to_check = (await profile_cls.query(id_=profile.id))[0]
        assert profile == profile_to_check

    @pytest.mark.asyncio
    async def test_update(self, make_profile, name, remark):
        profile, profile_cls = await make_profile()

        await profile.update(name=f'new{name}')
        profile_to_check = (await profile_cls.query(id_=profile.id))[0]
        assert profile == profile_to_check

    @pytest.mark.asyncio
    async def test_delete(self, make_profile):
        profile, profile_cls = await make_profile()
        await profile.delete()

        try: 
            query = (await profile_cls.query(id_=profile.id))[0]
            assert not query
        except IndexError:
            pass

    @pytest.mark.asyncio
    async def test_move(self, make_profile, name, remark):
        profile, profile_cls = await make_profile()

        name = profile.group.name
        group = await Group.create(name=f'new{name}', remark=remark)

        group_id_before = profile.group.id

        await profile.move(group=group)
        assert group_id_before != profile.group.id

    @pytest.mark.asyncio
    async def test_get_browser(self, make_profile):
        profile, profile_cls = await make_profile()

        async with profile as browser:
            if isinstance(browser, WebDriver):
                browser.get('https://google.com')
            else:
                page = browser.pages[0]
                await page.goto('https://google.com')
