# Install if needed
install.packages(c("quantmod", "PerformanceAnalytics", "TTR", "zoo", "moments"))

library(quantmod)
library(PerformanceAnalytics)
library(TTR)
library(zoo)
library(moments)

#---------------------------------------
# Download data
#---------------------------------------

getSymbols(c("AAPL", "MSFT", "SPY", "^VIX"),
           from = "2015-01-01",
           to   = "2025-12-31",
           src  = "yahoo")

#---------------------------------------
# Adjusted Closing Prices
#---------------------------------------

prices <- na.omit(merge(
  Ad(AAPL),
  Ad(MSFT),
  Ad(SPY),
  Cl(VIX)
))

colnames(prices) <- c(
  "AAPL",
  "MSFT",
  "SPY",
  "VIX"
)

head(prices)
returns <- na.omit(Return.calculate(prices[,1:3], method="log"))

colnames(returns) <- c(
  "AAPL_Return",
  "MSFT_Return",
  "SPY_Return"
)

HMM_dataset <- data.frame(
  Date = index(returns),
  
  AAPL_Return = coredata(returns$AAPL_Return),
  MSFT_Return = coredata(returns$MSFT_Return),
  SPY_Return  = coredata(returns$SPY_Return),
  
  AAPL = coredata(prices[index(returns), "AAPL"]),
  MSFT = coredata(prices[index(returns), "MSFT"]),
  SPY  = coredata(prices[index(returns), "SPY"]),
  VIX  = coredata(prices[index(returns), "VIX"])
)

head(HMM_dataset)
HMM_dataset$RollingVol21 <- zoo::rollapply(
  HMM_dataset$SPY_Return,
  width = 21,
  FUN = sd,
  fill = NA,
  align = "right"
)
HMM_dataset$RollingSkew21 <- zoo::rollapply(
  HMM_dataset$SPY_Return,
  width = 21,
  FUN = moments::skewness,
  fill = NA,
  align = "right"
)
running_max <- cummax(HMM_dataset$SPY)

HMM_dataset$Drawdown <-
  (HMM_dataset$SPY - running_max) /
  running_max
HMM_dataset$VolOfVol <- zoo::rollapply(
  HMM_dataset$RollingVol21,
  width = 21,
  FUN = sd,
  fill = NA,
  align = "right"
)
corr_aapl_msft <- zoo::rollapply(
  cbind(HMM_dataset$AAPL_Return,
        HMM_dataset$MSFT_Return),
  21,
  function(x) cor(x[,1], x[,2]),
  by.column = FALSE,
  fill = NA,
  align = "right"
)

corr_aapl_spy <- zoo::rollapply(
  cbind(HMM_dataset$AAPL_Return,
        HMM_dataset$SPY_Return),
  21,
  function(x) cor(x[,1], x[,2]),
  by.column = FALSE,
  fill = NA,
  align = "right"
)

corr_msft_spy <- zoo::rollapply(
  cbind(HMM_dataset$MSFT_Return,
        HMM_dataset$SPY_Return),
  21,
  function(x) cor(x[,1], x[,2]),
  by.column = FALSE,
  fill = NA,
  align = "right"
)

HMM_dataset$C_t <-
  rowMeans(
    cbind(
      corr_aapl_msft,
      corr_aapl_spy,
      corr_msft_spy
    ),
    na.rm = TRUE
  )
V_component <- read.csv(
  "C:/A-CMSI research/Data/Main components for A CMSI/V_component.csv"
)

V_component$Date <- as.Date(V_component$Date)

HMM_dataset$Date <- as.Date(HMM_dataset$Date)

HMM_dataset <- merge(
  HMM_dataset,
  V_component,
  by = "Date"
)
HMM_features <- HMM_dataset[, c(
  "Date",
  "SPY_Return",
  "SPY_V",
  "RollingVol21",
  "RollingSkew21",
  "Drawdown",
  "VolOfVol",
  "VIX",
  "C_t"
)]

HMM_features <- na.omit(HMM_features)
write.csv(
  HMM_features,
  "C:/A-CMSI research/Data/HMM data/HMM_Input_Features.csv",
  row.names = FALSE
)
