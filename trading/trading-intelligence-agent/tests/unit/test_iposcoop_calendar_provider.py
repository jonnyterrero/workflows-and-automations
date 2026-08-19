from __future__ import annotations

from packages.data_providers.live.iposcoop_calendar import IPOScoopCalendarProvider


def test_parse_ipo_calendar_table() -> None:
    provider = IPOScoopCalendarProvider()
    html = """
    <html>
      <body>
        <table class="standard-table ipolist">
          <tr>
            <th>Company</th><th>Symbol proposed</th><th>Lead Managers</th><th>Shares (Millions)</th>
            <th>Price Low</th><th>Price High</th><th>Est. $ Volume</th><th>Expected to Trade</th>
            <th>SCOOP Rating</th><th>Rating Change</th>
          </tr>
          <tr>
            <td><a href="/ipo/example-holdings/">Example Holdings</a></td>
            <td>EXM</td>
            <td>Example Bank</td>
            <td>5.0</td>
            <td>12.00</td>
            <td>14.00</td>
            <td>$ 65.0 mil</td>
            <td>6/20/2026 Friday</td>
            <td>S/O</td>
            <td>Up</td>
          </tr>
        </table>
      </body>
    </html>
    """

    rows = provider._parse_calendar(html)

    assert len(rows) == 1
    assert rows[0]["ipo_name"] == "Example Holdings"
    assert rows[0]["ipo_symbol"] == "EXM"
    assert rows[0]["event_date"] == "2026-06-20"
    assert rows[0]["url"] == "https://www.iposcoop.com/ipo/example-holdings/"


async def test_fetch_articles_filters_by_symbol(monkeypatch) -> None:
    provider = IPOScoopCalendarProvider()
    html = """
    <html>
      <body>
        <table class="standard-table ipolist">
          <tr>
            <th>Company</th><th>Symbol proposed</th><th>Lead Managers</th><th>Shares (Millions)</th>
            <th>Price Low</th><th>Price High</th><th>Est. $ Volume</th><th>Expected to Trade</th>
            <th>SCOOP Rating</th><th>Rating Change</th>
          </tr>
          <tr>
            <td>Alpha Labs</td>
            <td>ALPH</td>
            <td>Example Bank</td>
            <td>2.0</td>
            <td>8.00</td>
            <td>10.00</td>
            <td>$ 18.0 mil</td>
            <td>6/19/2026 Thursday</td>
            <td>S/O</td>
            <td>S/O</td>
          </tr>
          <tr>
            <td>Beta Systems</td>
            <td>BETA</td>
            <td>Example Bank</td>
            <td>3.0</td>
            <td>11.00</td>
            <td>13.00</td>
            <td>$ 36.0 mil</td>
            <td>6/21/2026 Sunday</td>
            <td>S/O</td>
            <td>S/O</td>
          </tr>
        </table>
      </body>
    </html>
    """

    async def _fake_fetch_html() -> str:
        return html

    monkeypatch.setattr(provider, "_fetch_html", _fake_fetch_html)

    articles = await provider.fetch_articles(query="ALPH", limit=10)

    assert len(articles) == 1
    assert articles[0]["ipo_symbol"] == "ALPH"
