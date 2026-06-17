library(quantmod)
library(xts)
library(zoo)

prices_merged <- read.csv("C:/Time series research paper/all_prices.csv")

nrow(prices_merged)
ncol(prices_merged)

colSums(is.na(prices_merged))

min(as.Date(prices_merged$Date))
max(as.Date(prices_merged$Date))

sum(duplicated(prices_merged$Date))

prices_filled <- na.locf(prices_merged, na.rm = FALSE)
prices_filled
colSums(is.na(prices_filled))

write.csv(
  prices_filled,
  "C:/Time series research paper/prices_clean.csv",
  row.names = FALSE
)
