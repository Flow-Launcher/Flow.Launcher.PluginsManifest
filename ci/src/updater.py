# -*-coding: utf-8 -*-
import asyncio
import aiohttp
from zipfile import ZipFile
import re
from io import BytesIO
from typing import List
from os import getenv
from sys import argv
import traceback

from tqdm.asyncio import tqdm

from _utils import *
from discord import rejection_hook, update_hook

async def batch_github_plugin_info(
    info: P, tags: ETagsType, github_token=None, webhook_url: str | None = None
) -> P:
    try:
        headers = {"authorization": f"token {github_token}"}
        if "github.com" not in info[url_download]:
            return info

        url_parts: List[str] = info[url_sourcecode].split("/")
        if len(url_parts) < 5:
            return info

        repo = "/".join(url_parts[3:5])
        # ETag of the newest release we have already seen, from etags.json.
        # It can belong to a rejected release, so it is not the version currently in the manifest.
        tag: str = tags.get(info[id_name], info.get(etag, ""))

        # Send the stored ETag whenever there is one, so a rejected release is not fetched
        # again. Gating this on a release date would miss manifests that do not have one yet.
        if tag:
            headers["If-None-Match"] = tag

        async with aiohttp.ClientSession() as session:
            res = await session.get(
                url_release.format(repo=repo),
                headers=headers,
            )
            if res.status in (403, 304):
                return info

            latest_rel = await res.json()

            assets = latest_rel.get("assets")

            if assets:
                browser_download_url = None

                if len(assets) > 1:
                    match = github_download_url_regex.match(info[url_download])
                    if not match:
                        raise ValueError(
                            f"Download URL did not match regex: {info[url_download]!r}"
                        )
                    filename = f"{match['filename']}.zip"
                    for asset in assets:
                        if asset["browser_download_url"].endswith(filename):
                            browser_download_url = asset["browser_download_url"]

                new_download_url = (
                    browser_download_url or assets[0]["browser_download_url"]
                )

                # Reject a tag we cannot turn into a valid download URL rather than writing it.
                # A bad URL fails manifest validation for every plugin, not only this one.
                if github_download_url_regex.fullmatch(new_download_url) is None:
                    issue_reported = await report_invalid_release(
                        info, repo, latest_rel, new_download_url, webhook_url
                    )
                    if issue_reported:
                        # Cache only after an issue exists, so notification failures are retried.
                        tags[info[id_name]] = res.headers.get(etag, "")
                    return info

                info[url_download] = new_download_url

                latest_ver = clean(latest_rel["tag_name"], "v")
                if version_tuple(info[version]) != version_tuple(latest_ver):
                    tqdm.write(f"Update detected: {info[plugin_name]} {latest_ver}")

                    metadata = await get_plugin_dot_json(
                        info[url_download], session=session
                    )
                    for key in (
                        description,
                        author,
                        language_name,
                        website,
                    ):
                        info[key] = metadata[key]

                    if metadata.get(minimum_app_version):
                        info[minimum_app_version] = metadata[minimum_app_version]

                    if webhook_url:
                        await send_notification(
                            info,
                            latest_ver,
                            latest_rel,
                            webhook_url,
                        )
                info[version] = latest_ver

            # Only an accepted release reaches here, so a rejected one keeps its previous date
            if info.get(release_date, "") != latest_rel.get("published_at"):
                info[release_date] = latest_rel.get("published_at")

            tags[info[id_name]] = res.headers.get(etag, "")

            return info
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Error when processing plugin {info[plugin_name]}:\n{e} {tb}")
        return info


async def get_plugin_dot_json(download_url: str, *, session: aiohttp.ClientSession):
    async with session.get(download_url) as res:
        data = await res.read()

    with ZipFile(BytesIO(data)) as zip:
        for fileinfo in zip.filelist:
            if not fileinfo.filename.endswith("plugin.json"):
                continue

            with zip.open(fileinfo, "r") as file:
                return json.loads(file.read())

    raise ValueError(f"plugin.json file not found. Download Url: {download_url}")


async def batch_plugin_infos(
    plugin_infos: Ps, tags: ETagsType, github_token, webhook_url: str | None = None
) -> Ps:
    return await tqdm.gather(
        *[
            batch_github_plugin_info(info, tags, github_token, webhook_url)
            for info in tqdm(plugin_infos)
        ]
    )


def remove_unused_etags(plugin_infos: PluginsType, etags: ETagsType) -> ETagsType:
    etags_updated = {}
    plugin_ids = [info.get("ID") for info in plugin_infos]

    for id, tag in etags.items():
        if id not in plugin_ids:
            print(
                f"Plugin with ID {id} has been removed. The associated ETag will be also removed now."
            )
            continue

        etags_updated[id] = tag

    return etags_updated


async def send_notification(
    info: PluginType, latest_ver: str, release, webhook_url: str | None = None
) -> None:
    if not webhook_url:
        return

    try:
        await update_hook(webhook_url, info, latest_ver, release)
    except Exception as e:
        tqdm.write(str(e))


