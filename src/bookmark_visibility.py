"""Pure predicate deciding whether the bookmark rail has a useful item."""


def has_bookmark_toolbar_content(bookmarks) -> bool:
    return any(
        isinstance(item, dict)
        and item.get('folder', 'toolbar') == 'toolbar'
        and str(item.get('url', '')).startswith(('https://', 'http://'))
        for item in bookmarks
    )
