prices <- read.csv("C:/Time series research paper/Data/log_returns.csv")

library(zoo)

# 21-day rolling means
prices$roll_mean_aapl <- rollapply(
  prices$aapl_ret,
  width = 21,
  FUN = mean,
  fill = NA,
  align = "right"
)

prices$roll_mean_msft <- rollapply(
  prices$msft_ret,
  width = 21,
  FUN = mean,
  fill = NA,
  align = "right"
)

prices$roll_mean_spy <- rollapply(
  prices$spy_ret,
  width = 21,
  FUN = mean,
  fill = NA,
  align = "right"
)

#Rolling variance

prices$roll_var_aapl <- rollapply(
  prices$aapl_ret,
  width = 21,
  FUN = var,
  fill = NA,
  align = "right"
)

prices$roll_var_msft <- rollapply(
  prices$msft_ret,
  width = 21,
  FUN = var,
  fill = NA,
  align = "right"
)

prices$roll_var_spy <- rollapply(
  prices$spy_ret,
  width = 21,
  FUN = var,
  fill = NA,
  align = "right"
)

#Rolling correlation
prices$corr_aapl_msft <- rollapply(
  prices[, c("aapl_ret", "msft_ret")],
  width = 21,
  FUN = function(x) cor(x[,1], x[,2]),
  by.column = FALSE,
  fill = NA,
  align = "right"
)

prices$corr_aapl_spy <- rollapply(
  prices[, c("aapl_ret", "spy_ret")],
  width = 21,
  FUN = function(x) cor(x[,1], x[,2]),
  by.column = FALSE,
  fill = NA,
  align = "right"
)

prices$corr_msft_spy <- rollapply(
  prices[, c("msft_ret", "spy_ret")],
  width = 21,
  FUN = function(x) cor(x[,1], x[,2]),
  by.column = FALSE,
  fill = NA,
  align = "right"
)

write.csv(
  prices,
  "C:/Time series research paper/data/features.csv",
  row.names = FALSE
)
