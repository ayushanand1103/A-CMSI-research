aapl <- read.csv(
  "C:/A-CMSI research/Data/GARCH vol/AAPL_GARCH_Volatility.csv"
)

msft <- read.csv(
  "C:/A-CMSI research/Data/GARCH vol/MSFT_GARCH_Volatility.csv"
)

spy <- read.csv(
  "C:/A-CMSI research/Data/GARCH vol/SPY_EGARCH_Volatility.csv"
)

vol_data <- data.frame(
  Date = aapl$Date,
  AAPL_vol = aapl$AAPL_vol,
  MSFT_vol = msft$MSFT_vol,
  SPY_vol = spy$SPY_vol
)

head(vol_data)
dim(vol_data)
summary(vol_data)
colSums(is.na(vol_data))
write.csv(
  vol_data,
  "C:/A-CMSI research/Data/GARCH vol/Merged_Volatility.csv",
  row.names = FALSE
)
