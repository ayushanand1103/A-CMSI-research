library(tseries)
prices <- read.csv("C:/Time series research paper/Data/features.csv")

prices$Date <- as.Date(
  prices$Date,
  format = "%d-%m-%Y"
)

# Creating first order difference
prices$aapl_diff <- c(NA, diff(prices$AAPL))
prices$msft_diff <- c(NA, diff(prices$MSFT))
prices$spy_diff  <- c(NA, diff(prices$SPY))
# For raw prices ADF
adf_aapl_price <- adf.test(prices$AAPL)

adf_msft_price <- adf.test(prices$MSFT)

adf_spy_price <- adf.test(prices$SPY)

# For Log returns ADF
adf_aapl_ret <- adf.test(prices$aapl_ret)

adf_msft_ret <- adf.test(prices$msft_ret)

adf_spy_ret <- adf.test(prices$spy_ret)

# For first order difference ADF
adf_aapl_diff <- adf.test(na.omit(prices$aapl_diff))

adf_msft_diff <- adf.test(na.omit(prices$msft_diff))

adf_spy_diff <- adf.test(na.omit(prices$spy_diff))

# For prices KPSS
kpss_aapl_price <- kpss.test(prices$AAPL)

kpss_msft_price <- kpss.test(prices$MSFT)

kpss_spy_price <- kpss.test(prices$SPY)

# For log returns KPSS
kpss_aapl_ret <- kpss.test(prices$aapl_ret)

kpss_msft_ret <- kpss.test(prices$msft_ret)

kpss_spy_ret <- kpss.test(prices$spy_ret)

#For First order difference
kpss_aapl_diff <- kpss.test(na.omit(prices$aapl_diff))

kpss_msft_diff <- kpss.test(na.omit(prices$msft_diff))

kpss_spy_diff <- kpss.test(na.omit(prices$spy_diff))

results <- data.frame(
  Series = c(
    "AAPL Price","MSFT Price","SPY Price",
    "AAPL Return","MSFT Return","SPY Return",
    "AAPL Diff","MSFT Diff","SPY Diff"
  ),
  
  ADF_p = c(
    adf_aapl_price$p.value,
    adf_msft_price$p.value,
    adf_spy_price$p.value,
    adf_aapl_ret$p.value,
    adf_msft_ret$p.value,
    adf_spy_ret$p.value,
    adf_aapl_diff$p.value,
    adf_msft_diff$p.value,
    adf_spy_diff$p.value
  ),
  
  KPSS_p = c(
    kpss_aapl_price$p.value,
    kpss_msft_price$p.value,
    kpss_spy_price$p.value,
    kpss_aapl_ret$p.value,
    kpss_msft_ret$p.value,
    kpss_spy_ret$p.value,
    kpss_aapl_diff$p.value,
    kpss_msft_diff$p.value,
    kpss_spy_diff$p.value
  )
)

results
