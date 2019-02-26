# Stock-analysis

How to run?
Import all the libraries and required dependencies for the project. (such as Flask, Beautifulsoup)
Run the file app.py on your machine.
Then you can see the link where the web servie is being hosted. (localhost)
Go to the link, enter a stock ticker and get started!

Summary:
Web app built in Flask, and data scraping is done with beautifulsoup4. Azure Text analytics Api is used to provide get sentiment score.

What it does?
Given a stock ticker (i.e. EOG) it searches NASDAQ.com and seekingalpha.com for related articles and scrapes off all the data. You can do sentiment analysis, earning call transcript analysis and even get the latest stock information.

Sentiment analysis:
Most frequent words analyzed from the news articles are presented. Also links to the articles are given.


