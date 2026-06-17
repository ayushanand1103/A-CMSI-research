library(forecast)
library(FinTS)
library(lmtest)
prices <- read.csv(
  "C:/Time series research paper/Data/features.csv"
)
prices$Date <- as.Date(
  prices$Date,
  format = "%d-%m-%Y"
)

##ARIMA
aapl_arima <- auto.arima(
  prices$aapl_ret,
  seasonal = FALSE,
  stepwise = FALSE,
  approximation = FALSE
)
summary(aapl_arima)

msft_arima <- auto.arima(
  prices$msft_ret,
  seasonal = FALSE,
  stepwise = FALSE,
  approximation = FALSE
)
summary(msft_arima)

spy_arima <- auto.arima(
  prices$spy_ret,
  seasonal = FALSE,
  stepwise = FALSE,
  approximation = FALSE
)

summary(spy_arima)

##Getting residuals 
aapl_residuals <- residuals(aapl_arima)
msft_residuals <- residuals(msft_arima)
spy_residuals <- residuals(spy_arima)

## ARCH test 
ArchTest(
  aapl_residuals,
  lags = 12
)
ArchTest(
  msft_residuals,
  lags = 12
)
ArchTest(
  spy_residuals,
  lags = 12
)

##Linjung box test 
Box.test(
  aapl_residuals,
  lag = 20,
  type = "Ljung-Box"
)

Box.test(
  msft_residuals,
  lag = 20,
  type = "Ljung-Box"
)

Box.test(
  spy_residuals,
  lag = 20,
  type = "Ljung-Box"
)

par(mfrow = c(3,1))
acf(aapl_residuals)
acf(msft_residuals)
acf(spy_residuals)

checkresiduals(aapl_arima)
checkresiduals(msft_arima)
checkresiduals(spy_arima)

##Durbin watson test
##DW ≈ 2 → no autocorrelation
##DW < 2 → positive autocorrelation
##DW > 2 → negative autocorrelation
dwtest(aapl_residuals ~ 1)
dwtest(msft_residuals ~ 1)
dwtest(spy_residuals ~ 1)


residuals_df <- data.frame(
  Date = prices$Date,
  AAPL_RESID = as.numeric(aapl_residuals),
  MSFT_RESID = as.numeric(msft_residuals),
  SPY_RESID  = as.numeric(spy_residuals)
)

## Save for GARCH phase

write.csv(
  residuals_df,
  "C:/Time series research paper/Data/arima_residuals.csv",
  row.names = FALSE
)


