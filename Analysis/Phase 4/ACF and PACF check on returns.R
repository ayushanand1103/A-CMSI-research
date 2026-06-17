prices <- read.csv(
  "C:/Time series research paper/Data/features.csv"
)
prices$Date <- as.Date(
  prices$Date,
  format = "%d-%m-%Y"
)

par(mfrow = c(2,1))
##AAPL returns ACF and PACF
acf(
  prices$aapl_ret,
  lag.max=50,
  main = 'AAPL returns ACF'
)
pacf(
  prices$aapl_ret,
  lag.max=50,
  main = "AAPL returns PACF"
)

##MSFT returns ACF and PACF
acf(
  prices$msft_ret,
  lag.max = 50,
  main= "MSFT returns ACF"
)
pacf(
  prices$msft_ret,
  lag.max = 50,
  main = "MSFT returns PACF"
)

##SPY returns ACF and PACF
acf(
  prices$spy_ret,
  lag.max = 50,
  main = "SPY returns ACF"
)
pacf(
  prices$spy_ret,
  lag.max = 50,
  main = "SPY returns PACF"
)