# Name of the environment variable holding a token that can open issues on plugin repositories.
# The updater workflow's GITHUB_TOKEN only covers this repository, so it cannot notify authors.
# TODO: create the secret and grant it issue-write access to plugin repositories.
plugin_issue_token_env = "PLUGIN_ISSUE_TOKEN"


async def report_invalid_release(
    info: PluginType,
    repo: str,
    release: dict,
    download_url: str,
    webhook_url: str | None = None,
) -> bool:
    """Tell a plugin author their release tag cannot be accepted.

    Opens an issue on the plugin's own repository, posts the rejection to Discord when
    configured, and logs the rejection. When an issue exists, its link is included in
    the Discord message. Returns True only when the author issue exists, allowing the
    caller to cache the ETag only after author notification is recorded.

    Args:
        info: Plugin dictionary whose update was rejected.
        repo: ``owner/name`` of the plugin repository.
        release: GitHub release payload that was rejected.
        download_url: Release asset URL that failed validation.
        webhook_url: Discord webhook URL, when one is configured.
    """
    tag = release.get("tag_name", "")
    tqdm.write(
        f"Rejected update for {info[plugin_name]} ({tag}): {download_url} is not a valid download URL"
    )

    token = getenv(plugin_issue_token_env)
    if not token:
        if webhook_url:
            skipped_notifications = "issue and Discord notifications"
        else:
            skipped_notifications = "issue notification"
        tqdm.write(
            f"Skipping {skipped_notifications} for {repo}: "
            f"{plugin_issue_token_env} is not set"
        )
        return False

    issue_url = None
    existing_issue_found = False
    title = f"Flow Launcher update to {tag} rejected for {info[plugin_name]}"
    body = (
        f"The Flow Launcher update to `{tag}` was rejected because the release download URL "
        f"cannot be used.\n\n"
        f"Download URL: {download_url}\n"
        f"Release: {release.get('html_url', '')}\n\n"
        f"Release download URLs must look like "
        f"`https://github.com/<owner>/<repo>/releases/download/<version>/<file>.zip`, "
        f"where `<version>` contains only letters, digits and dots, for example `v1.2.3`.\n\n"
        f"Publish the release under a version tag such as `v1.2.3` and the update will be picked up automatically."
    )
    try:
        issue_url, existing_issue_found = await open_plugin_repo_issue(
            repo, title, body, token
        )
    except Exception as e:
        tqdm.write(f"Failed to notify {repo}: {e}")

    if webhook_url and not existing_issue_found:
        try:
            await rejection_hook(webhook_url, info, release, download_url, issue_url)
        except Exception as e:
            tqdm.write(f"Failed to post rejection to Discord: {e}")

    return issue_url is not None


async def open_plugin_repo_issue(
    repo: str, title: str, body: str, token: str
) -> tuple[str | None, bool]:
    """Open an issue on a plugin repository unless a matching issue is found.

    Args:
        repo: ``owner/name`` of the plugin repository.
        title: Issue title, also used to find an existing matching issue.
        body: Issue body.
        token: GitHub token with issue-write access to the plugin repository.

    Returns:
        issue_url: URL of the matching existing issue or newly created issue, or
            None if lookup or creation failed.
        existing_issue_found: True if a matching issue appeared in the lookup
            response; False if this call created an issue or lookup or creation failed.
    """
    headers = {"authorization": f"token {token}", "accept": "application/vnd.github+json"}
    issues_url = f"https://api.github.com/repos/{repo}/issues"

    async with aiohttp.ClientSession() as session:
        async with session.get(
            issues_url, headers=headers, params={"state": "all", "per_page": 100}
        ) as res:
            if res.status >= 400:
                tqdm.write(
                    f"Failed to check issues on {repo}: HTTP {res.status} {await res.text()}"
                )
                return None, False
            existing = await res.json()
            for issue in existing:
                if "pull_request" not in issue and issue.get("title") == title:
                    tqdm.write(f"Rejection issue already exists on {repo}, skipping")
                    return issue.get("html_url"), True

        async with session.post(
            issues_url, headers=headers, json={"title": title, "body": body}
        ) as res:
            if res.status >= 400:
                tqdm.write(f"Failed to open issue on {repo}: HTTP {res.status} {await res.text()}")
                return None, False
            created = await res.json()
            issue_url = created.get("html_url", "")
            tqdm.write(f"Opened {issue_url} on {repo}")
            return issue_url or None, False


async def main():
    webhook_url = None
    if len(argv) > 1:
        webhook_url = argv[1]
    plugin_infos = plugin_reader()
    etags = etag_reader()

    plugin_infos_new = await batch_plugin_infos(
        plugin_infos, etags, getenv("GITHUB_TOKEN"), webhook_url
    )
    plugin_writer(plugin_infos_new)

    etags_new = remove_unused_etags(plugin_infos_new, etags)
    etags_writer(etags_new)


if __name__ == "__main__":
    asyncio.run(main())
