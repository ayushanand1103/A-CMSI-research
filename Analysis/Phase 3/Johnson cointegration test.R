library(urca)
library(vars)

prices <- read.csv(
  "C:/Time series research paper/Data/features.csv"
)

price_data <- prices[, c("AAPL", "MSFT", "SPY")]

#All 3 series
johansen_test <- ca.jo(
  price_data,
  type = "trace",
  ecdet = "const",
  K = 2
)

summary(johansen_test)

johansen_test@ecdet

#AAPL MSFT

summary(ca.jo(
  prices[, c("AAPL","MSFT")],
  type = "trace",
  ecdet = "const",
  K = 2
))

summary(ca.jo(
  prices[, c("AAPL","SPY")],
  type = "trace",
  ecdet = "const",
  K = 2
))

summary(ca.jo(
  prices[, c("MSFT","SPY")],
  type = "trace",
  ecdet = "const",
  K = 2
))

#ECM model 
ecm_model <- cajorls(
  johansen_test,
  r = 1
)

summary(ecm_model$rlm)
