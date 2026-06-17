library(rugarch)

# Load ARIMA residuals
residuals_data <- read.csv(
  "C:/Time series research paper/Data/arima_residuals.csv"
)

# Convert Date column
residuals_data$Date <- as.Date(residuals_data$Date)

spy_gjr_spec <- ugarchspec(
  variance.model = list(
    model = "gjrGARCH",
    garchOrder = c(1,1)
  ),
  mean.model = list(
    armaOrder = c(0,0),
    include.mean = FALSE
  ),
  distribution.model = "std"
)

spy_gjr <- ugarchfit(
  spec = spy_gjr_spec,
  data = residuals_data$SPY_RESID
)

show(spy_gjr)

coef(spy_gjr)

infocriteria(spy_gjr)

# Conditional Volatility
spy_gjrgarch_vol <- sigma(spy_gjr)


plot(
  residuals_data$Date,
  spy_gjrgarch_vol,
  type = "l",
  main = "SPY Conditional Volatility (GJRGARCH(1,1))",
  xlab = "Date",
  ylab = "Sigma"
)

