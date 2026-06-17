library(rugarch)

# Load ARIMA residuals
residuals_data <- read.csv(
  "C:/Time series research paper/Data/arima_residuals.csv"
)

# Convert Date column
residuals_data$Date <- as.Date(residuals_data$Date)

# EGARCH(1,1) Specification
spy_egarch_spec <- ugarchspec(
  variance.model = list(
    model = "eGARCH",
    garchOrder = c(1,1)
  ),
  mean.model = list(
    armaOrder = c(0,0),
    include.mean = FALSE
  ),
  distribution.model = "std"
)
# Fit EGARCH model
spy_egarch <- ugarchfit(
  spec = spy_egarch_spec,
  data = residuals_data$SPY_RESID
)

# Full Results
show(spy_egarch)

# Parameters
coef(spy_egarch)

# Information Criteria
infocriteria(spy_egarch)

# Conditional Volatility
spy_egarch_vol <- sigma(spy_egarch)

# Plot
plot(
  residuals_data$Date,
  spy_egarch_vol,
  type = "l",
  main = "SPY Conditional Volatility (EGARCH(1,1))",
  xlab = "Date",
  ylab = "Sigma"
)
spy_egarch_output <- data.frame(
  Date = residuals_data$Date,
  SPY_vol = as.numeric(spy_egarch_vol)
)

rownames(spy_egarch_output) <- NULL
