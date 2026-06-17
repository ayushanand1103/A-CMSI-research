library(zoo)
prices <- read.csv("C:/Time series research paper/Data/features.csv")

prices$Date <- as.Date(
  prices$Date,
  format = "%d-%m-%Y"
)


library(zoo)

prices$corr_aapl_msft_63 <- rollapply(
  prices[, c("aapl_ret", "msft_ret")],
  width = 63,
  FUN = function(x) cor(x[,1], x[,2]),
  by.column = FALSE,
  fill = NA,
  align = "right"
)

prices$corr_aapl_spy_63 <- rollapply(
  prices[, c("aapl_ret", "spy_ret")],
  width = 63,
  FUN = function(x) cor(x[,1], x[,2]),
  by.column = FALSE,
  fill = NA,
  align = "right"
)

prices$corr_msft_spy_63 <- rollapply(
  prices[, c("msft_ret", "spy_ret")],
  width = 63,
  FUN = function(x) cor(x[,1], x[,2]),
  by.column = FALSE,
  fill = NA,
  align = "right"
)

##Plots
par(mfrow = c(3,1))

plot(prices$Date,
     prices$corr_aapl_msft_63,
     type = "l",
     main = "63-Day Rolling Correlation: AAPL-MSFT",
     ylab = "Correlation",
     xlab = "Date")

abline(h = 1, lty = 2)

plot(prices$Date,
     prices$corr_aapl_spy_63,
     type = "l",
     main = "63-Day Rolling Correlation: AAPL-SPY",
     ylab = "Correlation",
     xlab = "Date")

abline(h = 1, lty = 2)

plot(prices$Date,
     prices$corr_msft_spy_63,
     type = "l",
     main = "63-Day Rolling Correlation: MSFT-SPY",
     ylab = "Correlation",
     xlab = "Date")

abline(h = 1, lty = 2)
