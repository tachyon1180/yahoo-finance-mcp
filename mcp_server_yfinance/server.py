from mcp.server.fastmcp import FastMCP
import yfinance as yf
import json
from loguru import logger

# Initialize FastMCP server
mcp = FastMCP("yfinance")


@mcp.tool(
    name="get_historical_stock_prices",
    description="Get historical stock prices for a given ticker symbol from yahoo finance. Include the following information: Date, Open, High, Low, Close, Volume, Adj Close.",
)
async def get_historical_stock_prices(ticker: str, period: str = "1mo", interval: str = "1d"):
    """Get historical stock prices for a given ticker symbol
    
    Args:
        ticker: str
            The ticker symbol of the stock to get historical prices for, e.g. "AAPL"
        period : str
            Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
            Either Use period parameter or use start and end
            Default is "1mo"
        interval : str
            Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
            Intraday data cannot extend last 60 days
            Default is "1d"
    """
    company = yf.Ticker(ticker)
    try:
        if company.isin is None:
            logger.warning(f"Company ticker {ticker} not found.")
            return f"Company ticker {ticker} not found."
    except Exception as e:
        logger.error(f"Error getting historical stock prices for {ticker}: {e}")
        return f"Error getting historical stock prices for {ticker}: {e}"

    # If the company is found, get the historical data
    hist_data = company.history(period=period, interval=interval)
    hist_data = hist_data.reset_index(names='Date')
    hist_data = hist_data.to_json(orient="records", date_format="iso")
    return hist_data


@mcp.tool(
    name="get_stock_info",
    description="""Get stock information for a given ticker symbol from yahoo finance. Include the following information:
Stock Price & Trading Info, Company Information, Financial Metrics, Earnings & Revenue, Margins & Returns, Dividends, Balance Sheet, Ownership, Analyst Coverage, Risk Metrics, Other.""",
)
async def get_stock_info(ticker: str):
    """Get stock information for a given ticker symbol"""
    company = yf.Ticker(ticker)
    try:
        if company.isin is None:
            logger.warning(f"Company ticker {ticker} not found.")
            return f"Company ticker {ticker} not found."
    except Exception as e:
        logger.error(f"Error getting stock information for {ticker}: {e}")
        return f"Error getting stock information for {ticker}: {e}"
    info = company.info
    return json.dumps(info)


@mcp.tool(
    name="get_yahoo_finance_news",
    description="Get news for a given ticker symbol from yahoo finance.",
)
async def get_yahoo_finance_news(ticker: str):
    """Get news for a given ticker symbol
    
    Args:
        ticker: str
            The ticker symbol of the stock to get news for, e.g. "AAPL"
    """
    company = yf.Ticker(ticker)
    try:
        if company.isin is None:
            logger.warning(f"Company ticker {ticker} not found.")
            return f"Company ticker {ticker} not found."
    except Exception as e:
        logger.error(f"Error getting news for {ticker}: {e}")
        return f"Error getting news for {ticker}: {e}"

    # If the company is found, get the news
    try:
        news = company.news
    except Exception as e:
        logger.error(f"Error getting news for {ticker}: {e}")
        return f"Error getting news for {ticker}: {e}"

    news_list = []
    for news in company.news:
        if news.get("content", {}).get("contentType", "") == "STORY":
            title = news.get("content", {}).get("title", "")
            summary = news.get("content", {}).get("summary", "")
            description = news.get("content", {}).get("description", "")
            url = news.get("content", {}).get("canonicalUrl", {}).get("url", "")
            news_list.append(f"Title: {title}\nSummary: {summary}\nDescription: {description}\nURL: {url}")
    if not news_list:
        logger.warning(f"No news found for company that searched with {ticker} ticker.")
        return f"No news found for company that searched with {ticker} ticker."
    return "\n\n".join(news_list)


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')