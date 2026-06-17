library(rugarch)

# Load ARIMA residuals
residuals_data <- read.csv(
  "C:/Time series research paper/Data/arima_residuals.csv"
)

# Convert Date column
residuals_data$Date <- as.Date(residuals_data$Date)


spy_spec <- ugarchspec(
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

spy_garch <- ugarchfit(
  spec = spy_spec,
  data = residuals_data$SPY_RESID
)

show(spy_garch)

coef(spy_garch)

infocriteria(spy_garch)

spy_volatility <- sigma(spy_garch)

plot(
  residuals_data$Date,
  spy_volatility,
  type = "l",
  main = "SPY Conditional Volatility (GARCH(1,1))",
  xlab = "Date",
  ylab = "Sigma"
)

spy_output <- data.frame(
  Date = residuals_data$Date,
  SPY_vol = as.numeric(spy_volatility)
)

rownames(spy_output) <- NULL
