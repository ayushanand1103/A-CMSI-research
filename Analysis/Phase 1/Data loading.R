library(quantmod)

getSymbols(c("AAPL","MSFT","SPY"),
           src="yahoo",
           from="2015-01-01",
           to="2025-12-31")

merged_data <- merge(
  Ad(AAPL),
  Ad(MSFT),
  Ad(SPY)
)

colnames(merged_data) <- c("AAPL","MSFT","SPY")

write.csv(
  data.frame(Date=index(merged_data), merged_data),
  "all_prices.csv",
  row.names = FALSE
)

write.csv(data.frame(AAPL),
          "AAPL_raw.csv",
          row.names = FALSE)

write.csv(data.frame(MSFT),
          "MSFT_raw.csv",
          row.names = FALSE)

write.csv(data.frame(SPY),
          "SPY_raw.csv",
          row.names = FALSE)