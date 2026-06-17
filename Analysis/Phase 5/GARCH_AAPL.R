library(rugarch)

# Load ARIMA residuals
residuals_data <- read.csv(
  "C:/Time series research paper/Data/arima_residuals.csv"
)

# Convert Date column
residuals_data$Date <- as.Date(residuals_data$Date)

# Verify
head(residuals_data)
str(residuals_data)

# GARCH(1,1) Specification
aapl_spec <- ugarchspec(
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

# Fit model
aapl_garch <- ugarchfit(
  spec = aapl_spec,
  data = residuals_data$AAPL_RESID
)

# Results
show(aapl_garch)

# Parameters
coef(aapl_garch)

# AIC/BIC
infocriteria(aapl_garch)


aapl_volatility <- sigma(aapl_garch)

plot(
  residuals_data$Date,
  aapl_volatility,
  type = "l",
  main = "AAPL Conditional Volatility",
  xlab = "Date",
  ylab = "Sigma"
)

