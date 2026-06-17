prices <- read.csv(
  "C:/Time series research paper/data/features.csv",
  stringsAsFactors = FALSE
)

prices$Date <- as.Date(
  prices$Date,
  format = "%d-%m-%Y"
)

head(prices$Date)
tail(prices$Date)

#Plotting actual values
par(mfrow = c(3,1))

plot(prices$Date,
     prices$AAPL,
     type = "l",
     main = "AAPL Adjusted Close Price",
     xlab = "Date",
     ylab = "Price")

plot(prices$Date,
     prices$MSFT,
     type = "l",
     main = "MSFT Adjusted Close Price",
     xlab = "Date",
     ylab = "Price")

plot(prices$Date,
     prices$SPY,
     type = "l",
     main = "SPY Adjusted Close Price",
     xlab = "Date",
     ylab = "Price")

#Plotting log returns
par(mfrow = c(3,1))

plot(prices$Date,
     prices$aapl_ret,
     type = "l",
     main = "AAPL Log Returns",
     xlab = "Date",
     ylab = "Return")

plot(prices$Date,
     prices$msft_ret,
     type = "l",
     main = "MSFT Log Returns",
     xlab = "Date",
     ylab = "Return")

plot(prices$Date,
     prices$spy_ret,
     type = "l",
     main = "SPY Log Returns",
     xlab = "Date",
     ylab = "Return")

#Plotting rolling mean 21 day window
par(mfrow = c(3,1))

plot(prices$Date,
     prices$roll_mean_aapl,
     type = "l",
     main = "AAPL returns 21-Day Rolling Mean")

plot(prices$Date,
     prices$roll_mean_msft,
     type = "l",
     main = "MSFT reuturns 21-Day Rolling Mean")

plot(prices$Date,
     prices$roll_mean_spy,
     type = "l",
     main = "SPY returns 21-Day Rolling Mean")

#Plotting rolling variance 21 day window
par(mfrow = c(3,1))

plot(prices$Date,
     prices$roll_var_aapl,
     type = "l",
     main = "AAPL 21-Day Rolling Variance")

plot(prices$Date,
     prices$roll_var_msft,
     type = "l",
     main = "MSFT 21-Day Rolling Variance")

plot(prices$Date,
     prices$roll_var_spy,
     type = "l",
     main = "SPY 21-Day Rolling Variance")
