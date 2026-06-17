library(rugarch)

# Load ARIMA residuals
residuals_data <- read.csv(
  "C:/Time series research paper/Data/arima_residuals.csv"
)

# Convert Date column
residuals_data$Date <- as.Date(residuals_data$Date)


msft_spec <- ugarchspec(
  variance.model = list(
    model = "sGARCH",
    garchOrder = c(1,1)
  ),
  mean.model = list(
    armaOrder = c(0,0),
    include.mean = FALSE
  ),
  distribution.model = "std"
)

msft_garch <- ugarchfit(
  spec = msft_spec,
  data = residuals_data$MSFT_RESID
)

show(msft_garch)
coef(msft_garch)
infocriteria(msft_garch)

msft_volatility <- sigma(msft_garch)

plot(
  residuals_data$Date,
  msft_volatility,
  type = "l",
  main = "MSFT Conditional Volatility (GARCH(1,1))",
  xlab = "Date",
  ylab = "Sigma"
)

