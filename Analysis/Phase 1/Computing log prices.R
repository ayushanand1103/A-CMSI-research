prices <- read.csv(
  "C:/Time series research paper/Data/all_prices.csv"
)

prices$Date <- as.Date(
  prices$Date,
  format = "%d-%m-%Y"
)
head(prices)
tail(prices)

prices$Date <- as.Date(prices$Date)

prices$aapl_ret <- c(NA, diff(log(prices$AAPL)))
prices$msft_ret <- c(NA, diff(log(prices$MSFT)))
prices$spy_ret  <- c(NA, diff(log(prices$SPY)))

head(prices)
tail(prices)

prices <- na.omit(prices)
colSums(is.na(prices))

write.csv(
  prices,
  "C:/Time series research paper/data/log_returns.csv",
  row.names = FALSE
)
